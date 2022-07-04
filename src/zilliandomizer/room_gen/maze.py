from collections import deque
from copy import deepcopy
import random
from typing import Dict, FrozenSet, Iterable, Iterator, List, Optional, Set, Tuple, Union
from zilliandomizer.logger import Logger
from zilliandomizer.room_gen.common import Coord

LEFT = 0
RIGHT = 13
TOP = 0
BOTTOM = 5


class Cell:
    wall = '|'
    floor = '_'
    space = ' '


class MakeFailure(Exception):
    pass


class Grid:
    data: List[List[str]]
    ends: List[Coord]
    """ coords of lower left """
    _logger: Logger

    def __init__(self, ends: List[Coord], logger: Logger) -> None:
        self.ends = ends
        self._logger = logger
        self.reset()

    def reset(self) -> None:
        self.data = [[Cell.wall for _ in range(14)] for _ in range(6)]

        for end in self.ends:
            row, col = end
            self.data[row][col] = Cell.floor
            self.data[row][col + 1] = Cell.floor
            self.data[row - 1][col] = Cell.space
            self.data[row - 1][col + 1] = Cell.space

    def _adj_moves(self, state: Tuple[int, int, bool], highest_jump: int) -> Iterator[Tuple[int, int, bool]]:
        """
        yield all the places I can move in one step

        state is (row, col, standing)
        """

        row, col, standing = state

        if not standing:
            # can change to standing
            if self.data[row - 1][col] == Cell.space:
                yield row, col, True

            if col > LEFT and self.data[row][col - 1] == Cell.floor:
                yield row, col - 1, standing
            if col < RIGHT and self.data[row][col + 1] == Cell.floor:
                yield row, col + 1, standing
        else:  # standing
            # can change to not standing
            yield row, col, False

            # jump around ledge
            # TODO: don't jump around ledges at low skill levels
            left_col = col - 1
            right_col = col + 1
            if highest_jump >= 2 and row > 2 and \
                    self.data[row - 2][col] == Cell.floor and \
                    self.data[row - 3][col] == Cell.space and ((
                        left_col >= LEFT and
                        self.data[row][left_col] == Cell.space and
                        self.data[row - 1][left_col] == Cell.space and
                        self.data[row - 2][left_col] == Cell.space and
                        self.data[row - 3][left_col] == Cell.space
                    ) or (
                        right_col <= RIGHT and
                        self.data[row][right_col] == Cell.space and
                        self.data[row - 1][right_col] == Cell.space and
                        self.data[row - 2][right_col] == Cell.space and
                        self.data[row - 3][right_col] == Cell.space
                    )):
                yield row - 2, col, True
            if highest_jump >= 3 and row > 3 and \
                    self.data[row - 3][col] == Cell.floor and \
                    self.data[row - 4][col] == Cell.space and ((
                        left_col >= LEFT and
                        self.data[row][left_col] == Cell.space and
                        self.data[row - 1][left_col] == Cell.space and
                        self.data[row - 2][left_col] == Cell.space and
                        self.data[row - 3][left_col] == Cell.space and
                        self.data[row - 4][left_col] == Cell.space
                    ) or (
                        right_col <= RIGHT and
                        self.data[row][right_col] == Cell.space and
                        self.data[row - 1][right_col] == Cell.space and
                        self.data[row - 2][right_col] == Cell.space and
                        self.data[row - 3][right_col] == Cell.space and
                        self.data[row - 4][right_col] == Cell.space
                    )):
                yield row - 3, col, True

            # check jump and move left or right
            for jump_height in range(1, highest_jump + 1):  # grid spaces, not jump levels
                if all(row > j and self.data[row - (j+1)][col] == Cell.space
                       for j in range(1, jump_height + 1)):
                    if col > LEFT and \
                            self.data[row - (jump_height + 1)][col - 1] == Cell.space and \
                            self.data[row - jump_height][col - 1] == Cell.floor:
                        yield row - jump_height, col - 1, True
                    if col < RIGHT and \
                            self.data[row - (jump_height + 1)][col + 1] == Cell.space and \
                            self.data[row - jump_height][col + 1] == Cell.floor:
                        yield row - jump_height, col + 1, True
                    if col > 1 and \
                            self.data[row - (jump_height + 1)][col - 1] == Cell.space and \
                            self.data[row - jump_height][col - 1] == Cell.space and \
                            self.data[row - (jump_height + 1)][col - 2] == Cell.space and \
                            self.data[row - jump_height][col - 2] == Cell.floor:
                        yield row - jump_height, col - 2, True
                    if col < 12 and \
                            self.data[row - (jump_height + 1)][col + 1] == Cell.space and \
                            self.data[row - jump_height][col + 1] == Cell.space and \
                            self.data[row - (jump_height + 1)][col + 2] == Cell.space and \
                            self.data[row - jump_height][col + 2] == Cell.floor:
                        yield row - jump_height, col + 2, True

            for dir in (-1, 1):
                # check move
                next_col = col + dir
                if next_col >= LEFT and next_col <= RIGHT and \
                        self.data[row - 1][next_col] == Cell.space:
                    if self.data[row][next_col] == Cell.floor:
                        yield row, next_col, True
                    # horizontal jump over gap of 1
                    next_next_col = next_col + dir
                    if next_next_col >= LEFT and next_next_col <= RIGHT and \
                            self.data[row][next_col] == Cell.space and \
                            self.data[row - 1][next_next_col] == Cell.space and \
                            self.data[row][next_next_col] == Cell.floor:
                        yield row, next_next_col, True
                    # horizontal jump over gap of 2
                    nnn_col = next_next_col + dir
                    if nnn_col >= LEFT and nnn_col <= RIGHT and \
                            self.data[row][next_col] == Cell.space and \
                            self.data[row - 1][next_next_col] == Cell.space and \
                            self.data[row][next_next_col] == Cell.space and \
                            self.data[row - 1][nnn_col] == Cell.space and \
                            self.data[row][nnn_col] == Cell.floor:
                        yield row, nnn_col, True
                    # or fall
                    if self.data[row][next_col] == Cell.space:
                        target_row = row
                        while self.data[target_row][next_col] == Cell.space:
                            target_row += 1
                        yield target_row, next_col, True

    def _search(self,
                start: Coord,
                highest_jump: int,
                standing: bool = True,
                target_end: Optional[Tuple[int, int, bool]] = None) -> Set[Tuple[int, int, bool]]:
        """
        returns the set of all (row, col, standing) where I can go

        stops search early if target_end (y, x, standing) is found
        """
        row, col = start
        been: Set[Tuple[int, int, bool]] = set()
        to_move_from = deque([(row, col, standing)])
        while len(to_move_from):
            here = to_move_from.pop()
            if here not in been:
                been.add(here)
                if here == target_end:
                    return been
                for adj in self._adj_moves(here, highest_jump):
                    to_move_from.append(adj)
        return been

    def solve(self, highest_jump: int) -> bool:
        """
        returns whether I can traverse from every end to every other end

        highest_jump is number of grid blocks, not jump level
        """
        if len(self.ends) == 2:
            # can stop search early if only 1 other end to look for
            a, b = self.ends
            a_state = (a[0], a[1], True)
            b_state = (b[0], b[1], True)
            return a_state in self._search(b, highest_jump, True, a_state) \
                and b_state in self._search(a, highest_jump, True, b_state)

        start = self.ends[0]
        start_state = (start[0], start[1], True)
        start_goables = self._search(start, highest_jump)
        all_ends = True
        for end in self.ends[1:]:
            all_ends = all_ends and ((end[0], end[1], True) in start_goables)
            all_ends = all_ends and (start_state in self._search(
                end, highest_jump, True, start_state
            ))
        return all_ends

    def map_str(self, marks: Union[None, Iterable[Coord]] = None) -> str:
        if not marks:
            marks = frozenset()
        coord_marks: FrozenSet[Coord] = frozenset(marks)
        under = "̲"  # unicode underline prev char
        tr = " "
        for y, row in enumerate(self.data):
            for x, col in enumerate(row):
                here = (y, x)
                if here in coord_marks:
                    if col == Cell.floor:
                        tr += under
                    tr += '*'
                else:
                    tr += col
            tr += '\n '
        return tr

    def in_exit(self, row: int, col: int) -> bool:
        """ this coordinate is in an exit area """
        if (row, col) in self.ends:
            return True
        if (row, col - 1) in self.ends:
            return True
        if (row + 1, col) in self.ends:
            return True
        return (row + 1, col - 1) in self.ends

    def sparsify(self) -> bool:
        clearables: List[Coord] = []

        def is_clearable(row: int, col: int) -> bool:
            if self.in_exit(row, col):
                return False

            here = self.data[row][col]
            if here == Cell.wall:
                return True
            if here == Cell.floor:
                return row < 5 and self.data[row + 1][col] != Cell.wall
            return False

        for row in range(6):
            for col in range(14):
                if is_clearable(row, col):
                    clearables.append((row, col))
        if len(clearables) == 0:
            return False
        row, col = random.choice(clearables)
        current = self.data[row][col]
        if current == Cell.floor:
            self.data[row][col] = Cell.space
            return True
        # else removing wall
        if row == 5 or self.data[row + 1][col] == Cell.wall:
            self.data[row][col] = Cell.floor
        else:
            self.data[row][col] = random.choice((Cell.space, Cell.floor))
        return True

    def make(self, jump_blocks: int) -> None:
        while not self.solve(jump_blocks):
            if not self.sparsify():
                raise MakeFailure("make terrain failed")

    def get_goables(self, jump_blocks: int) -> Set[Tuple[int, int, bool]]:
        """ coordinates can go to, and whether I can stand there """
        return self._search(self.ends[0], jump_blocks)

    def get_standing_goables(self, jump_blocks: int) -> List[Tuple[int, int, bool]]:
        return [
            goable
            for goable in self.get_goables(jump_blocks)
            if goable[2]
        ]

    def copy(self) -> "Grid":
        tr = Grid(self.ends, self._logger)
        tr.data = deepcopy(self.data)
        return tr

    def fix_crawl_fall(self, jump_blocks: int = 3) -> None:
        """ eliminate softlocks from crawling into falling holes """
        base_goables = self.get_standing_goables(jump_blocks)
        for y, row in enumerate(self.data):
            if y > 0:
                for x, col in enumerate(row):
                    for dir in (-1, 1):
                        target_col = x + dir
                        if target_col >= LEFT and target_col <= RIGHT:
                            if (
                                col == Cell.floor and
                                self.data[y][target_col] == Cell.space and (
                                    self.data[y - 1][target_col] != Cell.space or
                                    self.data[y - 1][x] != Cell.space
                                )
                            ):
                                if self.data[y - 1][x] != Cell.space:
                                    target_col = x
                                to_restore: Dict[Coord, str] = {}
                                to_restore[y, target_col] = self.data[y][target_col]
                                self.data[y][target_col] = Cell.wall
                                if self.data[y - 1][target_col] == Cell.space:
                                    to_restore[y - 1, target_col] = self.data[y - 1][target_col]
                                    self.data[y - 1][target_col] = Cell.floor
                                new_goables = self.get_standing_goables(jump_blocks)
                                if new_goables != base_goables:
                                    # restore
                                    for y_r, x_r in to_restore:
                                        value = to_restore[y_r, x_r]
                                        self.data[y_r][x_r] = value
                                # else:
                                #     # debug
                                #     self._logger.debug(
                                #         f"eliminated crawl fall at row {y}, col {target_col}"
                                #     )

    def optimize_encoding(self, jump_blocks: int = 3) -> None:
        """ try to save space in run-length encoding """
        base_goables = self.get_goables(jump_blocks)

        def try_change(y: int, x: int, value: str) -> bool:
            """ returns whether change was good """
            if value == Cell.space and y < BOTTOM and self.data[y + 1][x] == Cell.wall:
                # space above wall not allowed
                return False
            saved = self.data[y][x]
            self.data[y][x] = value
            above_saved: Optional[str] = None
            if value == Cell.wall and y > 0 and self.data[y - 1][x] == Cell.space:
                above_saved = self.data[y - 1][x]
                self.data[y - 1][x] = Cell.floor
            new_goables = self.get_goables(jump_blocks)
            if new_goables != base_goables:
                self.data[y][x] = saved
                if above_saved:
                    self.data[y - 1][x] = above_saved
                return False
            return True

        for y, row in enumerate(self.data):
            for x, col in enumerate(row):
                left = self.data[y][x - 1] if x > LEFT else Cell.wall
                right = self.data[y][x + 1] if x < RIGHT else Cell.wall
                if col != left and col != right:
                    if left == right:
                        try_change(y, x, left)
                    # I'm worried that this will bring back crawl fall softlocks
                    # after I get rid of them
                    # else:  # something different on each side
                    #     first, second = (left, right) if random.random() < 0.5 else (right, left)
                    #     if first != Cell.wall:
                    #         first, second = second, first
                    #     if not try_change(y, x, first):
                    #         try_change(y, x, second)
                # else col same as one of its neighbors
            # done with row
        # done with data
        # TODO: another pass on the top row? (often ends up with small useless platforms)

    def softlock_exists(self, jump_blocks: int) -> bool:
        start = self.ends[0]
        start_state = (start[0], start[1], True)
        start_goables = self._search(start, jump_blocks)
        for y, x, standing in start_goables:
            here = (y, x)
            here_goables = self._search(here, jump_blocks, standing, start_state)
            if start_state not in here_goables:
                self._logger.debug(f"softlock at row {y} col {x}")
                self._logger.debug(self.map_str())
                return True
        return False
