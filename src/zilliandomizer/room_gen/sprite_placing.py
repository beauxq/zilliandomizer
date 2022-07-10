from dataclasses import dataclass
from random import shuffle
from typing import FrozenSet, List
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
    horizontal bars go at the bottom of this place,
    so sensors are in the tiles below
    """
    c: Coord
    hor_len: int
    """ if hor_len is 0, that means it's vertical """


class SensorBarrierPlaces:
    floor_things: FrozenSet[Coord]
    bars: List[BarPlace]
    """
    horizontal bars go at the bottom of these places,
    so sensors are in the tiles below
    """

    def __init__(self, floor_things: FrozenSet[Coord]) -> None:
        self.floor_things = floor_things
        self.bars = []

    def add(self, c: Coord, horizontal_length: int) -> None:
        """
        if horizontal_length is 0, that means it's vertical
        """
        below = (c[0] + 1, c[1])
        if below in self.floor_things:
            return
        if horizontal_length == 2:
            below_right = (c[0] + 1, c[1] + 1)
            if below_right in self.floor_things:
                return
        self.bars.append(BarPlace(c, horizontal_length))


def sensor_barrier_places(g: Grid, floor_things: List[Coord]) -> SensorBarrierPlaces:
    tr = SensorBarrierPlaces(frozenset(floor_things))
    for y, row in enumerate(g.data):
        for x, this_cell in enumerate(row):
            if this_cell == Cell.space and not g.in_exit(y, x):
                here = (y, x)
                if x == LEFT or g.data[y][x - 1] != Cell.space:
                    # (the bottom of this) is a place where a horizontal bar can start
                    if x == RIGHT or g.data[y][x + 1] != Cell.space:
                        tr.add(here, 1)
                    else:  # space to the right
                        if not g.in_exit(y, x + 1):
                            if x + 1 == RIGHT or g.data[y][x + 2] != Cell.space:
                                tr.add(here, 2)
                            else:
                                # could put a longer than 2 sensor here, but barrier max length is 2
                                pass
                        else:
                            # moved into an exit, so we don't want bar here
                            pass
                elif (
                    # The even restriction is because: in red rooms, there is no tile
                    # for a vertical alarm line through an odd row tile unless it's on the floor
                    # TODO: ignore alarm line restrictions here and use different algorithm for alarm lines
                    (y & 1 == 0) and
                    (y == TOP or g.data[y - 1][x] != Cell.space) and
                    # y is even, so no need for check on y + 1 bounds
                    g.data[y + 1][x] == Cell.floor
                ):
                    # vertical bar can be here
                    tr.add(here, 0)
    shuffle(tr.bars)
    return tr
