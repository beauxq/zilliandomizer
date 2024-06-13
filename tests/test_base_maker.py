from zilliandomizer.map_gen.base_maker import BaseMaker, Node, red_inputs


def test_make() -> None:
    possible, existing = red_inputs()
    bm = BaseMaker(5, 5, possible, existing, None)
    bm.make()
    print(bm.map_str())
    print(bm.path(Node(0, 3), Node(4, 0)))

    print(f"fork distance {bm.fork_altitude(Node(0, 3), (Node(1, 0), Node(3, 0), Node(4, 0)))}")


def test_no_changes() -> None:
    possible, existing = red_inputs()
    bm = BaseMaker(5, 5, possible, existing, None)
    assert bm.no_changes == {(4, 0), (1, 2), (0, 3), (4, 3)}


if __name__ == "__main__":
    test_no_changes()
    test_make()
