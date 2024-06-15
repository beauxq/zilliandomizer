import os
from typing import Iterator
import pytest
from zilliandomizer.generator import generate, some_options
from zilliandomizer.options import Options
from zilliandomizer.system import System


@pytest.fixture
def no_options_file() -> Iterator[None]:
    path_original = "roms" + os.sep + "options.yaml"
    path_temp = "roms" + os.sep + "_options.yaml"
    renamed = False
    if os.path.exists(path_original):
        renamed = True
        os.rename(path_original, path_temp)
    yield
    if renamed:
        os.rename(path_temp, path_original)


@pytest.mark.usefixtures("fake_rom")
def test_all() -> None:
    # looking for seeds that see lots of conditions...
    generate(0x42069428)
    generate(0x42069429)


@pytest.mark.usefixtures("fake_rom")
def test_with_room_gen() -> None:
    system = System()
    p = system.make_patcher()
    options: Options = some_options
    options.map_gen = "rooms"

    system.seed(0x42069429)
    r = system.make_randomizer(options)
    system.make_map()

    r.roll()

    system.post_fill()

    game = system.get_game()

    p.write_locations(game.regions, options.start_char)
    rm = system.resource_managers
    assert rm, "resource_managers not initialized"
    p.all_fixes_and_options(game)

    p.write(os.devnull)


@pytest.mark.usefixtures("fake_rom", "no_options_file")
def test_default_options() -> None:
    generate(0x42069428)


# TODO: make sure the same seed with the same options generates the same output
