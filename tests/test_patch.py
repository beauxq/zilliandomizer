import os
import pytest
from typing import Counter as _Counter, Iterator, Set
from collections import Counter
from zilliandomizer.low_resources import rom_info
from zilliandomizer.np_sprite_manager import NPSpriteManager
from zilliandomizer.options import Options
from zilliandomizer.patch import ROM_NAME, Patcher
from zilliandomizer.resource_managers import ResourceManagers
from zilliandomizer.room_gen.aem import AlarmEntranceManager
from zilliandomizer.terrain_modifier import TerrainModifier
from zilliandomizer.utils import ItemData


@pytest.mark.usefixtures("fake_rom")
def test_read_items_from_rom() -> None:
    p = Patcher()

    totals: _Counter[int] = Counter()
    door_code_rooms: Set[int] = set()
    col = 0
    for room in p.get_item_rooms():
        item_count = p.item_count(room)
        items = list(p.get_items(room))
        if item_count > 0 and (item_count > 1 or items[0].code != 0x2b):
            found_non_keywords = 0
            for item in items:
                if item.code != 0x0a:
                    found_non_keywords += 1
                else:  # keyword
                    door_code_rooms.add(col)
            if found_non_keywords:
                print(f"{found_non_keywords} ", end="")
            else:
                print("- ", end="")
            for item in items:
                totals[item.item_id] += 1
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
def test_patches_default_options() -> None:
    o = Options()
    p = Patcher()
    rm = ResourceManagers(TerrainModifier(), NPSpriteManager(), AlarmEntranceManager())
    p.all_fixes_and_options(o, rm)


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


# testing always makes fake rom now
# TODO: figure out a way to run tests with real rom
# @pytest.mark.usefixtures("no_rom")
# def test_no_rom() -> None:
#     with pytest.raises(FileNotFoundError):
#         Patcher()


@pytest.mark.usefixtures("fake_rom")
def test_set_item() -> None:
    p = Patcher()
    p.set_item(23, ItemData(-1, 0, 1, 2, 254, 255, 256, 257))


@pytest.mark.usefixtures("fake_rom")
def test_defense() -> None:
    o = Options()
    o.balance_defense = False
    p = Patcher()
    rm = ResourceManagers(TerrainModifier(), NPSpriteManager(), AlarmEntranceManager())
    p.all_fixes_and_options(o, rm)

    for level in range(8):
        for char_i in range(3):
            address = rom_info.stats_per_level_table_7cc8 + char_i * 32 + level * 4 + 3
            assert address not in p.writes, "didn't change defense"

    o.balance_defense = True
    o.skill = 0
    p = Patcher()
    rm = ResourceManagers(TerrainModifier(), NPSpriteManager(), AlarmEntranceManager())
    p.all_fixes_and_options(o, rm)
    apple_level_1_damage_taken = rom_info.stats_per_level_table_7cc8 + 2 * 32 + 0 * 4 + 3
    assert p.writes[apple_level_1_damage_taken] < 4

    o.skill = 5
    p = Patcher()
    rm = ResourceManagers(TerrainModifier(), NPSpriteManager(), AlarmEntranceManager())
    p.all_fixes_and_options(o, rm)
    assert p.writes[apple_level_1_damage_taken] == 4
    apple_level_4_damage_taken = rom_info.stats_per_level_table_7cc8 + 2 * 32 + 3 * 4 + 3
    assert p.writes[apple_level_4_damage_taken] == 4

    o.skill = 2
    p = Patcher()
    rm = ResourceManagers(TerrainModifier(), NPSpriteManager(), AlarmEntranceManager())
    p.all_fixes_and_options(o, rm)
    assert p.writes[apple_level_1_damage_taken] == 4
    apple_level_2_damage_taken = rom_info.stats_per_level_table_7cc8 + 2 * 32 + 1 * 4 + 3
    assert p.writes[apple_level_2_damage_taken] < 4
