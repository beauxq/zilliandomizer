from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterator, List, Tuple

from zilliandomizer.low_resources import rom_info


@dataclass
class Sprite:
    ram: int
    """ ram address where this byte is loaded """
    y: int
    x: int
    type: Tuple[int, int]

    def to_bytes(self) -> bytes:
        return bytes([
            self.ram % 256,
            self.ram // 256,
            self.x,
            self.y,
            self.type[0],
            self.type[1]
        ])

    @staticmethod
    def from_bytes(b: bytes) -> "Sprite":
        assert len(b) == 6, f"Sprite data structure in rom should be 6 bytes - found {len(b)}"
        ram_lo, ram_hi, x, y, sprite_type, subtype = b
        return Sprite(
            ram_lo | (ram_hi * 256),
            y,
            x,
            (sprite_type, subtype)
        )


Sprite.__doc__ = rom_info.np_sprites_80b6.__doc__


RoomSprites = List[Sprite]
""" all the sprites in 1 room """


def sprite_rooms(rom: bytes) -> Iterator[int]:
    """ iterator that gives the address to the sprite data in each room """
    for map_index in range(136):
        room_pointer = rom_info.np_sprites_80b6 + 2 * map_index
        room_addr_lo = rom[room_pointer]
        room_addr_hi = rom[room_pointer + 1]
        yield (room_addr_hi * 256) | room_addr_lo


class NPSpriteManager:
    _rom: bytes
    _data: Dict[int, RoomSprites]
    """ `{ map_index: room_sprites }` """
    _saved_data: Dict[int, RoomSprites]

    def __init__(self, rom: bytes) -> None:
        self._rom = rom
        self._load()
        self.save_state()

    def _load(self) -> None:
        print("loading non-player sprites...")
        self._data = {}

        for map_index, room_address in enumerate(sprite_rooms(self._rom)):
            room_sprites: RoomSprites = []
            count = self._rom[room_address]
            for sprite_no in range(count):
                sprite_address = room_address + 1 + 6 * sprite_no
                room_sprites.append(Sprite.from_bytes(
                    self._rom[sprite_address:sprite_address + 6]
                ))
            self._data[map_index] = room_sprites

    def get_room(self, map_index: int) -> RoomSprites:
        return deepcopy(self._data[map_index])

    def set_room(self, map_index: int, sprites: RoomSprites) -> None:
        assert len(sprites) == len(self._data[map_index]), \
            f"wrong number of sprites in room {map_index}: " \
            f"{len(sprites)} should be {len(self._data[map_index])}"
        self._data[map_index] = sprites

    def get_writes(self) -> Dict[int, int]:
        tr: Dict[int, int] = {}

        for map_index, room_address in enumerate(sprite_rooms(self._rom)):
            room_sprites = self._data[map_index]
            for sprite_no, sprite in enumerate(room_sprites):
                # not changing the number of sprites in each room
                sprite_address = room_address + 1 + 6 * sprite_no
                b = sprite.to_bytes()
                for i, byte in enumerate(b):
                    tr[sprite_address + i] = byte

        return tr

    def save_state(self) -> None:
        self._saved_data = deepcopy(self._data)

    def load_state(self) -> None:
        self._data = deepcopy(self._saved_data)
