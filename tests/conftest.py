import pytest
from typing import Iterator
import os

from verified import verified

from zilliandomizer.options import ID, chars, char_to_jump
from zilliandomizer.patch import ROM_NAME
from zilliandomizer.low_resources import asm, rom_info


def set_verified_bytes(b: bytearray) -> None:
    # floppy display
    b[rom_info.floppy_display_compare_1899] = 0x06
    b[rom_info.floppy_display_change_189d] = 0x05

    # floppy req code
    b[rom_info.floppy_req_instruction_4fb0] = 0xc2
    # floppy req
    b[rom_info.floppy_req_4faf] = 0x05

    # floppy intro text
    floppy_text = b'THE 5 FLOPPY DISKS FROM'
    for i, char in enumerate(floppy_text):
        b[rom_info.floppy_intro_text_1a771 + i] = char

    # rescue sprite code
    for a in range(rom_info.bank_7_free_space_1ffdb, len(b)):
        b[a] = 0xff
    b[rom_info.load_blue_code_10a3 + 0] = asm.LDHL
    b[rom_info.load_blue_code_10a3 + 1] = 0xfd
    b[rom_info.load_blue_code_10a3 + 2] = 0x81
    b[rom_info.load_red_code_10cd + 0] = asm.LDHL
    b[rom_info.load_red_code_10cd + 1] = 0x95
    b[rom_info.load_red_code_10cd + 2] = 0x86

    # tutorial
    b[rom_info.tutorial_menu_default_1d0c] = 0x4c

    # rescue states
    b[rom_info.char_init_7b98] = 0x01
    b[rom_info.char_init_7b98 + 16] = 0x00
    b[rom_info.char_init_7b98 + 32] = 0x00
    b[rom_info.apple_rescue_code_4bdb] = 0x70
    b[rom_info.champ_rescue_code_4be1] = 0x60

    # rescue text
    apple_text = [
        b'THANK YOU FOR',
        b'RESCUING ME:',
        b'I<M SORRY THAT',
        b'I WAS CAPTURED:',
        b'IS CHAMP',
        b'ALL RIGHT;',
    ]
    for line_i, line in enumerate(apple_text):
        for char_i in range(len(line)):
            b[rom_info.apple_rescue_lines_1add8[line_i] + char_i] = line[char_i]
    champ_text = [
        b'YOU<RE',
        b'VERY LATE:',
        b'WHAT<VE YOU',
        b'BEEN DOING;',
        b'AH> I<VE',
        b'BUNGLED THINGS',
        b'BADLY:',
    ]
    for line_i, line in enumerate(champ_text):
        for char_i, char in enumerate(line):
            b[rom_info.champ_rescue_lines_1ae38[line_i] + char_i] = char

    # introduction captured text
    for i in range(len(rom_info.intro_rescue_text)):
        b[rom_info.intro_rescue_text_address + i] = rom_info.intro_rescue_text[i]

    # gun and level code block
    for i in range(rom_info.free_space_end_7e00 - 216, rom_info.free_space_end_7e00):
        b[i] = 0xff

    # opa pickup
    pickup_jump_table_entry = rom_info.item_pickup_jump_table_4abc + 2 * ID.opa
    b[pickup_jump_table_entry] = rom_info.level_up_code_4adf % 256
    b[pickup_jump_table_entry + 1] = rom_info.level_up_code_4adf // 256

    # gun data
    init_table_gun = rom_info.char_init_7b98 + 6  # gun in initialization of char data
    b[init_table_gun] = 0x00
    b[init_table_gun + 16] = 0x02
    b[init_table_gun + 32] = 0x00
    # gun code
    gun_inc = rom_info.increment_gun_code_4af8
    b[gun_inc + 0] = 0x46  # ram address of current char gun
    b[gun_inc + 1] = 0xc1
    b[gun_inc + 4] = 0x02  # compare value for limit
    b[gun_inc + 8] = rom_info.code_after_increment_gun_7c1e % 256
    b[gun_inc + 9] = rom_info.code_after_increment_gun_7c1e // 256

    # jump and speed data
    init_table_jump = rom_info.char_init_7b98 + 8  # index 8 is jump
    init_table_speed = init_table_jump - 1
    b[init_table_jump] = 0x01
    b[init_table_speed] = 0x01
    b[init_table_jump + 16] = 0x00
    b[init_table_speed + 16] = 0x00
    b[init_table_jump + 32] = 0x02
    b[init_table_speed + 32] = 0x02

    speed_values = {
        "JJ": [1, 1, 1, 1, 2, 2, 3, 3],
        "Champ": [0, 0, 0, 0, 1, 1, 2, 2],
        "Apple": [2, 2, 2, 2, 3, 3, 3, 3]
    }
    jump_base = rom_info.stats_per_level_table_7cc8 + 1
    for char_i, character in enumerate(chars):
        for level_i in range(8):
            addr = jump_base + char_i * 32 + level_i * 4
            b[addr] = char_to_jump[character]["vanilla"][level_i] - 1
            b[addr + 1] = speed_values[character][level_i]

    b[rom_info.continue_count_init_0af5] = 4
    for addr, v in enumerate(rom_info.continue_dec_code, rom_info.continue_dec_addr_2523):
        b[addr] = v

    b[rom_info.demo_inc] = asm.INCVHL

    for key in verified:
        b[key] = verified[key]


@pytest.fixture
def fake_rom() -> Iterator[None]:
    path = "roms" + os.sep + ROM_NAME
    created = False
    if not os.path.exists(path):
        created = True
        b = bytearray(0x20000)
        set_verified_bytes(b)
        with open(path, "wb") as file:
            file.write(b)
    yield
    if created:
        os.remove(path)
