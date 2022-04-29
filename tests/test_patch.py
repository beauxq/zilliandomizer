import os
import pytest
from typing import Counter as _Counter, Set
from collections import Counter
from zilliandomizer.patch import Patcher


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
    p.set_new_opa_level_system(1)
    p.set_jump_levels("restrictive")
    p.set_new_gun_system_and_levels("restrictive")
    p.set_required_floppies(18)
    p.set_start_char("Champ")

    p.write("patch_test")
    if os.path.exists("patch_test.sms"):
        os.remove("patch_test.sms")
