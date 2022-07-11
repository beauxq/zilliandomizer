from dataclasses import dataclass
from random import shuffle
from typing import FrozenSet, List
from zilliandomizer.room_gen.common import Coord
from zilliandomizer.room_gen.maze import BOTTOM, LEFT, RIGHT, TOP, Cell, Grid


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
            if this_cell != Cell.wall and not g.in_exit(y, x):
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


@dataclass
class BarPlace:
    """
    horizontal bars go at the bottom of the large tiles
    """
    c: Coord
    horizontal: bool
    length: int


class BarrierPlaces:
    floor_things: FrozenSet[Coord]
    bars: List[BarPlace]
    """
    horizontal bars go at the bottom of the large tiles
    """

    def __init__(self, floor_things: FrozenSet[Coord]) -> None:
        self.floor_things = floor_things
        self.bars = []

    def add(self, c: Coord, horizontal: bool, length: int) -> None:
        """
        add a barrier if it doesn't cross a sprite placed on the floor
        """
        below = (c[0] + 1, c[1])
        if below in self.floor_things:
            return
        if horizontal and length == 2:
            below_right = (c[0] + 1, c[1] + 1)
            if below_right in self.floor_things:
                return
        self.bars.append(BarPlace(c, horizontal, length))


def barrier_places(g: Grid, floor_things: List[Coord]) -> BarrierPlaces:
    tr = BarrierPlaces(frozenset(floor_things))
    for y, row in enumerate(g.data):
        for x, this_cell in enumerate(row):
            here = (y, x)
            if this_cell == Cell.space and not g.in_exit(y, x):
                if x == LEFT or g.data[y][x - 1] != Cell.space:
                    # (the bottom of this) is a place where a horizontal bar can start
                    if x == RIGHT or g.data[y][x + 1] != Cell.space:
                        tr.add(here, True, 1)
                    else:  # space to the right
                        if not g.in_exit(y, x + 1):
                            if x + 1 == RIGHT or g.data[y][x + 2] != Cell.space:
                                tr.add(here, True, 2)
                            # else would have to be longer than 2, but barrier max length is 2
                        # else moved into an exit
                if (
                    (y == TOP or g.data[y - 1][x] != Cell.space) and
                    # y is even, so no need for check on y + 1 bounds
                    (y < BOTTOM and g.data[y + 1][x] == Cell.floor)
                ):
                    # length 2 vertical bar can be here
                    tr.add(here, False, 2)
            elif this_cell == Cell.floor and not g.in_exit(y, x) and (
                y > TOP and g.data[y - 1][x] != Cell.space
            ):
                # length 1 vertical bar can be here
                tr.add(here, False, 1)
    shuffle(tr.bars)

    # put the places I can't go first in the list, so they're the last to get chosen
    cant_go: List[BarPlace] = []
    can_go: List[BarPlace] = []
    goables = g.get_goables(3)
    for bar in tr.bars:
        y, x = bar.c
        if bar.horizontal:
            while y < BOTTOM and g.data[y][x] != Cell.floor:
                y += 1
        else:  # vertical
            y += bar.length - 1
        if (y, x, False) in goables:
            can_go.append(bar)
        else:
            cant_go.append(bar)
    tr.bars = cant_go + can_go
    return tr
