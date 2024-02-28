from typing import List

from zilliandomizer.logger import Logger
from zilliandomizer.room_gen.common import BOT_LEFT, BOT_RIGHT, TOP_LEFT, TOP_RIGHT, Coord
from zilliandomizer.room_gen.maze import Grid, Cell
from zilliandomizer.terrain_modifier import TerrainModifier


def test_navigation() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    skill = 5
    ends: List[Coord] = [BOT_LEFT, BOT_RIGHT]
    g = Grid(ends, ends, 0x31, tc, log, skill, [])
    g.data = [
        list("        |||__|"),
        list("__    ___  |||"),
        list("|________    |"),
        list("  ||       __|"),
        list("   _____      "),
        list("______________"),
    ]
    assert g.solve(2)
    assert g.solve(3)
    assert (1, 0, True) not in g.get_goables(2)
    assert (1, 0, True) not in g.get_goables(3)

    g.data = [
        list("              "),
        list("           _  "),
        list("__________ |  "),
        list("          _|_ "),
        list("         _||  "),
        list("__________||__"),
    ]
    assert not g.solve(2)
    assert not g.solve(3)
    g.data[2][9] = Cell.space
    assert g.solve(2)
    assert g.solve(3)
    g.data[2][9] = Cell.floor
    g.data[5][10] = Cell.floor
    assert not g.solve(3)
    g.data[4][10] = Cell.space
    assert not g.solve(3)
    g.data[3][10] = Cell.space
    assert g.solve(2)
    assert g.solve(3)

    g.data = [
        list("       _      "),
        list("              "),
        list("     __  __   "),
        list("     |        "),
        list("   __|     _  "),
        list("_____|________"),
    ]
    assert g.solve(2)
    assert g.solve(3)
    g.is_walkway[2][9] = True
    assert not g.solve(2)
    g.data[0][8] = Cell.floor
    assert g.solve(2)
    g.is_walkway[2][9] = False


def test_jump_requirements() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True
    g = Grid([BOT_LEFT, TOP_LEFT], [BOT_LEFT, TOP_LEFT], 0x31, tc, log, 5, [])
    g.data = [
        list("         |__  "),
        list("__       |||  "),
        list("   ______||  _"),
        list("             |"),
        list("        __   |"),
        list("_____________|"),
    ]
    assert not g.solve(2)
    print("2 false")
    assert g.solve(3)
    print("3 true")


def test_softlock_detect() -> None:
    """ jumping to known softlock """
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    g = Grid([BOT_LEFT, TOP_LEFT], [BOT_LEFT, TOP_LEFT], 0x31, tc, log, 0, [])
    g.data = [
        list("             |"),
        list("__          _ "),
        list("            |_"),
        list("   __        |"),
        list("             |"),
        list("_____________|"),
    ]
    assert g.softlock_exists(), "softlock detection can jump 4 tiles"

    g = Grid([BOT_LEFT, TOP_LEFT], [BOT_LEFT, TOP_LEFT], 0x31, tc, log, 0, [])
    g.data = [
        list("             |"),
        list("__            "),
        list("           _ _"),
        list("   _       | |"),
        list("           | |"),
        list("___________|_|"),
    ]
    assert not g.softlock_exists(), "If you can get in that hole, you can get out."

    g.data[3][9] = Cell.floor
    assert g.softlock_exists(), "jump 2 can get trapped in that hole"


def test_hard_jumps() -> None:
    """ jumping to known softlock """
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends: List[Coord] = [BOT_LEFT, TOP_RIGHT]
    g = Grid(ends, ends, 0x31, tc, log, 5, [])
    g.data = [
        list("              "),
        list("__          __"),
        list("            |_"),
        list("   __        |"),
        list("             |"),
        list("_____________|"),
    ]
    assert not g.solve(3), "can't jump to that platform"

    # horizontal jump length 3
    g.data[1][8] = Cell.floor
    assert g.solve(3), "horizontal jump 3"

    # It is possible to get there with jump 2 (2.5 blocks),
    # but my movement logic says I can't do this hor jump with 2 jump blocks
    # assert g.solve(2), "hor jump 3 with 2"

    g.data[1][9] = Cell.floor
    assert g.solve(3)
    assert g.solve(2)
    g.data[1][9] = Cell.space
    g.data[1][8] = Cell.space

    # Champ room exit equivalent jump
    g.data[2][7] = Cell.floor
    assert g.solve(3), "Champ room exit jump 3"
    assert g.solve(2), "Champ room exit jump 2"
    # add ceiling
    g.data[0][7] = '_'
    assert g.solve(3), "Champ room exit jump 3 with ceiling"
    assert g.solve(2), "Champ room exit jump 2 with ceiling"

    g.data = [
        list("              "),
        list("__   __     __"),
        list("         _  |_"),
        list("   __        |"),
        list("             |"),
        list("_____________|"),
    ]
    # TODO: enable this jump
    # assert g.solve(2), "jump to lower platform"

    g.data = [
        list("          _   "),
        list("__          __"),
        list("            |_"),
        list("   __    _   |"),
        list("             |"),
        list("_____________|"),
    ]
    # This is possible, but traversal logic doesn't support it.
    # assert g.solve(2)
    # assert g.solve(3)
    assert g.solve(4)


def test_from_early_dev() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    skill = 5
    ends: List[Coord] = [BOT_LEFT, TOP_RIGHT]
    g = Grid(ends, ends, 0x31, tc, log, skill, [])
    g.data = [
        list("| _   _       "),
        list("    _ |  _ ___"),
        list("___   |   __  "),
        list("|| _ _   __  _"),
        list("   |_ _  _  _ "),
        list("_________|____"),
    ]
    assert g.softlock_exists()

    ends = [BOT_LEFT, (2, 1)]
    g = Grid(ends, ends, 0x31, tc, log, skill, [])
    g.data = [
        list("         _    "),
        list("   _ _  _|  _ "),
        list(" ____|      | "),
        list("         _ _| "),
        list("    _    |  ||"),
        list("______________"),
    ]
    assert not g.solve(2)
    assert g.solve(3)


def test_skill_required_for_jumps() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends: List[Coord] = [BOT_LEFT, TOP_RIGHT]
    g = Grid(ends, ends, 0x31, tc, log, 0, [])
    g.data = [
        list("              "),
        list("            __"),
        list("              "),
        list("            __"),
        list("              "),
        list("______________"),
    ]
    assert not g.solve(2), "whether skill 0 can jump around ledges"
    h = Grid(ends, ends, 0x31, tc, log, 2, [])
    h.data = g.data
    assert h.solve(2), "whether skill 2 can jump around ledges"
    h.data[1][10] = Cell.floor
    assert not h.solve(2), "whether skill 2 can jump with horizontal movement into 1-tile holes"
    i = Grid(ends, ends, 0x31, tc, log, 5, [])
    i.data = h.data
    assert i.solve(2), "whether skill 5 can jump with horizontal movement into 1-tile holes"

    # make sure it doesn't think impossible jump is possible
    g = Grid(ends, ends, 0x31, tc, log, 5, [])
    g.data = [
        list("              "),
        list("        _   __"),
        list("          __| "),
        list("            | "),
        list("          __| "),
        list("______________"),
    ]
    assert not g.solve(2)
    g = Grid(ends, ends, 0x31, tc, log, 5, [])
    g.data = [
        list("          _   "),
        list("            __"),
        list("              "),
        list("            __"),
        list("              "),
        list("______________"),
    ]
    assert not g.solve(2)
    assert not g.solve(3)
    g = Grid(ends, ends, 0x31, tc, log, 5, [])
    g.data = [
        list("          _   "),
        list("            __"),
        list("              "),
        list("              "),
        list("            __"),
        list("______________"),
    ]
    assert not g.solve(2)
    assert not g.solve(3)

    g.data = [
        list("          _   "),
        list("            __"),
        list("            ||"),
        list("              "),
        list("            __"),
        list("______________"),
    ]
    assert not g.solve(2)
    assert not g.solve(3)

    g.data[2] = list("            __")
    assert not g.solve(2)
    assert not g.solve(3)


def test_long_distance_jumps() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends: List[Coord] = [BOT_LEFT, TOP_RIGHT]
    g = Grid(ends, ends, 0x31, tc, log, 0, [])
    g.data = [
        list("              "),
        list("            __"),
        list("              "),
        list("  ____        "),
        list("              "),
        list("______________"),
    ]
    assert not (g.solve(2) or g.solve(2.5) or g.solve(3)), "can't jump 5"
    g.data[3][6] = Cell.floor
    assert not g.solve(2), "height 2 distance 6, jump blocks 2"
    assert g.solve(2.5), "height 2 distance 6, jump blocks 2.5"
    assert g.solve(3), "height 2 distance 6, jump blocks 3"
    # TODO: verify and implement:
    # g.data[3][7] = Cell.floor
    # assert g.solve(2) and g.solve(2.5) and g.solve(3)

    g.data = [
        list("              "),
        list("            __"),
        list("           _  "),
        list("  __          "),
        list("              "),
        list("______________"),
    ]
    assert not (g.solve(2) or g.solve(2.5)), "can't jump distance 8"
    g.data[3][4] = Cell.floor
    assert not g.solve(2), "height 1 distance 7, jump blocks 2"
    assert g.solve(2.5), "height 1 distance 7, jump blocks 2.5"

    g.data = [
        list("              "),
        list("           ___"),
        list("   __         "),
        list("  _           "),
        list("              "),
        list("______________"),
    ]
    assert not (g.solve(2) or g.solve(2.5)), "can't jump height 1 distance 7 with ceiling"

    g.data = [
        list("              "),
        list("            __"),
        list("   __      _  "),
        list("  __          "),
        list("              "),
        list("______________"),
    ]
    assert not (g.solve(2) or g.solve(2.5)), "can't jump height 0 distance 7"
    g.data[2][5] = Cell.floor
    assert not g.solve(2), "height 0 distance 6, jump blocks 2"
    assert g.solve(2.5), "height 0 distance 6, jump blocks 2.5"


def test_jump_from_walkway() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends: List[Coord] = [BOT_LEFT, TOP_RIGHT]
    g0 = Grid(ends, ends, 0x31, tc, log, 0, [])
    g0.data = [
        list("              "),
        list("     ___  ____"),
        list("     |        "),
        list("_____|__      "),
        list("              "),
        list("______________"),
    ]
    assert g0.solve(2)
    g0.is_walkway[3][7] = 1
    assert not g0.solve(2)
    g0.is_walkway[3][7] = 2
    assert not g0.solve(2)

    g5 = Grid(ends, ends, 0x31, tc, log, 5, [])
    g5.data = g0.data
    assert g5.solve(2)
    g5.is_walkway[3][7] = 1  # right
    # assert g5.solve(2)  # TODO: fix jump in same direction as walkway
    g5.is_walkway[3][7] = 2  # left
    assert not g5.solve(2)


def test_stand_in_moving_walkway() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends: List[Coord] = [BOT_LEFT, TOP_RIGHT]
    g = Grid(ends, ends, 0x31, tc, log, 2, [])
    g.data = [
        list("____          "),
        list("|_ ____     __"),
        list("            _ "),
        list("    _   ______"),
        list("         |||||"),
        list("__________|___"),
    ]

    assert (3, 13, True) in g.get_standing_goables(3), "stand in small space"

    g.is_walkway[3][13] = 2

    assert (3, 13, True) not in g.get_standing_goables(3), "stand in small space from moving walkway"

    g.data = [
        list("____          "),
        list("|_ ____    ___"),
        list("           _  "),
        list("    _   ______"),
        list("         |||||"),
        list("__________|___"),
    ]

    g.is_walkway[3][12] = 2

    assert (3, 13, True) in g.get_standing_goables(3), "stand in larger space from moving walkway"

    g.data = [
        list("____          "),
        list("|_ ____    ___"),
        list("           _ _"),
        list("    _   ______"),
        list("         |||||"),
        list("__________|___"),
    ]

    assert (3, 12, True) not in g.get_standing_goables(3), "stand in small space from moving walkway away from wall"


def test_low_skill_jump_1_distance_5() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends: List[Coord] = [BOT_LEFT, TOP_LEFT]
    g = Grid(ends, ends, 0x31, tc, log, 2, [])
    g.data = [
        list("              "),
        list("_____         "),
        list("              "),
        list("         _ _ _"),
        list("       _      "),
        list("______________"),
    ]
    assert not g.solve(2), "jump 1, skill 2, distance 5"

    setattr(g, "_skill", 5)

    assert g.solve(2), "jump 1, skill 5, distance 5"


def test_low_skill_jump_1_distance_4() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends: List[Coord] = [(1, 7), BOT_RIGHT]
    g = Grid(ends, ends, 0x31, tc, log, 2, [])
    g.data = [
        list("||            "),
        list("___    _______"),
        list("|||   ___    |"),
        list("|      ||     "),
        list("___           "),
        list("______________"),
    ]
    assert not g.softlock_exists()
    assert g.solve(2), "jump 1, skill 2, distance 4"


def test_skill_horizontal_jump_from_walkway() -> None:
    tc = TerrainModifier()
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends: List[Coord] = [BOT_LEFT, TOP_LEFT]
    g = Grid(ends, ends, 0x31, tc, log, 2, [])
    g.data = [
        list("              "),
        list("___ _  _      "),
        list("|||           "),
        list("|          ___"),
        list("              "),
        list("______________"),
    ]
    assert g.solve(2), "jump 2, skill 2, over 2 gap"
    g.is_walkway[1][7] = 2
    assert not g.solve(2), "jump 2 with walkway"
    assert not g.solve(3), "jump 3 with walkway"
    setattr(g, "_skill", 5)
    assert g.solve(2), "jump 2 skill 5 with walkway"
    assert g.solve(3), "jump 3 skill 5 with walkway"


if __name__ == "__main__":
    test_navigation()
    test_jump_requirements()
    test_softlock_detect()
    test_hard_jumps()
    test_from_early_dev()
    test_skill_required_for_jumps()
    test_long_distance_jumps()
    test_jump_from_walkway()
    test_low_skill_jump_1_distance_5()
    test_low_skill_jump_1_distance_4()
    test_skill_horizontal_jump_from_walkway()
