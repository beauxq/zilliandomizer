from random import shuffle
from typing import List
from zilliandomizer.room_gen.common import Coord
from zilliandomizer.room_gen.maze import LEFT, RIGHT, TOP, Cell, Grid


class AutoGunPlaces:
    down: List[Coord]
    right: List[Coord]
    left: List[Coord]

    def __init__(self) -> None:
        self.down = []
        self.right = []
        self.left = []


def auto_gun_places(g: Grid) -> AutoGunPlaces:
    """
    finds all the places that auto-guns can go in each orientations
    and shuffles them within each orientation
    """
    tr = AutoGunPlaces()
    for y, row in enumerate(g.data):
        for x, this_cell in enumerate(row):
            if this_cell in (Cell.floor, Cell.space) and not g.in_exit(y, x):
                here = (y, x)
                if y == TOP or g.data[y - 1][x] != Cell.space:
                    tr.down.append(here)
                if x == LEFT or g.data[y][x - 1] == Cell.wall:
                    tr.right.append(here)
                if x == RIGHT or g.data[y][x + 1] == Cell.wall:
                    tr.left.append(here)
    shuffle(tr.down)
    shuffle(tr.right)
    shuffle(tr.left)
    return tr
