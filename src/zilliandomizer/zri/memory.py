import asyncio
from collections import Counter
import sys
from types import TracebackType
from typing import Dict, Final, Literal, Optional, Tuple, Iterator
import typing

from zilliandomizer.logic_components.items import RESCUE, NORMAL
from zilliandomizer.low_resources import ram_info
from zilliandomizer.patch import RescueInfo
from zilliandomizer.zri.events import EventFromGame, EventToGame, \
    AcquireLocationEventFromGame, ItemEventToGame, DeathEventToGame, \
    WinEventFromGame
from zilliandomizer.zri.rai import CANISTER_ROOM_COUNT, RAInterface, DOOR_BYTE_COUNT, RamData

BYTE_ORDER: Final[Literal['little', 'big']] = sys.byteorder  # type: ignore
# mypy doesn't see literal types of byteorder

ITEM_BYTE_COUNT = 0x0c
""" highest item id is 0x0b, using from 0 to 0x0b """


def bits(n: int) -> Iterator[int]:
    """ yield each activated bit of n """
    while n:
        b = n & ((~n) + 1)
        yield b
        n ^= b


def bytes_or(a: bytes, b: bytes) -> bytes:
    assert len(a) == len(b), f"requires parameters the same length, {len(a)}, {len(b)}"
    return bytes(a[i] | b[i] for i in range(len(a)))


class State:
    doors: bytes
    """ opened """
    received_items: bytearray
    """ index is item id (rescues 3 and 4) """

    def __init__(self, ram: Optional[RamData] = None) -> None:
        if ram:
            self.doors = ram[ram_info.door_state_d600: ram_info.door_state_d600 + DOOR_BYTE_COUNT]
            self.received_items = bytearray(
                ram[ram_info.item_pickup_queue: ram_info.item_pickup_queue + ITEM_BYTE_COUNT]
            )
        else:
            self.reset()

    def reset(self) -> None:
        self.doors = bytes(0 for _ in range(DOOR_BYTE_COUNT))
        self.received_items = bytearray(0 for _ in range(ITEM_BYTE_COUNT))

    def anything_lost(self, old: "State") -> bool:
        _, door_lost, _ = get_changed_lost(self.doors, old.doors)
        items_lost = any(self.received_items[i] < old.received_items[i]
                         for i in range(ITEM_BYTE_COUNT))

        # self.diff_cache = StateDiffCache(door_change, door_lost, door_int)

        return bool(door_lost) or bool(items_lost)


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
    """

    _rai: RAInterface
    rescues: Dict[int, Tuple[int, int]]
    """ { ram_char_status_address: (item_room_index, mask) } """
    loc_mem_to_loc_id: Dict[int, int]
    """ { ((item_room_index << 8) | bit_mask): location_id } """
    from_game_queue: "Optional[asyncio.Queue[EventFromGame]]"
    to_game_queue: "asyncio.Queue[EventToGame]"

    _restore_target: Optional[State]

    known_cans: bytes
    known_in_game: bool
    known_win_state: bool

    state: State

    def __init__(self,
                 from_game_queue: "Optional[asyncio.Queue[EventFromGame]]" = None,
                 to_game_queue: "Optional[asyncio.Queue[EventToGame]]" = None) -> None:
        """
        `rescues` maps a rescue id (0 or 1) to a canister location where that rescue is

        `loc_mem_to_loc_id` maps memory location of canister (room code and bit mask) to location id
        """
        self._rai = RAInterface()

        self.from_game_queue = from_game_queue
        self.to_game_queue = to_game_queue or asyncio.Queue()

        self._restore_target = None

        self.state = State()
        self.reset()

    async def check_for_player_name(self) -> bytes:
        """
        returns the data passed to zilliandomizer.patch.Patcher.set_rom_to_ram_data,
        empty bytes if not available
        """
        ram = await self._rai.read()

        if not ram.all_present():
            return b''

        name = ram[ram_info.rom_to_ram_data: ram_info.rom_to_ram_data + 16]
        null_index = name.find(b'\x00')
        if null_index == -1:
            null_index = len(name)
        return name[:null_index]

    def set_generation_info(self,
                            rescues: Dict[int, RescueInfo],
                            loc_mem_to_loc_id: Dict[int, int]) -> None:
        self.rescues = {}
        for rescue_id, ri in rescues.items():
            if ri.start_char == "JJ":
                address = ram_info.apple_status_c170 if rescue_id == 0 else ram_info.champ_status_c160
            elif ri.start_char == "Apple":
                address = ram_info.jj_status_c150 if rescue_id == 0 else ram_info.champ_status_c160
            else:  # start char Champ
                address = ram_info.apple_status_c170 if rescue_id == 0 else ram_info.jj_status_c150
            self.rescues[address] = (ri.room_code // 2, ri.mask)

        self.loc_mem_to_loc_id = loc_mem_to_loc_id

    def reset(self) -> None:
        self.known_in_game = False
        self.known_win_state = False
        self.known_cans = bytes(0 for _ in range(CANISTER_ROOM_COUNT))

        self.state.reset()

    def __enter__(self) -> "Memory":
        return self

    def close(self) -> None:
        if self._rai.sock:
            self._rai.sock.close()

    def __exit__(self, type: type, value: Exception, traceback: TracebackType) -> None:
        self.close()

    def _in_game(self, scene: int) -> bool:
        """ given the scene value from ram, process and return whether the game is started """
        in_game = (scene & 0x7f) in c11f_in_game_scenes
        if in_game != self.known_in_game:
            print(f"in game: {in_game}")
            self.known_in_game = in_game
        return in_game

    def _process_change(self, new_cans: bytes) -> None:
        # report
        change, _, new_int = get_changed_lost(new_cans, self.known_cans)
        added = change & new_int
        rooms = added.to_bytes(CANISTER_ROOM_COUNT, BYTE_ORDER)

        # indexes into rooms
        added_rooms = [i for i, b in enumerate(rooms) if b]

        for item_room_index in added_rooms:
            for can in bits(rooms[item_room_index]):
                print(f"picked up canister {can} in room {item_room_index}")
                if self.from_game_queue is None:
                    continue
                loc_memory = (item_room_index << 8) | (can)
                if loc_memory not in self.loc_mem_to_loc_id:
                    continue
                loc_id = self.loc_mem_to_loc_id[loc_memory]
                self.from_game_queue.put_nowait(
                    AcquireLocationEventFromGame(loc_id)
                )

    async def _process_to_game_queue(self, ram: RamData, q: "asyncio.Queue[EventToGame]") -> None:
        if q.qsize():
            if ram.safe_to_write():
                event = q.get_nowait()
                if isinstance(event, ItemEventToGame):
                    counts = Counter(event.ids)
                    await self._process_items(counts)
                elif isinstance(event, DeathEventToGame):
                    await self._rai.write(0xc308, [0x84])
                else:
                    print(f"WARNING: unhandled EventToGame {event}")
                q.task_done()

    async def _process_items(self, counts: typing.Counter[int]) -> None:
        counts_to_ram = bytearray(0 for _ in range(0x0c))
        for comm_item_id in counts:
            code = comm_item_id >> 8
            item_id = comm_item_id & 0xff
            if item_id == 0x04:  # empty
                # don't send empties to game
                continue
            if code == RESCUE:
                if item_id in (0, 1):
                    # 3 Apple, 4 Champ
                    item_id += 3
                else:
                    print(f"WARNING: invalid item id {comm_item_id} received with code rescue")
            elif code == NORMAL:
                if 0x05 <= item_id <= 0x0b:
                    pass
                else:
                    print(f"WARNING: invalid item id {comm_item_id} received with code normal")
            else:  # not rescue or normal
                print(f"WARNING: invalid item code {code} received")
            counts_to_ram[item_id] = counts[comm_item_id]
        if all((counts_to_ram[i] >= self.state.received_items[i])
               for i in range(ITEM_BYTE_COUNT)):
            for i in range(ITEM_BYTE_COUNT):
                new_count = counts_to_ram[i] - self.state.received_items[i]
                if new_count:
                    print(f"sending item {i}: {new_count}")
            await self._rai.write(ram_info.item_pickup_queue, counts_to_ram)
            self.state.received_items = counts_to_ram
        else:
            print(f"WARNING: sync problem - items lost {counts_to_ram} < {self.state.received_items}")
            # else not a good time to send something to game
        # else queue empty

    async def check(self) -> None:
        """ put info from game into from_game queue """
        ram = await self._rai.read()

        if not ram.all_present():
            return  # TODO: signal when data isn't retrieved?

        current_scene = ram[ram_info.current_scene_c11f]
        if self._in_game(current_scene):
            if self._restore_target:
                await self._restore(ram)
            else:
                self._check_win(ram)

                # TODO: check for base explosion timer? boss dead?
                # AcquireLocationEventFromGame(0)

                current_state = State(ram)

                lost = current_state.anything_lost(self.state)
                map = ram[ram_info.map_current_index_c198]

                if lost and map < 8:  # outside of base
                    self._restore_target = self.state
                else:
                    self.state.doors = bytes_or(current_state.doors, self.state.doors)

                    canisters = bytearray(ram[
                        ram_info.canister_state_d700 + 1:
                        ram_info.canister_state_d700 + CANISTER_ROOM_COUNT * 2:
                        2
                    ])
                    assert len(canisters) == CANISTER_ROOM_COUNT

                    # rescues don't show up in canister state
                    for address, canister in self.rescues.items():
                        item_room_index, mask = canister
                        if ram[address] > 0:
                            canisters[item_room_index] |= mask
                        else:  # not rescued
                            canisters[item_room_index] &= (~mask)

                    self._process_change(canisters)
                    self.known_cans = canisters

                    pushed_items = ram[
                        ram_info.item_pickup_queue:
                        ram_info.item_pickup_queue + ITEM_BYTE_COUNT
                    ]
                    self.state.received_items = bytearray(pushed_items)

                    await self._process_to_game_queue(ram, self.to_game_queue)
        # else not in game

    async def _restore(self, ram: RamData) -> None:
        if self._restore_target is None:
            return
        if ram.safe_to_write():
            print("doing restore")
            print("target:")
            print(self._restore_target)

            current = State(ram)
            print("current:")
            print(current)

            # TODO: get doors stored on AP server

            to_write = bytes_or(current.doors, self._restore_target.doors)

            if current.doors == to_write:
                self._restore_target = None
                print("restore finished")
                return

            # restore doors
            await self._rai.write(ram_info.door_state_d600, to_write)

    def _check_win(self, ram: RamData) -> None:
        """
        check for win state in game and
        if a new win state is found, put win event in from queue
        """
        current_win_state = ram.in_win()
        if current_win_state and not self.known_win_state:
            print("found win")
            self.known_win_state = current_win_state
            if not (self.from_game_queue is None):
                # TODO: move acquire main to when boss is dead, or something like that
                self.from_game_queue.put_nowait(
                    AcquireLocationEventFromGame(0)
                )
                self.from_game_queue.put_nowait(
                    WinEventFromGame()
                )
