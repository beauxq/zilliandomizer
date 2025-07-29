from pathlib import Path
import random
import sys
from typing import Set


def test_make() -> None:
    from zilliandomizer.map_gen.base_maker import BaseMaker, Node, red_inputs
    from zilliandomizer.map_gen.door_manager import DoorManager

    possible, existing = red_inputs()
    bm = BaseMaker(5, 3, 5, 5, 0, possible, existing, DoorManager(), None)
    bm.make()
    print(bm.map_str())
    print(bm.path(Node(0, 3), Node(4, 0)))

    print(f"fork distance {bm.fork_altitude(Node(0, 3), (Node(1, 0), Node(3, 0), Node(4, 0)))}")


def test_no_changes() -> None:
    from zilliandomizer.map_gen.base_maker import BaseMaker, red_inputs
    from zilliandomizer.map_gen.door_manager import DoorManager

    possible, existing = red_inputs()
    bm = BaseMaker(5, 3, 5, 5, 0, possible, existing, DoorManager(), None)
    assert bm.no_changes == {(4, 0), (1, 2), (0, 3), (4, 3)}


def test_make_paperclip() -> None:
    from zilliandomizer.map_gen.base_maker import Node, get_paperclip_base
    from zilliandomizer.map_gen.door_manager import DoorManager

    bm = get_paperclip_base(DoorManager(), None)
    print(bm.map_str(1))
    print(bm.path(Node(0, 0), Node(0, 5)))


def test_vanilla_path_rate() -> None:
    from zilliandomizer.map_gen.base_maker import Node, get_paperclip_base
    from zilliandomizer.map_gen.door_manager import DoorManager

    count_vanilla = 0
    for _ in range(1000):
        seed = random.randrange(1999999999)
        # print(f"{seed=}")
        bm = get_paperclip_base(DoorManager(), seed)
        # print(bm.map_str(1, possible_splits))

        path_to_goal = bm.path(Node(0, 0), Node(0, 5))
        if len(path_to_goal) > 10 and path_to_goal[-8] == Node(4, 6) and path_to_goal[-10] == Node(5, 7):
            count_vanilla += 1

    print(f"{count_vanilla=}")
    assert count_vanilla >= 40
    assert count_vanilla <= 400


def test_choose_splits() -> None:
    from zilliandomizer.map_gen.base_maker import Edge, Node, get_paperclip_base
    from zilliandomizer.map_gen.door_manager import DoorManager
    from zilliandomizer.map_gen.split_maker import choose_splits

    start = Node(0, 0)

    seed = random.randrange(1999999999)
    print(f"{seed=}")
    bm = get_paperclip_base(DoorManager(), seed)

    splits = choose_splits(bm, set(), start)

    from pprint import pp
    pp(splits)

    split_edges: Set[Edge] = {
        frozenset(nodes)
        for nodes in splits.items()
    }

    print(bm.map_str(1, splits, split_edges))


if __name__ == "__main__":
    sys.path.append(str((Path(__file__) / ".." / ".." / "src").resolve()))
    test_no_changes()
    test_make()
    test_make_paperclip()
    test_choose_splits()
    test_vanilla_path_rate()
