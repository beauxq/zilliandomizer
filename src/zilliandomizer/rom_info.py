bank_7_free_space_1ffdb = 0x1ffdb
""" from here to the end looks like free space """
free_space_end_7e00 = 0x7e00
""" before this is about 200 bytes of space that looks available """

load_blue_code_10a3 = 0x10a3
""" code that is run when entering blue area to load tiles into vram """
load_red_code_10cd = 0x10cd
""" code that is run when entering red area to load tiles into vram """

# memory address of tile data when bank 7 is active
blue_basic_banked_tiles_81fd = 0x81fd
apple_rescue_banked_tiles_8695 = 0x8695
champ_rescue_banked_tiles_8b93 = 0x8b93

floppy_display_compare_1899 = 0x1899
"""
max number of floppies displayed on pause screen + 1
```
if floppy_count >= (floppy_display_compare):
    display (floppy_display_change) floppies
```
"""
floppy_display_change_189d = 0x189d
"""
max number of floppies displayed on pause screen
```
if floppy_count >= (floppy_display_compare):
    display (floppy_display_change) floppies
```
"""

floppy_req_instruction_4fb0 = 0x4fb0
""" the conditional jump instruction that checks for the correct number of floppies """

floppy_req_4faf = 0x4faf
""" the number of floppies required """

floppy_intro_text_1a771 = 0x1a771
""" the text in the introduction that tells how many floppies are required """

tutorial_menu_default_1d0c = 0x1d0c
""" the default cursor position for showing the computer codes in the intro """

current_char_init_0b03 = 0x0b03
""" initialization of which character is currently playing """

char_init_7b98 = 0x7b98
""" initialization of char stats (to ram c150) """

intro_rescue_text_address = 0x1a83b
""" introduction text telling who is captured """
intro_rescue_text = b'CHAMP AND APPLE ARE'

apple_rescue_code_4bdb = 0x4bdb
""" low byte of pointer to ram character stats for whom to rescue when rescuing apple """
champ_rescue_code_4be1 = 0x4be1
""" low byte of pointer to ram character stats for whom to rescue when rescuing champ """

apple_rescue_lines_1add8 = [
    0x1add8,
    0x1ade8,
    0x1adf7,
    0x1ae08,
    0x1ae1d,
    0x1ae28,
]
""" each line of text displayed when rescuing apple """
champ_rescue_lines_1ae38 = [
    0x1ae38,
    0x1ae41,
    0x1ae4e,
    0x1ae5c,
    0x1ae6d,
    0x1ae78,
    0x1ae89,
]
""" each line of text displayed when rescuing champ """

room_table_91c2 = 0x91c2
""" table that contains the rom address for the item data for each map block """

item_pickup_jump_table_4abc = 0x4abc
""" table to jump to code based on the id of the item I'm picking up """

level_up_code_4adf = 0x4adf
""" code to increment level when picking up opa-opa """
level_up_code_plus_4aeb = 0x4aeb
""" relative jump location in level up code """

stats_per_level_table_7cc8 = 0x7cc8
""" table with the stats that are determined by level """

increment_gun_code_4af8 = 0x4af8
""" code to increment gun level """
code_after_increment_gun_7c1e = 0x7c1e
""" code to run after incrementing gun level """

terrain_index_13725 = 0x13725
"""
starting at `_DATA_13725_` is 65 bytes for each of the 17 rows

each row is 1 byte (unknown purpose, `01` in most of them)

followed by 8 bytes for each column
    - 00-01 banked address of terrain data for that location
    - 02 unknown
    - 03 map index (0-135)
    - 04-07 unknown
"""
terrain_begin_10ef0 = 0x10ef0
"""
The terrain data is packed tightly with some run-length encoding:

command, byte, ...
```
if command & 0x80:
    command & 0x7f is the number of bytes to take
else:
    command is the number of copies of the next byte
```
Each room's terrain data ends with `0x00`
"""
terrain_end_120da = 0x120da
""" the byte after the last room's 0x00 """

continue_count_init_0af5 = 0x0af5
""" the initialization value for the number of continues (+ 1) """
continue_dec_addr_2523 = 0x2523
""" the address of the code that decrements the continues """
continue_dec_code = [0x35, 0xfa, 0x1a, 0x25]
""" the code that decrements the continues """
