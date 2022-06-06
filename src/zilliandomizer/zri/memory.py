import asyncio
import sys
from typing import Final, Literal, Optional, Tuple, Iterator

from zilliandomizer.logic_components.items import RESCUE, NORMAL
from zilliandomizer.low_resources import ram_info
from zilliandomizer.zri.events import EventFromGame, EventToGame, \
    AcquireLocationEventFromGame, ItemEventToGame, DeathEventToGame
from zilliandomizer.zri.rai import CANISTER_ROOM_COUNT, RAInterface, DOOR_BYTE_COUNT, RamData

BYTE_ORDER: Final[Literal['little', 'big']] = sys.byteorder  # type: ignore
# mypy doesn't see literal types of byteorder


def bits(n: int) -> Iterator[int]:
    """ yield each activated bit of n """
    while n:
        b = n & ((~n) + 1)
        yield b
        n ^= b


def bytes_or(a: bytes, b: bytes) -> bytes:
    assert len(a) == len(b)
    return bytes(a[i] | b[i] for i in range(len(a)))


class State:
    doors: bytes
    """ opened """

    def __init__(self, ram: Optional[RamData] = None) -> None:
        if ram:
            self.doors = ram[ram_info.door_state_d600: ram_info.door_state_d600 + DOOR_BYTE_COUNT]
        else:
            self.reset()

    def reset(self) -> None:
        self.doors = bytes(0 for _ in range(DOOR_BYTE_COUNT))

    def anything_lost(self, old: "State") -> bool:
        _, door_lost, _ = get_changed_lost(self.doors, old.doors)

        # self.diff_cache = StateDiffCache(door_change, door_lost, door_int)

        return bool(door_lost)


c11f_in_game_scenes = frozenset((
    # continue, explode, cs, ship, computer, pause, play, main computer
    3, 4, 6, 7, 8, 9, 0xb, 0xc
))


def get_changed_lost(new: bytes, old: bytes) -> Tuple[int, int, int]:
    """
    changed bits, lost bits, new bits as `int`
    """
    new_int = int.from_bytes(new, BYTE_ORDER)
    old_int = int.from_bytes(old, BYTE_ORDER)
    changed = new_int ^ old_int
    lost = changed & old_int
    return changed, lost, new_int


class Memory:
    """
    puts in from_game_queue when sees events in game

    consumes to_game_queue

    mixing this with save states can corrupt game and is not supported
    """

    rai: RAInterface
    from_game_queue: "Optional[asyncio.Queue[EventFromGame]]"
    to_game_queue: "asyncio.Queue[EventToGame]"

    looking_for_send_confirmation: int
    """ item id sent (comm id 2 bytes) """

    restore_target: Optional[State]

    known_cans: bytes
    known_in_game: bool
    known_win_state: bool

    state: State

    def __init__(self,
                 from_game_queue: "Optional[asyncio.Queue[EventFromGame]]" = None,
                 to_game_queue: "Optional[asyncio.Queue[EventToGame]]" = None) -> None:
        self.rai = RAInterface()
        self.from_game_queue = from_game_queue
        self.to_game_queue = to_game_queue or asyncio.Queue()

        self.restore_target = None

        self.state = State()
        self.reset()

    def reset(self) -> None:
        self.looking_for_send_confirmation = 0

        self.known_in_game = False
        self.known_win_state = False
        self.known_cans = bytes(0 for _ in range(CANISTER_ROOM_COUNT))

        self.state.reset()

    def in_game(self, scene: int) -> bool:
        in_game = (scene & 0x7f) in c11f_in_game_scenes
        if in_game != self.known_in_game:
            print(f"in game: {in_game}")
            self.known_in_game = in_game
        return in_game

    def process_change(self, new_cans: bytes) -> None:
        # report
        change, _, new_int = get_changed_lost(new_cans, self.known_cans)
        added = change & new_int
        rooms = added.to_bytes(CANISTER_ROOM_COUNT, BYTE_ORDER)

        # indexes into rooms
        added_rooms = [i for i, b in enumerate(rooms) if b]

        for room_i in added_rooms:
            for can in bits(rooms[room_i]):
                print(f"picked up canister {can} in room {room_i}")
                loc_id = (room_i << 8) | (can)
                if not (self.from_game_queue is None):
                    self.from_game_queue.put_nowait(
                        AcquireLocationEventFromGame(loc_id)
                    )

    async def _process_to_game_queue(self, ram: RamData, q: "asyncio.Queue[EventToGame]") -> None:
        if q.qsize():
            if ram.safe_to_write():
                event = q.get_nowait()
                if isinstance(event, ItemEventToGame):
                    comm_item_id = event.id
                    code = comm_item_id >> 8
                    item_id = comm_item_id & 0xff
                    if code == RESCUE:
                        if item_id in (0, 1):
                            # 3 Apple, 4 Champ
                            item_id += 3
                            await self.rai.write(ram_info.external_item_trigger_c2ea, [item_id])
                            self.looking_for_send_confirmation = comm_item_id
                        else:
                            print(f"WARNING: invalid item id {comm_item_id} received")
                    elif code == NORMAL:
                        if 0x05 <= item_id <= 0x0b:
                            print(f"sending item {item_id} to game")
                            await self.rai.write(ram_info.external_item_trigger_c2ea, [item_id])
                            self.looking_for_send_confirmation = comm_item_id
                        else:
                            print(f"WARNING: invalid item id {comm_item_id} received")
                    else:  # not rescue or normal
                        print(f"WARNING: invalid item id {comm_item_id} received")
                elif isinstance(event, DeathEventToGame):
                    await self.rai.write(0xc308, [0x84])
                else:
                    print(f"WARNING: unhandled EventToGame {event}")
                q.task_done()
            # else not a good time to send something to game
        # else queue empty

    async def check(self) -> None:
        ram = await self.rai.read()

        if not ram.all_present():
            return  # TODO: signal when data isn't retrieved?

        current_scene = ram[ram_info.current_scene_c11f]
        if self.in_game(current_scene):
            if self.looking_for_send_confirmation:
                if ram.check_item_trigger():
                    self.looking_for_send_confirmation = 0
                else:  # no confirmation
                    # TODO: if x time passes, put item sent (id in flag) back in queue?
                    pass
            elif self.restore_target:
                await self._restore(ram)
            else:  # not looking for any confirmations
                self._check_win(ram)

                current_state = State(ram)

                lost = current_state.anything_lost(self.state)
                map = ram[ram_info.map_current_index_c198]

                if lost and map < 8:  # outside of base
                    self.restore_target = self.state
                else:
                    self.state.doors = bytes_or(current_state.doors, self.state.doors)

                    canisters = ram[
                        ram_info.canister_state_d700 + 1:
                        ram_info.canister_state_d700 + CANISTER_ROOM_COUNT * 2:
                        2
                    ]
                    assert len(canisters) == CANISTER_ROOM_COUNT
                    self.process_change(canisters)
                    self.known_cans = canisters

                    await self._process_to_game_queue(ram, self.to_game_queue)
        # else not in game

    async def _restore(self, ram: RamData) -> None:
        if self.restore_target is None:
            return
        if ram.safe_to_write():
            print("doing restore")
            print("target:")
            print(self.restore_target)

            current = State(ram)
            print("current:")
            print(current)

            # TODO: get doors stored on AP server

            to_write = bytes_or(current.doors, self.restore_target.doors)

            if current.doors == to_write:
                self.restore_target = None
                print("restore finished")
                return

            # restore doors
            await self.rai.write(ram_info.door_state_d600, to_write)

    def _check_win(self, ram: RamData) -> None:
        current_win_state = ram.in_win()
        if current_win_state and not self.known_win_state:
            print("found win")
            self.known_win_state = current_win_state
            if not (self.from_game_queue is None):
                self.from_game_queue.put_nowait(
                    AcquireLocationEventFromGame(0)
                )
