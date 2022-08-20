from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import typing
from zilliandomizer.low_resources import rom_info

BANK_4_OFFSET = 0x8000

DoorStatus = Tuple[int, int]
""" low byte of address and bit mask for whether a door is opened """


class DoorManager:
    status_reference_counts: typing.Counter[DoorStatus]
    doors: Dict[int, List[bytes]]
    """ map_index: [[a, b, x, y, t], ...] """

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
                status: DoorStatus = (a, b)
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
