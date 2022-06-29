from copy import deepcopy
import random
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple, Union
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

    def _can_arrive(self, target_end: Coord, start: Coord, highest_jump: int, standing: bool = True) -> bool:

        def dfs(target_end: Coord, row: int, col: int, standing: bool, been: Set[Tuple[int, int, bool]]) -> bool:
            # self.print((((row, col), True),))
            # input()
            if row == target_end[0] and col == target_end[1]:
                return True
            if (row, col, standing) in been:
                return False
            been_here = been.copy()
            been_here.add((row, col, standing))

            if not standing:
                # check standing
                if self.data[row - 1][col] == Cell.space:
                    if dfs(target_end, row, col, True, been_here):
                        return True

                if col > LEFT and self.data[row][col - 1] == Cell.floor:
                    if dfs(target_end, row, col - 1, standing, been_here):
                        return True
                if col < RIGHT and self.data[row][col + 1] == Cell.floor:
                    if dfs(target_end, row, col + 1, standing, been_here):
                        return True
            else:  # standing
                # check not standing
                if dfs(target_end, row, col, False, been_here):
                    return True

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
                    if dfs(target_end, row - 2, col, True, been_here):
                        return True
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
                    if dfs(target_end, row - 3, col, True, been_here):
                        return True

                # check jump and move left or right
                for jump_height in range(1, highest_jump + 1):  # grid spaces, not jump levels
                    if all(row > j and self.data[row - (j+1)][col] == Cell.space
                            for j in range(1, jump_height + 1)):
                        if col > LEFT and \
                                self.data[row - (jump_height + 1)][col - 1] == Cell.space and \
                                self.data[row - jump_height][col - 1] == Cell.floor:
                            if dfs(target_end, row - jump_height, col - 1, True, been_here):
                                return True
                        if col < RIGHT and \
                                self.data[row - (jump_height + 1)][col + 1] == Cell.space and \
                                self.data[row - jump_height][col + 1] == Cell.floor:
                            if dfs(target_end, row - jump_height, col + 1, True, been_here):
                                return True
                        if col > 1 and \
                                self.data[row - (jump_height + 1)][col - 1] == Cell.space and \
                                self.data[row - jump_height][col - 1] == Cell.space and \
                                self.data[row - (jump_height + 1)][col - 2] == Cell.space and \
                                self.data[row - jump_height][col - 2] == Cell.floor:
                            if dfs(target_end, row - jump_height, col - 2, True, been_here):
                                return True
                        if col < 12 and \
                                self.data[row - (jump_height + 1)][col + 1] == Cell.space and \
                                self.data[row - jump_height][col + 1] == Cell.space and \
                                self.data[row - (jump_height + 1)][col + 2] == Cell.space and \
                                self.data[row - jump_height][col + 2] == Cell.floor:
                            if dfs(target_end, row - jump_height, col + 2, True, been_here):
                                return True

                for dir in (-1, 1):
                    # check move
                    next_col = col + dir
                    if next_col >= LEFT and next_col <= RIGHT and \
                            self.data[row - 1][next_col] == Cell.space:
                        if self.data[row][next_col] == Cell.floor:
                            if dfs(target_end, row, next_col, True, been_here):
                                return True
                        # or jump
                        next_next_col = next_col + dir
                        if next_next_col >= LEFT and next_next_col <= RIGHT and \
                                self.data[row][next_col] == Cell.space and \
                                self.data[row - 1][next_next_col] == Cell.space and \
                                self.data[row][next_next_col] == Cell.floor:
                            if dfs(target_end, row, next_next_col, True, been_here):
                                return True
                        nnn_col = next_next_col + dir
                        if nnn_col >= LEFT and nnn_col <= RIGHT and \
                                self.data[row][next_col] == Cell.space and \
                                self.data[row - 1][next_next_col] == Cell.space and \
                                self.data[row][next_next_col] == Cell.space and \
                                self.data[row - 1][nnn_col] == Cell.space and \
                                self.data[row][nnn_col] == Cell.floor:
                            if dfs(target_end, row, nnn_col, True, been_here):
                                return True
                        # or fall
                        if self.data[row][next_col] == Cell.space:
                            target_row = row
                            while self.data[target_row][next_col] == Cell.space:
                                target_row += 1
                            if dfs(target_end, target_row, next_col, True, been_here):
                                return True

            return False

        return dfs(target_end, start[0], start[1], standing, set())

    def solve(self, highest_jump: int) -> bool:
        """
        returns whether I can traverse from every end to every other end

        highest_jump is number of grid blocks, not jump level
        """
        start = self.ends[0]
        all_ends = True
        for end in self.ends[1:]:
            all_ends = all_ends and self._can_arrive(end, start, highest_jump, True)
            all_ends = all_ends and self._can_arrive(start, end, highest_jump, True)
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

    def get_goables(self, jump_blocks: int, standing_only: bool) -> List[Tuple[Coord, bool]]:
        """ coordinates can go to (and whether I can stand there) """
        tr: List[Tuple[Coord, bool]] = []
        start = self.ends[0]
        for y, row in enumerate(self.data):
            for x, col in enumerate(row):
                if col == Cell.floor:
                    here = (y, x)
                    if self._can_arrive(here, start, jump_blocks) and \
                            self._can_arrive(start, here, jump_blocks, False):
                        can_stand = self.data[y - 1][x] == Cell.space
                        if can_stand or not standing_only:
                            tr.append((here, can_stand))
        return tr

    def copy(self) -> "Grid":
        tr = Grid(self.ends, self._logger)
        tr.data = deepcopy(self.data)
        return tr

    def fix_crawl_fall(self, jump_blocks: int = 3) -> None:
        """ eliminate softlocks from crawling into falling holes """
        base_goables = self.get_goables(jump_blocks, True)
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
                                new_goables = self.get_goables(jump_blocks, True)
                                if new_goables != base_goables:
                                    # restore
                                    for y_r, x_r in to_restore:
                                        value = to_restore[y_r, x_r]
                                        self.data[y_r][x_r] = value
                                else:
                                    # debug
                                    self._logger.debug(
                                        f"eliminated crawl fall at row {y}, col {target_col}"
                                    )

    def optimize_encoding(self, jump_blocks: int = 3) -> None:
        """ try to save space in run-length encoding """
        base_goables = self.get_goables(jump_blocks, False)

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
            new_goables = self.get_goables(jump_blocks, False)
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
        for y in range(1, 6):
            for x in range(14):
                here = (y, x)
                if self._can_arrive(here, self.ends[0], jump_blocks) and \
                        not self._can_arrive(self.ends[0], here, jump_blocks, False):
                    print(f"softlock at row {y} col {x}")
                    return True
        return False
