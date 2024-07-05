from random import Random
from typing import Dict, FrozenSet, Iterable, Iterator, List, NamedTuple, Sequence, Set, Tuple, Union

from zilliandomizer.map_gen.door_manager import DoorManager
from zilliandomizer.utils.disjoint_set import DisjointSet
from zilliandomizer.utils.deterministic_set import DetSet


class Node(NamedTuple):
    y: int
    x: int


Edge = FrozenSet[Node]
""" 2 nodes """
# frozenset because need hashable


def v(y: int, x: int) -> Edge:
    """ down """
    return frozenset((Node(y, x), Node(y + 1, x)))


def h(y: int, x: int) -> Edge:
    """ right """
    return frozenset((Node(y, x), Node(y, x + 1)))


class BaseMaker:
    random: Random
    row_offset: int
    col_offset: int
    height: int
    width: int
    prev_door: int
    possible_edges: DetSet[Edge]
    existing_edges: DetSet[Edge]
    paths: Dict[Node, List[Node]]
    """ destination: path """
    no_changes: Set[Node]
    """ which rooms will have no changes to the entrances and exits """
    door_manager: DoorManager

    def __init__(self,
                 row_offset: int,
                 col_offset: int,
                 height: int,
                 width: int,
                 prev_door: int,
                 possible: Iterable[Edge],
                 existing: Iterable[Edge],
                 door_manager: DoorManager,
                 seed: Union[int, str, None]) -> None:
        """
        `prev_door` is the last door I opened before coming to this section of the base

        existing is where there must be a room transition

        possible is where there can be a room transition (not including existing)
        """
        self.random = Random(seed)
        self.row_offset = row_offset
        self.col_offset = col_offset
        self.height = height
        self.width = width
        self.prev_door = prev_door
        self.possible_edges = DetSet(possible)
        self.existing_edges = DetSet(existing)
        self.paths = {}

        for edge in self.existing_edges:
            assert edge not in self.possible_edges

        self.no_changes = {
            Node(y, x)
            for y in range(height)
            for x in range(width)
            if (
                h(y, x) not in self.possible_edges and
                v(y, x) not in self.possible_edges and
                h(y, x - 1) not in self.possible_edges and
                v(y - 1, x) not in self.possible_edges
            )
        }

        self.door_manager = door_manager

    def map_str(self, stretch_x: int = 1) -> str:
        """ draw the map in ascii art """
        tr = ""
        for y in range(self.height):
            for x in range(self.width):
                room_here = Node(y, x) not in self.no_changes
                tr += "O" if room_here else "-"
                if h(y, x) in self.existing_edges:
                    tr += f"{' ' * stretch_x}-{' ' * stretch_x}"
                else:
                    tr += " " * (1 + stretch_x * 2)
            tr += '\n'
            for x in range(self.width):
                if v(y, x) in self.existing_edges:
                    tr += "| "
                else:
                    tr += "  "
                tr += "  " * stretch_x
            tr += '\n'
        return tr

    def make(self) -> DetSet[Edge]:
        """ returns spanning tree covering this sector """

        components: DisjointSet[Node] = DisjointSet()

        for a, b in self.existing_edges:
            components.union(a, b)

        def crop_possible() -> Iterable[Edge]:
            """ the edges to remove from possible to avoid cycles """
            tr: List[Edge] = []
            for p_edge in self.possible_edges:
                a, b = p_edge
                if components.find(a) == components.find(b):
                    tr.append(p_edge)
            return tr

        while len(self.possible_edges):
            edge = self.random.choice(self.possible_edges)
            self.possible_edges.remove(edge)
            self.existing_edges.add(edge)
            a, b = edge
            components.union(a, b)
            remove = crop_possible()
            for edge in remove:
                self.possible_edges.remove(edge)

        return self.existing_edges

    def adjs(self, node: Node) -> Iterator[Node]:
        y, x = node
        for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            target_y = y + dy
            target_x = x + dx
            if frozenset((Node(y, x), Node(target_y, target_x))) in self.existing_edges:
                yield Node(target_y, target_x)

    def path(self, fro: Node, to: Node) -> Sequence[Node]:
        if to in self.paths and self.paths[to][0] == fro:
            # print("found path in cache")
            return self.paths[to]

        been: Set[Node] = set()
        path_tr = [fro]

        def dfs() -> bool:
            here = path_tr[-1]
            if here == to:
                return True
            if here not in been:
                # print(f"searching {here}")
                been.add(here)
                for adj in self.adjs(here):
                    path_tr.append(adj)
                    if dfs():
                        return True
                    else:
                        path_tr.pop()
            return False

        dfs()

        self.paths[to] = path_tr
        return path_tr

    def fork_altitude(self, start: Node, ends: Sequence[Node]) -> float:
        """
        returns 0 if any end is on the path to another end
        otherwise returns the average distance from the ends to other paths

        ends should be in geographic order (around the outside of the sector)
        """
        total = 0
        count = 0
        for i in range(len(ends) - 1):
            path_1 = self.path(start, ends[i])
            path_2 = self.path(start, ends[i + 1])
            path_set_1 = frozenset(path_1)
            for j, node in enumerate(reversed(path_2)):
                if node in path_set_1:
                    if j == 0:
                        return 0
                    total += j
                    count += 1
                    break
            path_set_2 = frozenset(path_2)
            for j, node in enumerate(reversed(path_1)):
                if node in path_set_2:
                    if j == 0:
                        return 0
                    total += j
                    count += 1
                    break
        return total / count


def red_inputs() -> Tuple[List[Edge], List[Edge]]:
    """
    (in the red section of the map)
    where we can put connections between rooms (not including the places where we must put them),
    and where we must put connections between rooms

    `(possible, existing)`
    """
    possible_edges: List[Edge] = [
        # vertical
        v(0, 0), v(0, 1),                   v(0, 4),
        v(1, 0), v(1, 1),          v(1, 3), v(1, 4),
        v(2, 0), v(2, 1), v(2, 2), v(2, 3), v(2, 4),
                 v(3, 1), v(3, 2),          v(3, 4),  # noqa: E131

        # horizontal
        h(0, 0), h(0, 1),
        h(1, 0),                   h(1, 3),
        h(2, 0), h(2, 1), h(2, 2), h(2, 3),
        h(3, 0), h(3, 1), h(3, 2), h(3, 3),
                 h(4, 1)                     # noqa: E131
    ]

    existing_edges: List[Edge] = [
        h(0, 2), h(0, 3),
        h(1, 1), h(1, 2),
        h(4, 0), h(4, 2), h(4, 3)
    ]

    return possible_edges, existing_edges


def get_red_base(dm: DoorManager, seed: Union[int, str, None]) -> BaseMaker:
    random = Random(seed)
    while True:
        possible, existing = red_inputs()
        bm = BaseMaker(5, 3, 5, 5, 0x25, possible, existing, dm, random.randrange(1999999999))
        bm.make()
        # we don't want the path to one red exit to go past another red exit
        fork_distance = bm.fork_altitude(Node(0, 3), (Node(1, 0), Node(3, 0), Node(4, 0)))
        # we don't want r07c7 to be a dead end, because there are only 4 canisters, so nothing to put behind a door
        r07c7_is_dead_end = len(list(bm.adjs(Node(2, 4)))) < 2
        if fork_distance > 0 and not r07c7_is_dead_end:
            return bm


def paperclip_inputs() -> Tuple[List[Edge], List[Edge]]:
    """
    (in the bottom section of the map)
    where we can put connections between rooms (not including the places where we must put them),
    and where we must put connections between rooms

    `(possible, existing)`
    """

    existing_edges: List[Edge] = [
        # big entrance elevator
        v(0, 0), v(1, 0), v(2, 0), v(3, 0), v(4, 0), v(5, 0),
        # and hallway at bottom
        h(6, 0), v(5, 1),
        # all of the entrances
        # h(4, 0) is a special case, we pretend it doesn't exist for this algorithm
        h(1, 0), h(3, 0), h(5, 1), h(6, 1),
        # bottom right hallway
        h(6, 2), h(6, 3), h(6, 4), h(6, 5), h(6, 6),
        v(5, 7), h(5, 6),
        # end elevator
        v(0, 7), v(1, 7), v(2, 7), v(3, 7),
        # and its hallways
        h(4, 6), h(3, 6), h(0, 6), h(0, 5),
    ]

    possible_edges: List[Edge] = []

    for y in range(6):
        for x in range(1, 6):
            if y == 0 and x > 3:
                # main computer
                continue
            if y == 5 and x == 1:
                # bottom left corner
                continue
            possible_edges.append(h(y, x))

    for y in range(5):
        for x in range(1, 7):
            if y == 0 and x > 4:
                # main computer
                continue
            if y == 4 and x == 1:
                # bottom left corner
                continue
            possible_edges.append(v(y, x))

    # This one won't be possible without split rooms,
    # but I'll put it here to be ready for split rooms anyway.
    possible_edges.append(v(5, 2))

    return possible_edges, existing_edges


def get_paperclip_base(dm: DoorManager, seed: Union[int, str, None]) -> BaseMaker:
    possible, existing = paperclip_inputs()
    bm = BaseMaker(10, 0, 7, 8, 0x31, possible, existing, dm, seed)
    bm.make()
    return bm
