import os
import pytest
from typing import Counter as _Counter, Iterator, Set
from collections import Counter
from zilliandomizer.patch import ROM_NAME, Patcher


@pytest.mark.usefixtures("fake_rom")
def test_read_items_from_rom() -> None:
    p = Patcher()

    totals: _Counter[int] = Counter()
    door_code_rooms: Set[int] = set()
    col = 0
    for room in p.get_item_rooms():
        item_count = p.item_count(room)
        items = list(p.get_items(room))
        if item_count > 0 and (item_count > 1 or items[0][0] != 0x2b):
            found_non_keywords = 0
            for item in items:
                if item[0] != 0x0a:
                    found_non_keywords += 1
                else:  # keyword
                    door_code_rooms.add(col)
            if found_non_keywords:
                print(f"{found_non_keywords} ", end="")
            else:
                print("- ", end="")
            for item in items:
                totals[item[5]] += 1
        else:
            print("  ", end="")
        if col % 8 == 7:
            print()
        col += 1

    print(totals)
    print(sum(totals.values()))
    print(sorted(list(door_code_rooms)))


@pytest.mark.usefixtures("fake_rom")
def test_patches() -> None:
    p = Patcher()
    p.set_display_computer_codes_default(False)
    p.fix_floppy_display()
    p.fix_floppy_req()
    p.fix_rescue_tile_load()
    p.fix_spoiling_demos()
    p.fix_white_knights()
    p.set_new_opa_level_system(1)
    p.set_jump_levels("restrictive")
    p.set_new_gun_system_and_levels("restrictive")
    p.set_required_floppies(18)
    p.set_start_char("Apple")
    p.set_continues(-1)
    p.set_new_game_over(3)

    p.write("patch_test")
    if os.path.exists("patch_test.sms"):
        os.remove("patch_test.sms")


@pytest.mark.usefixtures("fake_rom")
def test_disable_demo_requirement() -> None:
    with pytest.raises(AssertionError):
        p = Patcher()
        p.set_new_opa_level_system(2)


@pytest.mark.usefixtures("fake_rom")
def test_no_verify() -> None:
    p = Patcher()
    p.verify = False
    p.set_display_computer_codes_default(False)
    p.fix_floppy_display()
    p.fix_floppy_req()
    p.fix_rescue_tile_load()
    p.fix_spoiling_demos()
    p.fix_white_knights()
    p.set_new_opa_level_system(1, 9)
    p.set_jump_levels("low")
    p.set_new_gun_system_and_levels("balanced")
    p.set_required_floppies(180)
    p.set_start_char("Champ")
    p.set_continues(7)
    p.set_new_game_over(7)

    p.write("patch_test")
    if os.path.exists("patch_test.sms"):
        os.remove("patch_test.sms")


@pytest.fixture
def no_rom() -> Iterator[None]:
    path_original = "roms" + os.sep + ROM_NAME
    path_temp = "roms" + os.sep + "_" + ROM_NAME
    renamed = False
    if os.path.exists(path_original):
        renamed = True
        os.rename(path_original, path_temp)
    yield
    if renamed:
        os.rename(path_temp, path_original)


@pytest.mark.usefixtures("no_rom")
def test_no_rom() -> None:
    with pytest.raises(FileNotFoundError):
        Patcher()


@pytest.mark.usefixtures("fake_rom")
def test_set_item() -> None:
    p = Patcher()
    p.set_item(23, (-1, 0, 1, 2, 254, 255, 256, 257))
