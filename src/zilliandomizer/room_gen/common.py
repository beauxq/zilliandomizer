from collections.abc import Collection
from dataclasses import dataclass

Coord = tuple[int, int]
""" row, col - 0 inside walls """

EdgeDoors = tuple[Collection[int], Collection[int]] | None
"""
for the left wall and the right wall, the y tiles with the platforms that I can walk out of the room on

`None` for putting the doors in the same place as vanilla
"""

TOP_LEFT = (1, 0)
BOT_LEFT = (5, 0)
TOP_RIGHT = (1, 12)
BOT_RIGHT = (5, 12)

FOUR_CORNERS = [TOP_LEFT, BOT_LEFT, TOP_RIGHT, BOT_RIGHT]


@dataclass
class RoomData:
    exits: list[Coord]
    computer: bool
    no_space: list[Coord]
    edge_doors: EdgeDoors = None
    dead_end_can: Coord | None = None
    split_dip_entrance: Coord | None = None


def coord_to_pixel(coord: Coord) -> tuple[int, int]:
    """ returns y_pixel [0x18, 0x98] (-8 for y_coord 0), x_pixel [0x10, 0xe0] """
    y_coord, x_coord = coord
    y_pixel = 0x20 * y_coord - 8
    x_pixel = x_coord * 0x10 + 0x10
    return y_pixel, x_pixel
