from copy import deepcopy
from typing import Tuple, Counter as _Counter
from collections import Counter
import pytest

from zilliandomizer.randomizer import Randomizer
from zilliandomizer.options import ID, Options
from zilliandomizer.generator import some_options
from zilliandomizer.logger import Logger
from zilliandomizer.patch import Patcher
from zilliandomizer.locations import Req
from zilliandomizer.regions import Region
from zilliandomizer.location_data import make_locations
from zilliandomizer.region_data import make_regions


@pytest.mark.usefixtures("fake_rom")
def test_randomizer() -> None:
    s = 7777
    options: Options = some_options
    logger = Logger()
    logger.spoil_stdout = True
    r = Randomizer(options, logger)
    r.roll(s)

    p = Patcher()
    p.write_locations(r.locations, options.start_char)
    p.all_fixes_and_options(options)
    filename = f"zilliandomizer-{s:016x}.sms"
    # p.write(filename)
    print(f"generated: {filename}")


def test_placement() -> None:
    total_iter = 10
    total_completable = 0
    total_item_row = 0

    for s in range(total_iter):
        options: Options = some_options
        logger = Logger()
        logger.spoil_stdout = False
        r = Randomizer(options, logger)
        r.roll(s)
        if r.check():
            total_completable += 1
            for line in logger.spoiler_lines:
                if line.startswith("get Apple"):
                    row = int(line.split(' ')[-1][1:3])
                    total_item_row += row
                    break
    print(f"average Apple row: {total_item_row / total_completable}")


def test_room_door_gun_requirements() -> None:
    rn = Randomizer(some_options)
    gun_reqs = rn.room_door_gun_requirements()

    # run this in console to see a map of gun requirements
    for room in range(136):
        if room in gun_reqs:
            print(gun_reqs[room], end=" ")
        else:
            print("  ", end="")
        if room % 8 == 7:
            print()


def test_get_locations() -> None:
    rn = Randomizer(some_options)
    have = Req(gun=3, jump=3, hp=940, skill=9001)
    locs = rn.get_locations(have)
    print(len(locs))
    rooms: _Counter[Tuple[int, int]] = Counter()
    for loc in locs:
        rs, cs = loc.name.split('y')[0].split('c')
        r = int(rs[1:])
        c = int(cs)
        rooms[(r, c)] += 1
    for row in range(17):
        for col in range(8):
            if (row, col) in rooms:
                print(f"{rooms[(row, col)]} ", end="")
            else:
                print("  ", end="")
        print()


def test_connections() -> None:
    """ check to make sure connections go in both directions """
    locations = make_locations()
    make_regions(locations)
    for name in Region.all:
        region = Region.all[name]
        for neighbor in region.connections:
            assert region in neighbor.connections, f"{region.name} not in {neighbor.name}"


def test_problems() -> None:
    options = deepcopy(some_options)
    options.item_counts[ID.card] = 200
    r = Randomizer(options)
    with pytest.raises(ValueError):
        r.roll(88)

    options = deepcopy(some_options)
    options.floppy_req = 30
    r = Randomizer(options)
    with pytest.raises(ValueError):
        r.roll(88)
