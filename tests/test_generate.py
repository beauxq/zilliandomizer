import os
from typing import Iterator
import pytest
from zilliandomizer.generator import generate


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
    # looking for seeds that see all conditions...
    # I don't know if I can guarantee 100% branch coverage after any changes
    generate(0x42069428)
    generate(0x42069429)
    generate(0x42069430)


@pytest.mark.usefixtures("fake_rom", "no_options_file")
def test_default_options() -> None:
    generate(0x42069427)
