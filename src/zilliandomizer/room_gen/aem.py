from collections.abc import Iterator
from copy import deepcopy
from random import shuffle

from zilliandomizer.low_resources import rom_info
from .alarm_entrance_data import AlarmEntrance, data, indexes


class AlarmEntranceManager:
    indexes: list[int]
    """ bytes pointing to data - all multiples of 6 because an AlarmEntrance is 6 bytes long """
    data: list[AlarmEntrance | None]
    """
    The order of this data must not change,
    because if there is no ceiling space in one of the rooms,
    the index that points to this list doesn't change.
    """

    def __init__(self) -> None:
        self.indexes = indexes.copy()
        self.data = deepcopy(data)

    def get_ceiling_entrances(self, level: int) -> Iterator[tuple[int, int]]:
        """
        yield in random order, the ceiling entrances (x, index_byte)

        matching closer to the level first
        """
        level_differences: list[list[tuple[int, int]]] = [[], [], []]
        for i, entrance in enumerate(self.data):
            if entrance and entrance.ceiling:
                diff = abs(level - entrance.level)
                level_differences[diff].append((entrance.x, (i + 1) * 6))
        for ld in level_differences:
            shuffle(ld)
        for ld in level_differences:
            yield from ld

    def room_gen_mods(self) -> None:
        """
        this puts all the x coordinates even with tiles
        and makes more variety to find a good tile
        """
        assert self.data[1] and self.data[1].x == 0x88
        self.data[1].x = 0x80
        assert self.data[9] and self.data[9].x == 0xd8
        self.data[9].x = 0xd0
        assert self.data[12] and self.data[12].x == 0x50
        self.data[12].x = 0x40
        assert self.data[13] and self.data[13].x == 0x78
        self.data[13].x = 0x80

    def is_ceiling(self, map_index: int) -> bool:
        i = (self.indexes[map_index] // 6) - 1
        entrance = self.data[i]
        if entrance:
            return entrance.ceiling
        return False

    def get_writes(self) -> dict[int, int]:
        tr: dict[int, int] = {}

        for i in range(136):
            address = rom_info.alarmed_enemy_entrance_table_7f04 + i
            tr[address] = self.indexes[i]

        for i, entrance in enumerate(self.data):
            address = rom_info.alarmed_enemy_entrance_data_7f86 + (6 * (i + 1))
            if entrance is None:
                x = 0
                y = 0
                i_2 = 0
                i_3 = 0
                level = 0
                i_5 = 0
            else:
                x = entrance.x
                y = 0xa0 if entrance.ceiling else 0x98
                i_2 = 0x00 if entrance.ceiling else (
                    0x01 if x < 0x80 else 0xff
                )
                i_3 = 0xff if entrance.ceiling else 0x00
                level = entrance.level
                i_5 = 0x11 if entrance.ceiling else (
                    0x12 if x < 0x80 else 0x13
                )
            tr[address + 0] = x
            tr[address + 1] = y
            tr[address + 2] = i_2
            tr[address + 3] = i_3
            tr[address + 4] = level
            tr[address + 5] = i_5

        return tr
