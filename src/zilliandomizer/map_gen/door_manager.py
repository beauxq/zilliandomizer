from collections import Counter, defaultdict
from enum import IntEnum
from typing import Dict, List, Literal, Tuple
import typing

from zilliandomizer.low_resources import rom_info

BANK_4_OFFSET = 0x8000

DoorStatusIndex = Tuple[int, int]
""" low byte of address and bit mask for whether a door is opened """


class DoorSprite(IntEnum):
    """
    - B blue
    - R red
    - P paperclip
    ---
    - L door in left half of large tile (usually leading to the right)
    - R door in right half of large tile (usually leading to the left)
    - D elevator at bottom to go down
    - U elevator at top to go up
    """
    BL = 0
    BR = 5
    BD = 30
    BU = 31
    RL = 10
    RR = 15
    RD = 32
    RU = 33
    PL = 20
    PR = 25
    PD = 34
    PU = 35

    @staticmethod
    def get_door(map_index: int, x: int) -> "DoorSprite":
        """ `x` in door data structure units (4 pixels) """
        assert (x & 1) == 0, f"{x=}"
        if map_index < 40:
            if x & 2:
                return DoorSprite.BR
            else:
                return DoorSprite.BL
        if map_index < 80:
            if x & 2:
                return DoorSprite.RR
            else:
                return DoorSprite.RL
        if x & 2:
            return DoorSprite.PR
        else:
            return DoorSprite.PL

    @staticmethod
    def get_elevator(map_index: int, y: Literal[0, 5]) -> "DoorSprite":
        """ `y` in door data structure units (0 top, 5 bottom) """
        if map_index < 40:
            if y == 0:
                return DoorSprite.BU
            else:
                return DoorSprite.BD
        if map_index < 80:
            if y == 0:
                return DoorSprite.RU
            else:
                return DoorSprite.RD
        if y == 0:
            return DoorSprite.PU
        else:
            return DoorSprite.PD


class DoorManager:
    status_reference_counts: typing.Counter[DoorStatusIndex]
    """
    how many of the door data structures (in the entire base)
    share the same share the same info on whether the door is open or not

    the index is `(a, b)` - the first 2 bytes of the door data structure
    """
    doors: Dict[int, List[bytes]]
    """
    map_index: [[a, b, x, y, t], ...]
        - a - byte index pointing to data of whether the door is open
        - b - bit mask ^
        - x - `<< 2` for (left) x pixel of door (or elevator)
        - y - 0 top row (both door and elevator), 4 door on bottom, 5 elevator on bottom
        - t - `DoorSprite`
    """

    def __init__(self, rom: bytes) -> None:
        self.status_reference_counts = Counter()
        self.doors = defaultdict(list)

        self._fill(rom)

    def _fill(self, rom: bytes) -> None:
        for map_index in range(136):
            row = map_index // 8
            col = map_index % 8
            room_data_address = rom_info.terrain_index_13725 + 65 * row + 8 * col
            room_data = rom[room_data_address:room_data_address + 8]
            door_data_address = (room_data[5] | (room_data[6] * 256)) + BANK_4_OFFSET
            door_count = rom[door_data_address]
            door_data_address += 1
            while door_count > 0:
                door_data = rom[door_data_address:door_data_address + 5]
                a, b, _, _, _ = door_data
                status: DoorStatusIndex = (a, b)
                self.status_reference_counts[status] += 1
                self.doors[map_index].append(door_data)

                door_count -= 1
                door_data_address += 5

    def get_writes(self) -> Dict[int, int]:
        null_address = rom_info.door_data_begin_13ce8
        null_banked_lo = null_address & 0xff
        null_banked_hi = (null_address - BANK_4_OFFSET) // 256
        tr = {null_address: 0}
        address = null_address + 1

        for map_index in range(136):
            row = map_index // 8
            col = map_index % 8
            door_data_pointer_address = rom_info.terrain_index_13725 + 65 * row + 8 * col + 5
            doors = self.doors[map_index]
            if len(doors) == 0:
                print(f"room {map_index} no doors")
                tr[door_data_pointer_address] = null_banked_lo
                tr[door_data_pointer_address + 1] = null_banked_hi
            else:
                print(f"room {map_index} {len(doors)} doors")
                banked_data_address = address - BANK_4_OFFSET
                banked_data_lo = banked_data_address & 0xff
                banked_data_hi = banked_data_address // 256
                tr[door_data_pointer_address] = banked_data_lo
                tr[door_data_pointer_address + 1] = banked_data_hi

                tr[address] = len(doors)
                address += 1
                for door in doors:
                    for b in door:
                        tr[address] = b
                        address += 1

        return tr
