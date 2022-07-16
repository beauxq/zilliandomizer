import pytest
from zilliandomizer.logger import Logger
from zilliandomizer.patch import Patcher
from zilliandomizer.room_gen.common import BOT_LEFT, BOT_RIGHT, TOP_LEFT, TOP_RIGHT
from zilliandomizer.room_gen.maze import Grid, Cell
from zilliandomizer.terrain_compressor import TerrainCompressor


@pytest.mark.usefixtures("fake_rom")
def test_navigation() -> None:
    p = Patcher()
    tc = TerrainCompressor(p.rom)
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    skill = 5
    ends = [BOT_LEFT, BOT_RIGHT]
    g = Grid(ends, ends, tc, log, skill)
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


@pytest.mark.usefixtures("fake_rom")
def test_jump_requirements() -> None:
    p = Patcher()
    tc = TerrainCompressor(p.rom)
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True
    g = Grid([BOT_LEFT, TOP_LEFT], [BOT_LEFT, TOP_LEFT], tc, log, 5)
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


@pytest.mark.usefixtures("fake_rom")
def test_softlock_detect() -> None:
    """ jumping to known softlock """
    p = Patcher()
    tc = TerrainCompressor(p.rom)
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    skill = 5  # needed to make some of these jumps
    g = Grid([BOT_LEFT, TOP_LEFT], [BOT_LEFT, TOP_LEFT], tc, log, skill)
    g.data = [
        list("             |"),
        list("__          _ "),
        list("            |_"),
        list("   __        |"),
        list("             |"),
        list("_____________|"),
    ]
    assert not g.softlock_exists(3), "softlock exists that I can't reach 3"
    assert not g.softlock_exists(2), "softlock exists that I can't reach 2"

    # horizontal jump length 3
    g.data[1][8] = Cell.floor
    assert g.softlock_exists(3), "horizontal jump 3"

    # It is possible to softlock like this with jump 2 (2.5 blocks),
    # but my movement logic says I can't do this hor jump with 2 jump blocks
    # assert g.softlock_exists(2), "hor jump 3 with 2"

    g.data[1][9] = Cell.floor
    assert g.softlock_exists(3)
    assert g.softlock_exists(2)
    g.data[1][9] = Cell.space
    g.data[1][8] = Cell.space

    # Champ room exit equivalent jump
    g.data[2][7] = Cell.floor
    assert g.softlock_exists(3), "Champ room exit jump 3 to softlock"
    assert g.softlock_exists(2), "Champ room exit jump 2 to softlock"
    # add ceiling
    g.data[0][7] = '_'
    assert g.softlock_exists(3), "Champ room exit jump 3 with ceiling to softlock"
    assert g.softlock_exists(2), "Champ room exit jump 2 with ceiling to softlock"

    g.data = [
        list("          _  |"),
        list("__          _ "),
        list("            |_"),
        list("   __    _   |"),
        list("             |"),
        list("_____________|"),
    ]
    # TODO: how to deal with this?
    # bring crawl fall back for the places I think I can't get to?
    # or always do softlock detection with 4 blocks (in addition to 2 and 3)?
    # assert g.softlock_exists(2)
    # assert g.softlock_exists(3)
    assert g.softlock_exists(4)


@pytest.mark.usefixtures("fake_rom")
def test_from_early_dev() -> None:
    p = Patcher()
    tc = TerrainCompressor(p.rom)
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    skill = 5
    ends = [BOT_LEFT, TOP_RIGHT]
    g = Grid(ends, ends, tc, log, skill)
    g.data = [
        list("| _   _       "),
        list("    _ |  _ ___"),
        list("___   |   __  "),
        list("|| _ _   __  _"),
        list("   |_ _  _  _ "),
        list("_________|____"),
    ]
    assert g.softlock_exists(2)

    ends = [BOT_LEFT, (2, 1)]
    g = Grid(ends, ends, tc, log, skill)
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


@pytest.mark.usefixtures("fake_rom")
def test_skill_required_for_jumps() -> None:
    p = Patcher()
    tc = TerrainCompressor(p.rom)
    log = Logger()
    log.debug_stdout = True
    log.spoil_stdout = True

    ends = [BOT_LEFT, TOP_RIGHT]
    g = Grid(ends, ends, tc, log, 0)
    g.data = [
        list("              "),
        list("            __"),
        list("              "),
        list("            __"),
        list("              "),
        list("______________"),
    ]
    assert not g.solve(2), "whether skill 0 can jump around ledges"
    h = Grid(ends, ends, tc, log, 2)
    h.data = g.data
    assert h.solve(2), "whether skill 2 can jump around ledges"
    h.data[1][10] = Cell.floor
    assert not h.solve(2), "whether skill 2 can jump with horizontal movement into 1-tile holes"
    i = Grid(ends, ends, tc, log, 5)
    i.data = h.data
    assert i.solve(2), "whether skill 5 can jump with horizontal movement into 1-tile holes"

    # make sure it doesn't think impossible jump is possible
    g = Grid(ends, ends, tc, log, 5)
    g.data = [
        list("              "),
        list("        _   __"),
        list("          __| "),
        list("            | "),
        list("          __| "),
        list("______________"),
    ]
    assert not g.solve(2)
    g = Grid(ends, ends, tc, log, 5)
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
    g = Grid(ends, ends, tc, log, 5)
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


if __name__ == "__main__":
    test_navigation()
    test_jump_requirements()
    test_softlock_detect()
    test_from_early_dev()
    test_skill_required_for_jumps()
