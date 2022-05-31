import asyncio
from dataclasses import dataclass
import sys
from typing import ClassVar, Iterator, Literal, Tuple

from zilliandomizer.zri.rai import RAInterface, DOOR_BYTE_COUNT, CANISTER_ROOM_COUNT
from zilliandomizer.zri.events import DoorEventToGame, EventFromGame, EventToGame, \
    AcquireLocationEventFromGame, DeathEventFromGame, LocationRestoreEventToGame


def bits(n: int) -> Iterator[int]:
    """ yield each activated bit of n """
    while n:
        b = n & ((~n) + 1)
        yield b
        n ^= b


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

    def death_from(self, old: "CharState") -> bool:
        return (
            (self.jj == 2 and old.jj != 2) or
            (self.champ == 2 and old.champ != 2) or
            (self.apple == 2 and old.apple != 2)
        )


class Memory:
    """
    puts in from_game_queue when sees events in game

    and puts in to_game_queue when sees losses in game
    """

    @staticmethod
    def get_changed_lost(new: bytes, old: bytes) -> Tuple[int, int, int]:
        """
        changed bits, lost bits, new bits as `int`
        """
        new_int = int.from_bytes(new, Memory.BYTE_ORDER)
        old_int = int.from_bytes(old, Memory.BYTE_ORDER)
        changed = new_int ^ old_int
        lost = changed & old_int
        return changed, lost, new_int

    rai: RAInterface
    from_game_queue: "asyncio.Queue[EventFromGame]"
    to_game_queue: "asyncio.Queue[EventToGame]"

    known_doors: bytes
    """ opened """
    known_canisters: bytes
    """ picked up """
    known_character_states: CharState
    known_win_state: bool

    BYTE_ORDER: ClassVar[Literal['little', 'big']] = sys.byteorder  # type: ignore
    # mypy doesn't see literal types of byteorder

    def __init__(self,
                 from_game_queue: "asyncio.Queue[EventFromGame]",
                 to_game_queue: "asyncio.Queue[EventToGame]") -> None:
        self.rai = RAInterface()
        self.from_game_queue = from_game_queue
        self.to_game_queue = to_game_queue
        self.reset()

    def reset(self) -> None:
        self.known_doors = bytes(0 for _ in range(DOOR_BYTE_COUNT))
        self.known_canisters = bytes(0 for _ in range(CANISTER_ROOM_COUNT))
        self.known_character_states = CharState(0, 0, 0)
        self.known_win_state = False

    def in_game(self) -> bool:
        # c11f is 0x8b any time I'm in the gameplay field
        # c1ad is 1 I think any time after the game is started
        # c300 is 129 after the game is started
        c300 = self.rai.read(0xc300)
        return bool(len(c300)) and c300[0] == 129

    def in_win(self) -> bool:
        c183_l = self.rai.read(0xc183)
        c11f_l = self.rai.read(0xc11f)

        if not (len(c183_l) and len(c11f_l)):
            return False

        c183 = c183_l[0]
        c11f = c11f_l[0]

        #          end credits      curtain call
        return (c11f == 0x8d) or (c11f == 0x8e) or (
            #      cutscene      oh great, ...., end text
            (c11f == 0x86) and (c183 in (1, 8, 9))
        )

    def check(self) -> None:
        if self.in_game():
            self._check_win()
            self._check_doors()
            self._check_canisters()
            self._check_chars()
        else:  # not in game
            print("not in game")

    def _restore(self) -> None:
        # TODO: restore guns, levels, scopes, chars alive with hp
        # self.to_game_queue.put_nowait(LocationRestoreEventToGame(self.known_canisters))
        self.to_game_queue.put_nowait(DoorEventToGame(self.known_doors))

    def _check_win(self) -> None:
        current_win_state = self.in_win()
        if current_win_state and not self.known_win_state:
            self.known_win_state = current_win_state
            self.from_game_queue.put_nowait(
                AcquireLocationEventFromGame(0)
            )

    def _check_canisters(self) -> None:
        # odd numbered bytes are whether they are collected
        canisters = bytes(v for i, v in enumerate(self.rai.read_canisters()) if i & 1)
        if len(canisters) == CANISTER_ROOM_COUNT:
            changed, lost, can_int = Memory.get_changed_lost(canisters, self.known_canisters)
            if changed and (not lost) and self.in_game():
                self.known_canisters = canisters

                # report
                added = changed & can_int
                rooms = added.to_bytes(CANISTER_ROOM_COUNT, Memory.BYTE_ORDER)

                # indexes into rooms
                added_rooms = [i for i, b in enumerate(rooms) if b]

                for room_i in added_rooms:
                    for can in bits(rooms[room_i]):
                        print(f"picked up canister {can} in room {room_i}")
                        loc_id = (room_i << 8) | (can)
                        self.from_game_queue.put_nowait(AcquireLocationEventFromGame(loc_id))
            elif lost:
                self._restore()
                self.to_game_queue.put_nowait(
                    LocationRestoreEventToGame(self.known_canisters)
                )

    def _check_doors(self) -> None:
        doors = self.rai.read_doors()
        if len(doors) == DOOR_BYTE_COUNT:
            changed, lost, doors_int = Memory.get_changed_lost(doors, self.known_doors)
            if changed and (not lost) and self.in_game():  # a double check of in_game
                self.known_doors = doors

                # test - report
                added = changed & doors_int
                added_bytes = added.to_bytes(DOOR_BYTE_COUNT, Memory.BYTE_ORDER)
                added_filtered = [i for i, b in enumerate(added_bytes) if b]
                for each in added_filtered:
                    print(f"opened door in byte {each}")
            elif lost and self.in_game():
                self.from_game_queue

    def _check_chars(self) -> None:
        jj, ch, ap = self.rai.read_char_status()
        if len(jj) == 1 and len(ch) == 1 and len(ap) == 1:
            new_state = CharState(jj[0], ch[0], ap[0])

            if (not new_state.lost_from(self.known_character_states)) and self.in_game():
                # check rescues
                if new_state.jj and not self.known_character_states.jj:
                    print("acquired JJ")
                if new_state.champ and not self.known_character_states.champ:
                    print("acquired Champ")
                if new_state.apple and not self.known_character_states.apple:
                    print("acquired Apple")

                # check deaths
                death_happened = new_state.death_from(self.known_character_states)
                if death_happened:
                    print("death happened")
                    self.from_game_queue.put_nowait(DeathEventFromGame())

                self.known_character_states = new_state
