from pathlib import Path
import sys


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


def test_something_else() -> None:
    from zilliandomizer.map_gen.base_maker import BaseMaker, Edge, h, v
    from zilliandomizer.map_gen.door_manager import DoorManager

    height = 2
    width = 2

    possible: list[Edge] = []
    for y in range(height):
        for x in range(width):
            if y < height - 1:
                possible.append(v(y, x))
            if x < width - 1:
                possible.append(h(y, x))

    bm = BaseMaker(0, 0, height, width, 0, possible, [], DoorManager(), None)
    bm.make()
    print(bm.map_str(2))


def test_make_paperclip() -> None:
    from zilliandomizer.map_gen.base_maker import Node, get_paperclip_base
    from zilliandomizer.map_gen.door_manager import DoorManager

    bm = get_paperclip_base(DoorManager(), None)
    bm.make()
    print(bm.map_str(1))
    print(bm.path(Node(0, 0), Node(0, 5)))


if __name__ == "__main__":
    sys.path.append(str((Path(__file__) / ".." / ".." / "src").resolve()))
    test_no_changes()
    test_make()
    test_something_else()
    test_make_paperclip()
