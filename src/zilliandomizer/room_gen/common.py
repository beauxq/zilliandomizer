from dataclasses import dataclass
from typing import List, Tuple

Coord = Tuple[int, int]
""" row, col - 0 inside walls """

TOP_LEFT = (1, 0)
BOT_LEFT = (5, 0)
TOP_RIGHT = (1, 12)
BOT_RIGHT = (5, 12)

FOUR_CORNERS = [TOP_LEFT, BOT_LEFT, TOP_RIGHT, BOT_RIGHT]


@dataclass
class RoomData:
    exits: List[Coord]
    computer: bool


def coord_to_pixel(coord: Coord) -> Tuple[int, int]:
    """ returns y_pixel [0x18, 0x98], x_pixel [0x10, 0xe0] """
    y_coord, x_coord = coord
    y_pixel = 0x20 * y_coord - 8
    x_pixel = x_coord * 0x10 + 0x10
    return y_pixel, x_pixel
