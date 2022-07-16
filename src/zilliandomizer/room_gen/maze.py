from collections import deque
from copy import deepcopy
import random
from typing import Dict, FrozenSet, Iterable, Iterator, List, Optional, Set, Tuple, Union
from zilliandomizer.logger import Logger
from zilliandomizer.low_resources.terrain_tiles import Tile
from zilliandomizer.room_gen.common import Coord
from zilliandomizer.terrain_compressor import TerrainCompressor

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
    exits: List[Coord]
    """ places I enter and exit room - coords of lower left """
    ends: List[Coord]
    """ superset of exits, places I want to be able to get to - coords of lower left """
    _tc: TerrainCompressor
    _logger: Logger
    _skill: int
    """ skill from options """

    def __init__(self,
                 exits: List[Coord],
                 ends: List[Coord],
                 tc: TerrainCompressor,
                 logger: Logger,
                 skill: int) -> None:
        self.exits = exits
        self.ends = ends
        self._tc = tc
        """ doesn't modify any terrain - this is just to read terrain data (to know where walls are) """
        self._logger = logger
        self._skill = skill
        self.reset()

    def reset(self) -> None:
        self.data = [[Cell.wall for _ in range(14)] for _ in range(6)]

        for end in self.ends:
            row, col = end
            self.data[row][col] = Cell.floor
            self.data[row][col + 1] = Cell.floor
            self.data[row - 1][col] = Cell.space
            self.data[row - 1][col + 1] = Cell.space

    def side_of_jump_around(self, row: int, col: int, dir: int, jump: int) -> bool:
        """ Is there terrain to the side that I can do a jump around ledge through? """
        next_col = col + dir

        if not (
            next_col >= LEFT and next_col <= RIGHT and
            all(
                self.data[row - i][next_col] == Cell.space
                for i in range(jump + 2)
            )
        ):
            return False

        next_next_col = next_col + dir

        if next_next_col < LEFT or next_next_col > RIGHT:
            return True

        # what I'm trying to deal with here
        # _  |  _  |     |     |     |     |
        #   _|    _|  _ _|  _ _|  _ _|  _ _|
        #    |     |     |     |  _ _|    _|
        #   _|     |    _|     |     |     |
        #    |    _|     |    _|    _|    _|
        # ___|  ___|  ___|  ___|  ___|  ___|
        # some are difficult, some are impossible

        # find out what row above me is solid
        head_hit = row - 2
        while head_hit >= 0 and self.data[head_hit][col] == Cell.space:
            head_hit -= 1

        if self.data[head_hit + 1][next_next_col] != Cell.space:
            # This solid block helps me get in the slot
            return True
        # else there is a space 1 below head hit
        if self.data[head_hit][next_next_col] != Cell.space:
            # I have to jump into a slot.
            return self._skill > 3
        # else space at head hit level also
        if self.data[head_hit - 1][next_next_col] != Cell.space:
            # I think this jump is impossible
            return False
        # else space all the way up to top of where I'm jumping
        return True

    def _adj_moves(self,
                   state: Tuple[int, int, bool],
                   highest_jump: int) -> Iterator[Tuple[int, int, bool]]:
        """
        yield all the places I can move in one step

        state is (row, col, standing)
        """

        row, col, standing = state

        if not standing:
            # can change to standing
            if self.data[row - 1][col] == Cell.space:
                yield row, col, True

            # move left or right crawling
            for dir in (-1, 1):
                target_col = col + dir
                if target_col >= LEFT and target_col <= RIGHT:
                    tile = self.data[row][target_col]
                    if tile == Cell.floor:
                        yield row, target_col, False
                    elif tile == Cell.space:
                        # fall
                        target_row = row + 1
                        while self.data[target_row][target_col] == Cell.space:
                            target_row += 1
                        yield target_row, target_col, True
        else:  # standing
            # can change to not standing
            yield row, col, False

            # jump around ledge
            if self._skill > 1:  # don't jump around ledges at low skill levels
                if highest_jump >= 2 and row > 2 and \
                        self.data[row - 2][col] == Cell.floor and \
                        self.data[row - 3][col] == Cell.space and (
                            self.side_of_jump_around(row, col, -1, 2) or
                            self.side_of_jump_around(row, col, 1, 2)
                        ):
                    yield row - 2, col, True
                if highest_jump >= 3 and row > 3 and \
                        self.data[row - 3][col] == Cell.floor and \
                        self.data[row - 4][col] == Cell.space and (
                            self.side_of_jump_around(row, col, -1, 3) or
                            self.side_of_jump_around(row, col, 1, 3)
                        ):
                    yield row - 3, col, True

            # check jump and move left or right
            for jump_height in range(1, highest_jump + 1):  # grid spaces, not jump levels
                target_row = row - jump_height
                if target_row < 1:
                    continue
                for dir in (-1, 1):
                    # some jump distances would require looking at more ceiling
                    # distance 5 example:
                    #     ___|
                    #        |
                    #      __|
                    # _      |
                    #        |
                    # _______|
                    # Champ room escape is distance 5, but with ceiling over all

                    # conclusion after below research:
                    #  - don't need to worry about partial ceilings if skill is high
                    #     - can release jump button early to not bonk

                    # new discovery after that conclusion:
                    # - height 1 distance 6 partial ceiling with jump 2 is possible
                    #    - It may have been a frame-perfect jump button release that I did.

                    # with no ceiling, jump 1 (2 blocks) can get distance 5 at height 1
                    #  - maybe barely distance 6 (didn't find a test for 6)
                    #  - with partial ceiling at distance 4, is possible, but difficult
                    #     - requires skill (> 4?) (release jump button early to not bonk)
                    # with ceiling, jump 1 (2 blocks) can get distance 4 at height 1
                    #  - distance 5 possible but difficult (release jump button early to not bonk)
                    #  - looks like partial ceiling probably doesn't matter for dist 4 (didn't find a test)
                    #     - can bonk head at distance 3 with a little difficulty (more often bonk at 2)
                    # jump 1 can barely get height 2 distance 5 (skill > 1?)

                    # jump 2 can barely get height 2 distance 6
                    # Champ escape (h 1 d 5 w/ ceiling) is easier with jump 2 than jump 1
                    #  - can hold jump button
                    # jump 2 cannot get h 1 d 6 with ceiling

                    # jump 3
                    # h 3 d 6 is easy
                    # looks like I can't do h 2 d 7 with ceiling
                    # h 2 d 6 w ceiling not hard (maybe skill > 0)

                    # include distance 4 and 5 only if skill is high
                    for distance in range(1, 6 if self._skill > 4 else 4):
                        target_col = col + distance * dir
                        if target_col < LEFT or target_col > RIGHT:
                            continue
                        start_of_needing_space = (
                            min(col + dir, target_col - dir)
                            if dir == 1
                            else max(col + dir, target_col - dir)
                        )
                        # require skill to jump with horizontal movement into a 1-tile hole
                        if self._skill < 4:
                            if target_col == col + 2 * dir:
                                start_of_needing_space = col
                        # check all space before target
                        if all(
                            all(
                                self.data[y][col_i] == Cell.space
                                for col_i in range(start_of_needing_space, target_col, dir)
                            )
                            for y in range(target_row - 1, row)
                        ) and (
                            # and landing
                            self.data[target_row][target_col] == Cell.floor
                            and self.data[target_row - 1][target_col] == Cell.space
                        ):
                            yield target_row, target_col, True

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
                    # horizontal jump over gap of 3
                    # this is only used on top row
                    # because it requires jump 3 for the speed
                    # and if it's not on the top row, I can use jump 3 to jump up from below
                    # TODO: except if there's no ceiling to bonk, then it's easy with jump 1
                    # TODO: and with ceiling, it's barely possible with jump 2 (same as jump 3?)
                    if row == 1 and highest_jump == 3 and self._skill > 4:
                        nnnn_col = nnn_col + dir
                        if nnnn_col >= LEFT and nnnn_col <= RIGHT and \
                                self.data[1][next_col] == Cell.space and \
                                self.data[0][next_next_col] == Cell.space and \
                                self.data[1][next_next_col] == Cell.space and \
                                self.data[0][nnn_col] == Cell.space and \
                                self.data[1][nnn_col] == Cell.space and \
                                self.data[0][nnnn_col] == Cell.space and \
                                self.data[1][nnnn_col] == Cell.floor:
                            yield row, nnnn_col, True
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
                # print(self.map_str([(here[0], here[1])]))
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
        if (row, col) in self.exits:
            return True
        if (row, col - 1) in self.exits:
            return True
        if (row + 1, col) in self.exits:
            return True
        return (row + 1, col - 1) in self.exits

    def in_end(self, row: int, col: int) -> bool:
        """ this coordinate is in an end area """
        if (row, col) in self.ends:
            return True
        if (row, col - 1) in self.ends:
            return True
        if (row + 1, col) in self.ends:
            return True
        return (row + 1, col - 1) in self.ends

    def sparsify(self) -> bool:
        """
        make more space for the character to move around in the room

        returns whether a change was made
        """
        clearables: List[Coord] = []

        def is_clearable(row: int, col: int) -> bool:
            if self.in_end(row, col):
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

    def shortify(self) -> bool:
        """
        make the room more compressible, so it takes fewer bytes in the rom

        return whether a change was made
        """
        changeables: List[Tuple[int, int, List[str]]] = []

        def is_changeable(row: int, col: int) -> List[str]:
            """ returns what it can change to """
            tr: List[str] = []
            if self.in_end(row, col):
                return tr

            here = self.data[row][col]
            left = self.data[row][col - 1] if col > LEFT else Cell.wall
            right = self.data[row][col + 1] if col < RIGHT else Cell.wall

            if here == left or here == right:
                # we benefit from changing this, only if
                # we can change to a floor without losing space
                # and we can benefit from changing below to a wall
                if here != Cell.floor and (
                    left == Cell.floor or
                    right == Cell.floor
                ) and row < BOTTOM:
                    # we can change to a floor without losing space
                    # and not on bottom row
                    below = self.data[row + 1][col]
                    below_left = self.data[row + 1][col - 1] if col > LEFT else Cell.wall
                    below_right = self.data[row + 1][col + 1] if col < RIGHT else Cell.wall
                    if below == below_left or below == below_right or Cell.wall not in (below_left, below_right):
                        # no benefit from changing below to a wall
                        return tr
                    else:  # would benefit from changing below to wall
                        return [Cell.floor]
                else:  # either bottom row or can't change to floor without losing space
                    return tr
            else:  # here is different from both left and right
                if left == right:
                    if left == Cell.wall:
                        if row == TOP or self.data[row - 1][col] != Cell.space:
                            return [left]
                        else:  # can't turn this to wall because space above it
                            return tr
                    elif left == Cell.space:
                        if row == BOTTOM or self.data[row + 1][col] != Cell.wall:
                            return [left]
                        else:  # can't turn this to space because wall below it
                            return tr
                    else:  # floor on both sides
                        return [left]
                else:  # left and right different
                    if left == Cell.wall:
                        if row == TOP or self.data[row - 1][col] != Cell.space:
                            tr.append(left)
                    elif left == Cell.space:
                        if row == BOTTOM or self.data[row + 1][col] != Cell.wall:
                            tr.append(left)
                    else:  # floor on left
                        tr.append(left)

                    if right == Cell.wall:
                        if row == TOP or self.data[row - 1][col] != Cell.space:
                            tr.append(right)
                    elif right == Cell.space:
                        if row == BOTTOM or self.data[row + 1][col] != Cell.wall:
                            tr.append(right)
                    else:  # floor on left
                        tr.append(right)
                    return tr

        for row in range(6):
            for col in range(14):
                changeable = is_changeable(row, col)
                if len(changeable):
                    changeables.append((row, col, changeable))
        if len(changeables) == 0:
            return False
        row, col, change_to = random.choice(changeables)
        self.data[row][col] = random.choice(change_to)
        return True

    def make(self, jump_blocks: int, size_limit: float) -> None:
        """
        produce a room that is traversable from each end to every other end
        <= size_limit bytes

        does not optimize or check for softlocks
        """
        success = False
        count = 0
        while count < 500 and not success:
            count += 1
            solved = self.solve(jump_blocks)
            if solved:
                # using a red room because red might be most restrictive?
                # otherwise doesn't matter which room
                data = self.to_room_data(0x31)
                if len(data) <= size_limit:
                    success = True
                else:
                    if self.shortify() or self.sparsify():
                        success = False  # need to check again
                    else:  # unable to find any changes
                        raise MakeFailure("make terrain failed")
            else:  # not able to traverse yet
                if self.sparsify() or self.shortify():
                    success = False  # check again
                else:  # unable to find any changes
                    raise MakeFailure("make terrain failed")
        if not success:
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
        tr = Grid(self.exits, self.ends, self._tc, self._logger, self._skill)
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

    def to_room_data(self, map_index: int) -> List[int]:
        """ to compressed """
        if map_index < 0x28:  # blue
            wall = Tile.b_walls
            floor_even = Tile.b_floor
            floor_odd = floor_even
            space_even = Tile.b_space
            space_odd = space_even
            ceiling_even = Tile.b_ceiling
            ceiling_odd = ceiling_even
            floor_ceiling_even = Tile.b_floor_ceiling
            floor_ceiling_odd = floor_ceiling_even
        elif map_index < 0x50:  # red
            wall = Tile.r_walls
            floor_even = Tile.r_light_floor
            floor_odd = Tile.r_dark_floor
            space_even = Tile.r_light_space
            space_odd = Tile.r_dark_space
            ceiling_even = Tile.r_light_ceiling
            ceiling_odd = Tile.r_dark_ceiling
            floor_ceiling_even = Tile.r_light_floor_ceiling
            floor_ceiling_odd = Tile.r_dark_floor_ceiling
        else:  # paperclip
            wall = Tile.p_walls
            floor_even = Tile.p_floor
            floor_odd = floor_even
            space_even = Tile.p_space
            space_odd = space_even
            ceiling_even = Tile.p_ceiling
            ceiling_odd = ceiling_even
            floor_ceiling_even = Tile.p_floor_ceiling
            floor_ceiling_odd = floor_ceiling_even

        original_data = TerrainCompressor.decompress(self._tc.get_room(map_index))

        tr: List[int] = []
        for row in range(len(self.data)):

            # left wall
            tr.append(original_data[len(tr)])

            for col in range(len(self.data[0])):
                if self.data[row][col] == Cell.wall:
                    tr.append(wall)
                else:  # not wall here
                    ceiling_here = (row == 0) or (self.data[row - 1][col] != Cell.space)
                    if not ceiling_here:
                        if self.data[row][col] == Cell.space:
                            tr.append(space_odd if (row & 1) else space_even)
                        else:  # floor with no ceiling
                            tr.append(floor_odd if (row & 1) else floor_even)
                    else:  # floor or space with ceiling above
                        if self.data[row][col] == Cell.space:
                            tr.append(ceiling_odd if (row & 1) else ceiling_even)
                        else:  # floor with no ceiling
                            tr.append(floor_ceiling_odd if (row & 1) else floor_ceiling_even)

            # right wall
            tr.append(original_data[len(tr)])

        return TerrainCompressor.compress(tr)
