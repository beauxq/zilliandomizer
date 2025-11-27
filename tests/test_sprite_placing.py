
from zilliandomizer.logger import Logger
from zilliandomizer.room_gen.common import BOT_LEFT, BOT_RIGHT, Coord
from zilliandomizer.room_gen.maze import Grid, g_row
from zilliandomizer.room_gen.sprite_placing import alarm_places


def test_alarm_places() -> None:
    logger = Logger()
    exits: list[Coord] = [BOT_LEFT, BOT_RIGHT]
    g = Grid(exits, exits, 0x0a, logger, 5, [], [])
    g.data = [
        g_row("              "),
        g_row("              "),
        g_row("              "),
        g_row("              "),
        g_row("              "),
        g_row("______________"),
    ]
    ap = alarm_places(g, [(5, 7)])
    horizontals = list(filter(lambda b: b.horizontal, ap.bars))
    print(horizontals)
    assert len(horizontals) == 4
    verticals = list(filter(lambda b: not b.horizontal, ap.bars))
    print(verticals)
    assert len(verticals) == 0
    print(len(ap.bars))

    g.data[4] = g_row("        _     ")
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
