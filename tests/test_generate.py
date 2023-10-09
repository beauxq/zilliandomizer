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
    options.room_gen = True

    r = system.make_randomizer(options)

    system.seed(0x42069429)

    system.make_map()

    r.roll()

    system.post_fill()

    p.write_locations(r.regions, options.start_char, r.loc_name_2_pretty)
    rm = system.resource_managers
    assert rm, "resource_managers not initialized"
    p.all_fixes_and_options(options, rm)

    p.write(os.devnull)


@pytest.mark.usefixtures("fake_rom", "no_options_file")
def test_default_options() -> None:
    generate(0x42069428)


# TODO: make sure the same seed with the same options generates the same output
