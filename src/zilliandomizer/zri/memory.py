import asyncio
from dataclasses import dataclass
import sys
from typing import ClassVar, Iterator, List, Literal, Tuple, Optional, cast
from zilliandomizer.logic_components.items import NORMAL, RESCUE
from zilliandomizer.low_resources import ram_info
from zilliandomizer.options import chars, ID

from zilliandomizer.zri.rai import RAInterface, DOOR_BYTE_COUNT, CANISTER_ROOM_COUNT
from zilliandomizer.zri.events import DeathEventToGame, EventFromGame, EventToGame, \
    AcquireLocationEventFromGame, DeathEventFromGame, ItemEventToGame

BYTE_ORDER: ClassVar[Literal['little', 'big']] = sys.byteorder  # type: ignore
# mypy doesn't see literal types of byteorder

# TODO: I want memory to handle both to and from,
# because I don't want anything coming in while restoring lost state.

# also check item trigger ram before read
# only do read if no write in progress,
# only do write if no read and restore in progress


def bits(n: int) -> Iterator[int]:
    """ yield each activated bit of n """
    while n:
        b = n & ((~n) + 1)
        yield b
        n ^= b


def bcd_decode(x: int) -> int:
    """ from bcd hex to int """
    lo_n = x & 0x0f
    hi_n = x >> 4
    return hi_n * 10 + lo_n


def bcd_encode(x: int) -> int:
    """ from int to bcd hex (2 decimal digits only) """
    lo = x % 10
    hi = x // 10
    return (hi << 4) | lo


@dataclass
class CharState:
    """ 0 not rescued, 1 rescued alive, 2 dead """
    jj: int
    champ: int
    apple: int

    def lost_from(self, old: "CharState") -> bool:
        return (
            (self.jj == 0 and old.jj > 0) or
            (self.champ == 0 and old.champ > 0) or
            (self.apple == 0 and old.apple > 0)
        )

    def print_new(self, old: "CharState") -> None:
        if self.jj and not old.jj:
            print("acquired JJ")
        if self.champ and not old.champ:
            print("acquired Champ")
        if self.apple and not old.apple:
            print("acquired Apple")

    def death_from(self, old: "CharState") -> bool:
        return (
            (self.jj == 2 and old.jj != 2) or
            (self.champ == 2 and old.champ != 2) or
            (self.apple == 2 and old.apple != 2)
        )


@dataclass(init=False)
class Acquires:
    highest_opa: ClassVar[int] = 0
    max_level: ClassVar[int] = 0
    """ max level (0-7) (updates after level up) """

    gun: int
    level: int
    opa: int
    scopes: Tuple[int, int, int]

    def __init__(self, gun: int, level: int, opa: int, scopes: Tuple[int, int, int]) -> None:
        self.gun = gun
        self.level = level
        self.opa = opa
        self.scopes = scopes

        # If someone grabs 2 opas fast between memory polls
        # to get to a level up,
        # and has never leveled up more slowly,
        # this `highest_opa` won't be right.
        # Then that incorrect info will only be an issue
        # if a restore is needed.
        # This seems like it would be pretty rare,
        # so I'm not worried about it.
        Acquires.highest_opa = max(Acquires.highest_opa, opa)

    def lost_from(self, old: "Acquires") -> bool:
        lost_gun = self.gun < old.gun
        lost_opa = self.level < old.level or (
            self.level == old.level and
            self.level < Acquires.max_level and
            self.opa < old.opa
        )
        lost_scope = any(self.scopes[i] < old.scopes[i] for i in range(3))

        return lost_gun or lost_opa or lost_scope

    def print_new(self, old: "Acquires") -> None:
        if self.gun > old.gun:
            print(f"acquired gun: {self.gun}")
        if self.level > old.level or (
            self.level == old.level and self.level < Acquires.max_level and self.opa > old.opa
        ):
            print(f"acquired level: {self.level + 1}  opa: {self.opa}")
        for i in range(3):
            if self.scopes[i] > old.scopes[i]:
                print(f"{chars[i]} acquired scope")


c11f_in_game_scenes = frozenset((
    # continue, explode, cs, ship, computer, pause, play, main computer
    3, 4, 6, 7, 8, 9, 0xb, 0xc
))


@dataclass
class StateDiffCache:
    door_change: int
    door_lost: int
    door_int: int
    can_change: int
    canister_lost: int
    can_int: int


class State:
    """ everything I want to restore """

    @staticmethod
    def get_changed_lost(new: bytes, old: bytes) -> Tuple[int, int, int]:
        """
        changed bits, lost bits, new bits as `int`
        """
        new_int = int.from_bytes(new, BYTE_ORDER)
        old_int = int.from_bytes(old, BYTE_ORDER)
        changed = new_int ^ old_int
        lost = changed & old_int
        return changed, lost, new_int

    char_state: CharState
    acquires: Acquires
    doors: bytes
    """ opened """
    canisters: bytes
    """ picked up """
    diff_cache: Optional[StateDiffCache] = None

    def reset(self) -> None:
        self.doors = bytes(0 for _ in range(DOOR_BYTE_COUNT))
        self.canisters = bytes(0 for _ in range(CANISTER_ROOM_COUNT))
        self.char_state = CharState(0, 0, 0)
        self.acquires = Acquires(0, 0, 0, (0, 0, 0))

    def anything_lost(self, old: "State") -> bool:
        door_change, door_lost, door_int = State.get_changed_lost(self.doors, old.doors)
        can_change, can_lost, can_int = State.get_changed_lost(self.canisters, old.canisters)
        char_lost = self.char_state.lost_from(old.char_state)
        acq_lost = self.acquires.lost_from(old.acquires)

        self.diff_cache = StateDiffCache(door_change, door_lost, door_int, can_change, can_lost, can_int)

        return bool(door_lost) or bool(can_lost) or char_lost or acq_lost

    def process_change(self,
                       old: "State",
                       from_game_queue: "Optional[asyncio.Queue[EventFromGame]]") -> None:
        assert self.diff_cache

        # can change
        # report
        added = self.diff_cache.can_change & self.diff_cache.can_int
        rooms = added.to_bytes(CANISTER_ROOM_COUNT, BYTE_ORDER)

        # indexes into rooms
        added_rooms = [i for i, b in enumerate(rooms) if b]

        for room_i in added_rooms:
            for can in bits(rooms[room_i]):
                print(f"picked up canister {can} in room {room_i}")
                loc_id = (room_i << 8) | (can)
                if not (from_game_queue is None):
                    from_game_queue.put_nowait(
                        AcquireLocationEventFromGame(loc_id)
                    )

        # door change
        # test - report
        added = self.diff_cache.door_change & self.diff_cache.door_int
        added_bytes = added.to_bytes(DOOR_BYTE_COUNT, BYTE_ORDER)
        added_filtered = [i for i, b in enumerate(added_bytes) if b]
        for each in added_filtered:
            print(f"opened door in byte {each}")

        # char change
        # check rescues
        self.char_state.print_new(old.char_state)

        # check deaths
        death_happened = self.char_state.death_from(old.char_state)
        if death_happened:
            print("death happened")
            if not (from_game_queue is None):
                from_game_queue.put_nowait(DeathEventFromGame())

        # acquire change
        self.acquires.print_new(old.acquires)

    def __repr__(self) -> str:
        doors = sum(bin(d).count('1') for d in self.doors)
        cans = sum(bin(c).count('1') for c in self.canisters)
        return f"State(doors={doors}, cans={cans}, {str(self.acquires)}, {str(self.char_state)})"

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, State):
            return False
        return self.doors == __o.doors \
            and self.canisters == __o.canisters \
            and self.acquires == __o.acquires \
            and self.char_state == __o.char_state


class Memory:
    """
    puts in from_game_queue when sees events in game

    and puts in to_game_queue when sees losses in game
    """

    rai: RAInterface
    from_game_queue: "Optional[asyncio.Queue[EventFromGame]]"
    to_game_queue: "asyncio.Queue[EventToGame]"
    restore_queue: "asyncio.Queue[EventToGame]"

    looking_for_send_confirmation: int
    """ item id sent (comm id 2 bytes) """

    restore_target: Optional[State]

    known_in_game: bool
    known_win_state: bool

    state: State

    def __init__(self,
                 from_game_queue: "Optional[asyncio.Queue[EventFromGame]]" = None,
                 to_game_queue: "Optional[asyncio.Queue[EventToGame]]" = None) -> None:
        self.rai = RAInterface()
        self.from_game_queue = from_game_queue
        self.to_game_queue = to_game_queue or asyncio.Queue()
        self.restore_queue = asyncio.Queue()

        self.restore_target = None

        self.state = State()
        self.reset()

    def reset(self) -> None:
        self.looking_for_send_confirmation = 0

        self.known_in_game = True  # default True to see change to False at beginning
        self.known_win_state = False

        self.state.reset()

    def in_game(self) -> bool:
        """
        game has started - might be in computer or cutscene or ending

        use `in_game_play` for something more strict
        """
        # c11f is 0x8b any time I'm in the gameplay field
        # c1ad is 1 I think any time after the game is started
        c11f = self.rai.read(ram_info.current_scene_c11f)
        in_game = bool(len(c11f)) and \
            (c11f[0] & 0x7f) in c11f_in_game_scenes
        if in_game != self.known_in_game:
            print(f"in game: {in_game}")
            self.known_in_game = in_game
        return in_game

    def in_game_play(self) -> bool:
        """ in the state where can move/jump/shoot """
        c11f_l = self.rai.read(ram_info.current_scene_c11f)
        if len(c11f_l) != 1:
            return False
        c11f = c11f_l[0]
        return c11f == 0x8b

    def current_hp(self) -> int:
        """ returns 0 if read fails """
        c143_l = self.rai.read(0xc143)
        if len(c143_l) != 1:
            return 0
        c143 = c143_l[0]
        # binary coded decimal / 10
        return bcd_decode(c143) * 10

    def _check_item_trigger(self) -> bool:
        """ True if ram value 0 (available for sending an item) """
        c2ea = self.rai.read(0xc2ea)
        return (len(c2ea) == 1) and (c2ea[0] == 0)

    def in_win(self) -> bool:
        c183_l = self.rai.read(0xc183)
        c11f_l = self.rai.read(ram_info.current_scene_c11f)

        if not (len(c183_l) and len(c11f_l)):
            return False

        c183 = c183_l[0]
        c11f = c11f_l[0]

        # TODO: decide: currently end credits and curtain call are not
        # possible to detect because they're not in in_game set
        # should I consider end credits and curtain call in game?
        # or is it enough to just detect the 3 cutscenes before curtain call?
        #          end credits      curtain call
        return (c11f == 0x8d) or (c11f == 0x8e) or (
            #      cutscene      oh great, ...., end text
            (c11f == 0x86) and (c183 in (1, 8, 9))
        )

    def _safe_to_write(self) -> bool:
        """ in game play and current hp > 0 and item trigger ready """
        return self.in_game_play() and \
            bool(self.current_hp()) and \
            self._check_item_trigger()

    def _process_to_game_queue(self, q: "asyncio.Queue[EventToGame]") -> None:
        if q.qsize():
            if self._safe_to_write():
                event = q.get_nowait()
                if isinstance(event, ItemEventToGame):
                    comm_item_id = event.id
                    code = comm_item_id >> 8
                    item_id = comm_item_id & 0xff
                    if code == RESCUE:
                        if item_id in (0, 1):
                            # 3 Apple, 4 Champ
                            item_id += 3
                            self.rai.write(0xc2ea, [item_id])
                            self.looking_for_send_confirmation = comm_item_id
                        else:
                            print(f"WARNING: invalid item id {comm_item_id} received")
                    elif code == NORMAL:
                        if 0x05 <= item_id <= 0x0b:
                            print(f"sending item {item_id} to game")
                            self.rai.write(0xc2ea, [item_id])
                            self.looking_for_send_confirmation = comm_item_id
                        else:
                            print(f"WARNING: invalid item id {comm_item_id} received")
                    else:  # not rescue or normal
                        print(f"WARNING: invalid item id {comm_item_id} received")
                elif isinstance(event, DeathEventToGame):
                    self.rai.write(0xc308, [0x84])
                else:
                    print(f"WARNING: unhandled EventToGame {event}")
                q.task_done()
            # else not a good time to send something to game
        # else queue empty

    def check(self) -> None:
        if self.in_game():
            if self.looking_for_send_confirmation:
                if self._check_item_trigger():
                    self.looking_for_send_confirmation = 0
                else:  # no confirmation
                    # TODO: if x time passes, put item sent (id in flag) back in queue?
                    pass
            elif self.restore_target:
                self._restore()
            else:  # not looking for any confirmations
                self._check_win()

                current = self._get_state()
                lost = current.anything_lost(self.state)

                if lost:
                    self.restore_target = self.state
                else:
                    current.process_change(self.state, self.from_game_queue)
                    self.state = current
                    self._process_to_game_queue(self.to_game_queue)
        # else not in game

    def _restore(self) -> None:
        if self.restore_queue.qsize():
            self._process_to_game_queue(self.restore_queue)
            return
        if self.restore_target is None:
            return
        if self._safe_to_write():
            print("doing restore")
            print("target:")
            print(self.restore_target)

            current = self._get_state()
            print("current:")
            print(current)

            if current == self.restore_target:
                self.restore_target = None
                print("restore finished")
                return

            # restore guns
            guns = current.acquires.gun
            if self.restore_target.acquires.gun != guns:
                print("putting 1 gun in restore queue")
                self.restore_queue.put_nowait(ItemEventToGame(
                    (NORMAL << 8) | ID.gun
                ))
                self.rai.write(ram_info.guns_c2ec, [self.restore_target.acquires.gun - 1])

            # restore opas
            opas = current.acquires.opa
            level = current.acquires.level
            if self.restore_target.acquires.level > level or (
                self.restore_target.acquires.level == level and
                level < Acquires.max_level and
                self.restore_target.acquires.opa > opas
            ):

                def write(lev: int, op: int) -> None:
                    for level_addr in (
                        ram_info.level_c145 + i * 16
                        for i in range(4)
                    ):
                        self.rai.write(level_addr, [lev])
                    self.rai.write(ram_info.opas_c2ee, [op])

                if self.restore_target.acquires.level > 0:
                    add_opas = self.restore_target.acquires.opa + 1
                    for _ in range(add_opas):
                        self.restore_queue.put_nowait(ItemEventToGame(
                            (NORMAL << 8) | ID.opa
                        ))
                    write(self.restore_target.acquires.level - 1, Acquires.highest_opa)
                else:  # highest level seen is 0, just missing opas
                    write(self.restore_target.acquires.level, self.restore_target.acquires.opa)

            # restore scopes
            # TODO: restore scope to current char doesn't work
            # need current char ram
            scopes = self.restore_target.acquires.scopes
            self.rai.write(ram_info.jj_scope_c159, [scopes[0]])
            self.rai.write(ram_info.champ_scope_c169, [scopes[1]])
            self.rai.write(ram_info.apple_scope_c179, [scopes[2]])

            # restore canisters (opened same acquired)
            restoring_canisters: List[int] = []
            for can in self.restore_target.canisters:
                restoring_canisters.append(can)
                restoring_canisters.append(can)
            self.rai.write(0xd700, restoring_canisters)

            # restore doors
            self.rai.write(0xd600, self.restore_target.doors)

            # restore to rescued or not rescued, not to dead
            self.rai.write(0xc150, [min(1, self.restore_target.char_state.jj)])
            self.rai.write(0xc160, [min(1, self.restore_target.char_state.champ)])
            self.rai.write(0xc170, [min(1, self.restore_target.char_state.apple)])

            # setting to 10 hp if 0
            for char_hp_addr in (0xc153, 0xc163, 0xc173):
                hp_l = self.rai.read(char_hp_addr)
                if len(hp_l) and hp_l[0] == 0:
                    self.rai.write(char_hp_addr, [1])

    def _check_win(self) -> None:
        current_win_state = self.in_win()
        if current_win_state and not self.known_win_state:
            print("found win")
            self.known_win_state = current_win_state
            if not (self.from_game_queue is None):
                self.from_game_queue.put_nowait(
                    AcquireLocationEventFromGame(0)
                )

    def _get_state(self) -> State:
        canisters = bytes(v for i, v in enumerate(self.rai.read_canisters()) if i & 1)
        doors = self.rai.read_doors()
        jj, ch, ap = self.rai.read_char_status()

        gun_l = self.rai.read(ram_info.guns_c2ec)
        level_l = self.rai.read(ram_info.level_c145)
        opa_l = self.rai.read(ram_info.opas_c2ee)
        scopes_l = tuple(
            self.rai.read(a)
            for a in (
                ram_info.jj_scope_c159,
                ram_info.champ_scope_c169,
                ram_info.apple_scope_c179
            )
        )
        max_level_l = self.rai.read(ram_info.max_level)

        if len(gun_l) == 1 and \
                len(level_l) == 1 and \
                len(opa_l) == 1 and \
                all([len(a) == 1 for a in scopes_l]) and \
                len(max_level_l) == 1 and \
                len(canisters) == CANISTER_ROOM_COUNT and \
                len(doors) == DOOR_BYTE_COUNT and \
                len(jj) == 1 and len(ch) == 1 and len(ap) == 1:
            Acquires.max_level = max(Acquires.max_level, max_level_l[0])

            current = State()
            current.canisters = canisters
            current.doors = doors
            current.char_state = CharState(jj[0], ch[0], ap[0])
            these_acquires = Acquires(
                gun_l[0],
                level_l[0],
                opa_l[0],
                cast(Tuple[int, int, int], tuple(s[0] for s in scopes_l))
            )
            current.acquires = these_acquires
            return current
        return self.state
