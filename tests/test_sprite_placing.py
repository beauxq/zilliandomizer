import pytest
from zilliandomizer.logger import Logger
from zilliandomizer.patch import Patcher
from zilliandomizer.room_gen.common import BOT_LEFT, BOT_RIGHT
from zilliandomizer.room_gen.maze import Grid
from zilliandomizer.room_gen.sprite_placing import alarm_places
from zilliandomizer.terrain_compressor import TerrainCompressor


@pytest.mark.usefixtures("fake_rom")
def test_alarm_places() -> None:
    p = Patcher()
    tc = TerrainCompressor(p.rom)
    logger = Logger()
    exits = [BOT_LEFT, BOT_RIGHT]
    g = Grid(exits, exits, 0x0a, tc, logger, 5, [])
    g.data = [
        list("              "),
        list("              "),
        list("              "),
        list("              "),
        list("              "),
        list("______________")
    ]
    ap = alarm_places(g, [(5, 7)])
    horizontals = list(filter(lambda b: b.horizontal, ap.bars))
    print(horizontals)
    assert len(horizontals) == 4
    verticals = list(filter(lambda b: not b.horizontal, ap.bars))
    print(verticals)
    assert len(verticals) == 0
    print(len(ap.bars))

    g.data[4] = list("        _     ")
    ap = alarm_places(g, [(5, 7)])
    horizontals = list(filter(lambda b: b.horizontal, ap.bars))
    print(horizontals)
    assert len(horizontals) == 4
    verticals = list(filter(lambda b: not b.horizontal, ap.bars))
    print(verticals)
    assert len(verticals) == 1
    print(len(ap.bars))

    ap = alarm_places(g, [(5, 7), (4, 8)])
    horizontals = list(filter(lambda b: b.horizontal, ap.bars))
    print(horizontals)
    assert len(horizontals) == 3
    verticals = list(filter(lambda b: not b.horizontal, ap.bars))
    print(verticals)
    assert len(verticals) == 1
    print(len(ap.bars))

    ap = alarm_places(g, [(5, 7), (4, 8), (5, 9)])
    horizontals = list(filter(lambda b: b.horizontal, ap.bars))
    print(horizontals)
    assert len(horizontals) == 3
    verticals = list(filter(lambda b: not b.horizontal, ap.bars))
    print(verticals)
    assert len(verticals) == 0
    print(len(ap.bars))


if __name__ == "__main__":
    test_alarm_places()
