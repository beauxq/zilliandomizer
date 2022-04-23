from collections import Counter
import os
from typing import Dict, Generator, List, Set, Tuple, cast, Counter as _Counter
from zilliandomizer.items import KEYWORD, NORMAL, RESCUE
from zilliandomizer.locations import Location
from zilliandomizer.options import ID, VBLR, Chars, Options, char_to_jump, char_to_gun, chars
from zilliandomizer import asm, rom_info
from zilliandomizer.utils import ItemData, make_loc_name

ROM_NAME = "Zillion (UE) [!].sms"

paths: List[List[str]] = [
    ["."],
    ["roms"],
    ["src"],
    ["src", "roms"],
    ["src", "zilliandomizer"],
    ["src", "zilliandomizer", "roms"],
    [".."],
    ["..", "roms"],  # this one should find it according to the readme instructions
    ["..", ".."],
    ["..", "..", "roms"],
]
""" paths to search for rom """

# TODO: fix Champ rescue sprite in top rooms
# TODO: lots of JJ rescue graphic work
# (easy step is, after champ sprite is fixed, use that for jj on play screen)


class Patcher:
    writes: Dict[int, int]  # address to byte
    verify: bool
    end_of_available: int
    rom_path: str
    rom: bytearray

    def __init__(self) -> None:
        self.writes = {}
        self.verify = True
        self.end_of_available = rom_info.free_space_end_7e00  # 1st used byte after an unused section

        self.rom_path = ""
        for path_list in paths:
            assert len(path_list)  # use "." for current directory
            path = os.sep.join(path_list)
            if os.path.exists(path + os.sep + ROM_NAME):
                self.rom_path = path
                break
        if self.rom_path == "":
            raise FileNotFoundError(f'unable to find original rom "{ROM_NAME}"')
        print(f"found rom at {self.rom_path}{os.sep}{ROM_NAME}")

        with open(f"{self.rom_path}{os.sep}{ROM_NAME}", "rb") as file:
            self.rom = bytearray(file.read())

    def fix_floppy_req(self) -> None:
        """
        The vanilla game requires an exact number of floppies to use the main computer.
        This patch changes it to require at least that number of floppies,
        instead of requiring the exact number.
        """
        # shortly after _LABEL_4FA5_ we compare the # of floppies with 5
        # I think that's saying "If we don't have a good number of floppies, jump to ++"
        # at 1899, we take the number of floppies, and subtract 6.
        # If that goes negative, then jump? I always get confused by subtract carry.
        # If we subtract x=5 and that DOES go negative, we don't have a good number of floppies. So jump?
        # jp c, ++
        # 01:4FB0 = 11011010 (DA) changed from 11000010 (C2)
        # 01:4FAF = number of floppies required
        addr = rom_info.floppy_req_instruction_4fb0
        if self.verify:
            assert self.rom[addr] == asm.JPNZ
        self.writes[addr] = asm.JPC

        # TODO: Investigate: I think there's another place in the code that checks the floppy requirement.
        # maybe something happens at the ship if you have them?

    def fix_floppy_display(self) -> None:
        """
        The vanilla game will display no more than 5 floppies on the pause screen.
        This fix changes it to 8, which is to the edge of the screen.
        This is only visual. You can pick up up to 255 floppies.
        """
        # rom addr 1899 set to 9
        # rom addr 189D set to 8
        # (if floppy_count >= 9: use 8 instead)
        # that will set max floppies displayed to 8
        # (if you go more than 8, they wrap around to the other side of the screen, we don't need that)
        # You can still get more floppies. It just won't show more than this setting.
        compare_addr = rom_info.floppy_display_compare_1899
        change_addr = rom_info.floppy_display_change_189d
        if self.verify:
            assert self.rom[compare_addr] == 0x06
            assert self.rom[change_addr] == 0x05
        self.writes[compare_addr] = 0x09
        self.writes[change_addr] = 0x08

    def fix_rescue_tile_load(self) -> None:
        """ load apple and champ rescue tiles when entering blue area and red area """
        bank_offset = 0x14000  # I hope this bank is always loaded when this code runs

        vram_load_lo = 0xae
        vram_load_hi = 0x03

        champ_lo = rom_info.champ_rescue_banked_tiles_8b93 % 256
        champ_hi = rom_info.champ_rescue_banked_tiles_8b93 // 256
        apple_lo = rom_info.apple_rescue_banked_tiles_8695 % 256
        apple_hi = rom_info.apple_rescue_banked_tiles_8695 // 256
        blue_lo = rom_info.blue_basic_banked_tiles_81fd % 256
        blue_hi = rom_info.blue_basic_banked_tiles_81fd // 256

        blue_code = [
            asm.LDHL, champ_lo, champ_hi,  # set of tiles that has champ's rescue
            asm.LDDE, 0xC0, 0x6F,  # where to put that data
            asm.CALL, vram_load_lo, vram_load_hi,
            asm.LDHL, apple_lo, apple_hi,  # set of tiles that has apple's rescue
            asm.LDDE, 0x20, 0x67,  # where to put that data
            asm.CALL, vram_load_lo, vram_load_hi,
            asm.LDHL, blue_lo, blue_hi,  # blue area canisters
            asm.RET
        ]

        blue_code_addr = rom_info.bank_7_free_space_1ffdb
        banked_blue_addr = blue_code_addr - bank_offset

        for i in range(len(blue_code)):
            if self.verify:
                assert self.rom[blue_code_addr + i] == 0xff
            self.writes[blue_code_addr + i] = blue_code[i]

        red_code = [
            asm.LDHL, champ_lo, champ_hi,  # set of tiles that has champ's rescue
            asm.LDDE, 0xC0, 0x6F,  # where to put that data
            asm.CALL, vram_load_lo, vram_load_hi,
            asm.LDHL, apple_lo, apple_hi,  # set of tiles that has apple's rescue
            asm.RET
        ]

        red_code_addr = blue_code_addr + len(blue_code)
        banked_red_addr = red_code_addr - bank_offset

        for i in range(len(red_code)):
            if self.verify:
                assert self.rom[red_code_addr + i] == 0xff
            self.writes[red_code_addr + i] = red_code[i]

        blue_entry = rom_info.load_blue_code_10a3
        red_entry = rom_info.load_red_code_10cd

        if self.verify:
            assert self.rom[blue_entry + 0] == blue_code[-4]
            assert self.rom[blue_entry + 1] == blue_code[-3]
            assert self.rom[blue_entry + 2] == blue_code[-2]
            assert self.rom[red_entry + 0] == red_code[-4]
            assert self.rom[red_entry + 1] == red_code[-3]
            assert self.rom[red_entry + 2] == red_code[-2]
        self.writes[blue_entry + 0] = asm.CALL
        self.writes[blue_entry + 1] = banked_blue_addr % 256
        self.writes[blue_entry + 2] = banked_blue_addr // 256
        self.writes[red_entry + 0] = asm.CALL
        self.writes[red_entry + 1] = banked_red_addr % 256
        self.writes[red_entry + 2] = banked_red_addr // 256

    def set_required_floppies(self, floppy_count: int) -> None:
        """ set how many floppies are required to use the main computer """
        # 01:4FAF = number of floppies required
        addr = rom_info.floppy_req_4faf
        if self.verify:
            assert self.rom[addr] == 0x05
        assert 0 <= floppy_count < 256
        self.writes[addr] = floppy_count

        # change introduction text to tell how many floppies are required
        addr = rom_info.floppy_intro_text_1a771
        original_text = b'THE 5 FLOPPY DISKS FROM'
        replacement = f"THE {floppy_count} FLOPPY DISKS FROM"
        if floppy_count > 9:
            replacement = f"{floppy_count} FLOPPY DISKS FROM  "
            if floppy_count < 100:
                replacement += " "
        replacement_bytes = replacement.encode("ascii")
        assert len(original_text) == len(replacement_bytes)
        for i in range(len(original_text)):
            if self.verify:
                assert self.rom[addr + i] == original_text[i]
            self.writes[addr + i] = replacement_bytes[i]

        # TODO: Investigate: I think there's another place in the code that checks the floppy requirement.
        # maybe something happens at the ship if you have them?
        # I don't see anything special happening if I go to the ship with 5 floppies.

    def set_display_computer_codes_default(self, display: bool) -> None:
        """
        set the default cursor position to decide whether to show
        all the computer codes in the beginning text boxes

        original rom defaults to true
        """
        # selection is at ram C3A5 bit 4 - 0 (4C) for yes, 1 (5C) for no
        # but I had trouble finding what set the default
        # It gets set to 4C as soon as the option appears.
        # It's 00 since reset before that.
        # found it at 1d0c
        # The bit is also written to C707, but that's not the source of truth.

        address = rom_info.tutorial_menu_default_1d0c
        other_bits = 0x4c
        if self.verify:
            assert (self.rom[address] & 0b11101111) == other_bits
        write = other_bits | ((not display) << 4)
        # 0x1d09 should be [dd, 36, 05, 4c] by default
        self.writes[address] = write

    def set_start_char(self, char: Chars) -> None:
        """ set which character you start the game with """

        # c127 is current character: 0 jj, 1 champ, 2 apple
        # label AA9 sets c127 to 0 when "press start button" with ldir
        #         ld hl, _DATA_AFA_
        #         ld de, _RAM_C11E_
        #         ld bc, $000A
        #         ldir
        # so it looks like 0B03 gets copied to c127 to initialize it

        current_char_init_addr = rom_info.current_char_init_0b03
        if self.verify:
            assert self.rom[current_char_init_addr] == 0x00
        self.writes[current_char_init_addr] = {
            "JJ": 0x00,
            "Apple": 0x02,
            "Champ": 0x01
        }[char]

        # TODO: important!!! change the color of the tiny sprite that comes out of the ship

        # c150 is whether jj is "rescued"
        # c160 for Apple
        # c170 for champ
        # whether they are rescued is initialized by _DATA_7B98_
        jj_rescue = rom_info.char_init_7b98
        champ_rescue = rom_info.char_init_7b98 + 16
        apple_rescue = rom_info.char_init_7b98 + 32
        # for whom to rescue
        apple_rescue_code = rom_info.apple_rescue_code_4bdb  # 70 change to 50 for jj
        champ_rescue_code = rom_info.champ_rescue_code_4be1  # 60 change to 50 for jj
        if self.verify:
            assert self.rom[jj_rescue] == 0x01
            assert self.rom[champ_rescue] == 0x00
            assert self.rom[apple_rescue] == 0x00
            assert self.rom[apple_rescue_code] == 0x70
            assert self.rom[champ_rescue_code] == 0x60
        self.writes[jj_rescue] = int(char == "JJ")
        self.writes[champ_rescue] = int(char == "Champ")
        self.writes[apple_rescue] = int(char == "Apple")
        if char == "Apple":
            # rescue JJ instead of Apple
            self.writes[apple_rescue_code] = 0x50
        elif char == "Champ":
            # rescue JJ instead of Champ
            self.writes[champ_rescue_code] = 0x50

        apple_text_addr = rom_info.apple_rescue_lines_1add8
        champ_text_addr = rom_info.champ_rescue_lines_1ae38

        # change text that char says depending on who is where
        apple_text: Dict[int, Tuple[bytes, bytes]] = {
            apple_text_addr[0]: (b'THANK YOU FOR', b'I<M SO GLAD  '),
            apple_text_addr[1]: (b'RESCUING ME:', b'THAT YOU<RE '),
            apple_text_addr[2]: (b'I<M SORRY THAT', b'ALL RIGHT>    '),
            apple_text_addr[3]: (b'I WAS CAPTURED:', b'JJ:            '),
            apple_text_addr[4]: (b'IS CHAMP', b'LET<S   '),
            apple_text_addr[5]: (b'ALL RIGHT;', b'GO:       ')
        }
        champ_text: Dict[int, Tuple[bytes, bytes]] = {
            champ_text_addr[0]: (b'YOU<RE', b'HOW DO'),
            champ_text_addr[1]: (b'VERY LATE:', b'WE KEEP   '),
            champ_text_addr[2]: (b'WHAT<VE YOU', b'GETTING IN '),
            champ_text_addr[3]: (b'BEEN DOING;', b'THIS MESS; '),
            champ_text_addr[4]: (b'AH> I<VE', b'LET<S   '),
            champ_text_addr[5]: (b'BUNGLED THINGS', b'GET OUT OF    '),
            champ_text_addr[6]: (b'BADLY:', b'HERE: ')
        }
        for old, new in apple_text.values():
            assert len(old) == len(new)
        for old, new in champ_text.values():
            assert len(old) == len(new)
        if self.verify:
            for addr in apple_text:
                old, _ = apple_text[addr]
                for i in range(len(old)):
                    # print(f"checking addr {hex(addr + i)}: {chr(self.rom[addr + i])} {chr(old[i])}")
                    assert self.rom[addr + i] == old[i]
            for addr in champ_text:
                old, _ = champ_text[addr]
                for i in range(len(old)):
                    assert self.rom[addr + i] == old[i]
        if char != "JJ":
            text = apple_text if char == "Apple" else champ_text
            for addr in text:
                _, new = text[addr]
                for i in range(len(new)):
                    self.writes[addr + i] = new[i]

        # TODO: starting text says who has been captured, wrongly

    def set_item(self, address: int, data: ItemData) -> None:
        for i, v in enumerate(data):
            if v < 0 or v > 255:
                print(f"item index {i} trying to write {v}")
            self.writes[address + i] = v

    def write(self, filename: str) -> None:
        if not filename.endswith(".sms"):
            filename += ".sms"
        new_rom = bytearray(self.rom)  # copy
        for address in self.writes:
            new_rom[address] = self.writes[address]
        with open(f"{self.rom_path}{os.sep}{filename}", "wb") as file:
            file.write(new_rom)

    def get_item_index_for_room(self, room: int) -> int:
        index = rom_info.room_table_91c2 + 2 * room
        low = self.rom[index]
        high = self.rom[index + 1]
        return (high << 8) | low

    def get_item_rooms(self) -> Generator[int, None, None]:
        """
        bytes indexes for the data structures of the items of each room
        """
        for i in range(136):
            yield self.get_item_index_for_room(i)

    def item_count(self, ram_index: int) -> int:
        """ parameter is from `get_item_index_for_room` or `get_item_rooms` """
        return self.rom[ram_index]

    def get_items(self, ram_index: int) -> Generator[ItemData, None, None]:
        """ parameter is from `get_item_index_for_room` or `get_item_rooms` """
        start = ram_index + 1
        for _ in range(self.item_count(ram_index)):
            this_item: ItemData = cast(ItemData, tuple(self.rom[v] for v in range(start, start + 8)))
            yield this_item
            start += 8

    def write_locations(self, locations: Dict[str, Location]) -> None:
        for room_no, room in enumerate(self.get_item_rooms()):
            for item_no, item_from_rom in enumerate(self.get_items(room)):
                if item_from_rom[0] in {KEYWORD, NORMAL, RESCUE}:
                    name = make_loc_name(room_no, item_from_rom)
                    loc = locations[name]
                    assert not (loc.item is None)
                    y = item_from_rom[1]
                    if loc.item.code == RESCUE:
                        y -= 8
                    if item_from_rom[0] == RESCUE:
                        y += 8
                    x = item_from_rom[2]
                    r = item_from_rom[3]  # not changing room code (different from room number)
                    m = item_from_rom[4]  # not changing bit mask to id item within room
                    i = loc.item.id
                    s = loc.req.gun * 2
                    # different sprite for red and paperclip
                    if room_no >= 80:
                        s += 12
                    elif room_no >= 40:
                        s += 6
                    if loc.item.code == RESCUE:
                        s = loc.item.id * 2 + 0x14
                    g = max(0, loc.req.gun - 1)
                    new_item_data: ItemData = (loc.item.code, y, x, r, m, i, s, g)
                    self.set_item(room + 1 + 8 * item_no, new_item_data)

    def set_new_opa_level_system(self, opas_per_level: int, hp_per_level: int = 20, max_level: int = 8) -> None:
        """
        Letting the player choose who to level up has a few drawbacks:
         - possible softlock from making bad choices (nobody has jump 3 when it's required)
         - In multiworld, you won't be able to choose because you won't know it's coming beforehand.

        So with this new system:
         - Everyone levels up together (even if they're not rescued yet).
         - You can choose how many opa-opas are required for a level up.
         - You can set a max level from 1 to 8.
         - The currently active character is still the only one that gets the health refill.
           - TODO: Change this to choose based on missing (effective) health, and/or an option to refill everyone.
        """
        rom_hp_per_level = round(hp_per_level / 10)
        if not (hp_per_level % 10 == 0):
            print(f"warning: hp_per_level needs to be multiple of 10, rounding to {rom_hp_per_level * 10}")
        max_level = min(8, max_level)  # limited to 3 bits, would be difficult to change
        max_level = max(1, max_level)

        # original code location
        old_hi = rom_info.level_up_code_4adf // 256
        old_lo = rom_info.level_up_code_4adf % 256

        # this is the location of the "+" label of the 4ADF section of code in the rom
        _4ADF_plus_hi = rom_info.level_up_code_plus_4aeb // 256
        _4ADF_plus_lo = rom_info.level_up_code_plus_4aeb % 256

        # ram locations for each char's level
        lv_hi = 0xc1
        lv_jj_lo = 0x55
        lv_ch_lo = 0x65
        lv_ap_lo = 0x75

        # new ram going to use - hope it's not already used
        opa_hi = 0xc2
        opa_lo = 0xee

        new_code = bytearray([
            # get opa opa
            asm.LDAV, opa_lo, opa_hi,
            asm.INCA,
            asm.CP, opas_per_level,
            asm.JRZ, 6,
            asm.LDVA, opa_lo, opa_hi,
            asm.JP, _4ADF_plus_lo, _4ADF_plus_hi,

            # level up all chars
            asm.LDAI, 0,
            asm.LDVA, opa_lo, opa_hi,
            asm.LDHL, lv_jj_lo, lv_hi,
            asm.LDAVHL,
            asm.CP, max_level - 1,  # memory values are 0 to 7
            asm.JPNC, _4ADF_plus_lo, _4ADF_plus_hi,
            asm.INCVHL,
            asm.LDHL, lv_ch_lo, lv_hi,
            asm.INCVHL,
            asm.LDHL, lv_ap_lo, lv_hi,
            asm.INCVHL,

            # load jumps into pause screen data so we can see them
            asm.LDAVHL,
            asm.ADDAA,
            asm.ADDAA,
            asm.LDCA,
            asm.LDBI, 0x00,
            asm.LDHL, 0xc9, 0x7c,  # jj level 0 jump
            asm.ADDHLBC,
            asm.LDAVHL,
            asm.LDVA, 0x58, 0xc1,
            asm.LDCI, 0x20,
            asm.ADDHLBC,  # move to Champ's data
            asm.LDAVHL,
            asm.LDVA, 0x68, 0xc1,
            asm.ADDHLBC,  # move to Apple's data
            asm.LDAVHL,
            asm.LDVA, 0x78, 0xc1,

            # change hp and max hp by hp per level
            asm.LDAV, 0x51, 0xc1,  # JJ max hp
            asm.ADDAI, rom_hp_per_level,
            asm.DAA,
            asm.LDVA, 0x51, 0xc1,
            asm.LDAV, 0x53, 0xc1,  # JJ curr hp
            asm.ADDAI, rom_hp_per_level,
            asm.DAA,
            asm.LDVA, 0x53, 0xc1,
            asm.LDAV, 0x61, 0xc1,  # Champ max hp
            asm.ADDAI, rom_hp_per_level,
            asm.DAA,
            asm.LDVA, 0x61, 0xc1,
            asm.LDAV, 0x63, 0xc1,  # Champ curr hp
            asm.ADDAI, rom_hp_per_level,
            asm.DAA,
            asm.LDVA, 0x63, 0xc1,
            asm.LDAV, 0x71, 0xc1,  # Apple max hp
            asm.ADDAI, rom_hp_per_level,
            asm.DAA,
            asm.LDVA, 0x71, 0xc1,
            asm.LDAV, 0x73, 0xc1,  # Apple curr hp
            asm.ADDAI, rom_hp_per_level,
            asm.DAA,
            asm.LDVA, 0x73, 0xc1,

            # TODO: before jumping to 4adf, handle HP fill
            asm.JP, old_lo, old_hi
        ])
        length = len(new_code)

        new_code_addr = self.end_of_available - length  # 7e00 is 1st used byte after an unused section
        self.end_of_available = new_code_addr

        print(f"programming {length} bytes for new opa code at {hex(new_code_addr)}")
        for i in range(length):
            write_addr = new_code_addr + i
            if self.verify:
                assert self.rom[write_addr] == 0xff
            self.writes[write_addr] = new_code[i]

        # change jump table to point at new code
        # table at 4ABC, 2 bytes for each entry, we want entry 9 for opa-opa
        entry = rom_info.item_pickup_jump_table_4abc + 2 * ID.opa
        if self.verify:
            assert self.rom[entry] == old_lo
            assert self.rom[entry + 1] == old_hi
        self.writes[entry] = new_code_addr % 256
        self.writes[entry + 1] = new_code_addr // 256

    def set_jump_levels(self, jump_option: VBLR) -> None:
        table_addr = rom_info.stats_per_level_table_7cc8
        jump_base = table_addr + 1

        init_table_jump = rom_info.char_init_7b98 + 8  # jump in initialization of char data

        for char_i, char in enumerate(chars):
            jump_addr = init_table_jump + char_i * 16
            if self.verify:
                # print(char)
                # print(self.rom[jump_addr], char_to_jump[char]["vanilla"][0] - 1)
                assert self.rom[jump_addr] == char_to_jump[char]["vanilla"][0] - 1
            self.writes[jump_addr] = char_to_jump[char][jump_option][0] - 1

            for level_i in range(8):
                addr = jump_base + char_i * 32 + level_i * 4
                if self.verify:
                    assert self.rom[addr] == char_to_jump[char]["vanilla"][level_i] - 1
                self.writes[addr] = char_to_jump[char][jump_option][level_i] - 1

    def set_new_gun_system_and_levels(self, gun: VBLR) -> None:
        MAX_GUN_LEVEL_COUNT = 7
        table = bytearray(len(chars) * MAX_GUN_LEVEL_COUNT)
        for char_i, char in enumerate(chars):
            gun_levels = char_to_gun[char][gun][:]
            while len(gun_levels) < MAX_GUN_LEVEL_COUNT:
                gun_levels.append(gun_levels[-1])
            for level_i in range(MAX_GUN_LEVEL_COUNT):
                table[level_i * len(chars) + char_i] = gun_levels[level_i] - 1
        # 21 byte table
        length = len(table)
        table_addr = self.end_of_available - length
        self.end_of_available = table_addr
        print(f"programming {length} bytes for gun table at {hex(table_addr)}")
        for i in range(length):
            addr = table_addr + i
            if self.verify:
                assert self.rom[addr] == 0xff
            self.writes[addr] = table[i]

        # initialization of gun data
        init_table_gun = rom_info.char_init_7b98 + 6  # gun in initialization of char data
        for table_i, addr in enumerate(range(init_table_gun, init_table_gun + 33, 16)):
            if self.verify:
                assert self.rom[addr] == char_to_gun[chars[table_i]]["vanilla"][0] - 1
            self.writes[addr] = table[table_i]

        # new ram going to use - hope it's not already used
        new_gun_hi = 0xc2
        new_gun_lo = 0xec

        # ram locations for each char's gun level
        gn_hi = 0xc1
        gn_cu_lo = 0x46
        gn_jj_lo = 0x56
        gn_ch_lo = 0x66
        gn_ap_lo = 0x76

        # the vanilla code to go back to after incrementing guns
        after_gun_hi = rom_info.code_after_increment_gun_7c1e // 256
        after_gun_lo = rom_info.code_after_increment_gun_7c1e % 256

        new_gun_code = bytearray([
            asm.LDAV, new_gun_lo, new_gun_hi,
            asm.LDCA,
            asm.ADDAA,
            asm.ADDAC,
            asm.LDCA,  # c = 3 * gun
            asm.LDBI, 0x00,
            asm.LDHL, table_addr % 256, table_addr // 256,
            asm.ADDHLBC,
            asm.LDAVHL,  # JJ's gun level
            asm.LDVA, gn_jj_lo, gn_hi,
            asm.INCHL,
            asm.LDAVHL,  # Champ's gun level
            asm.LDVA, gn_ch_lo, gn_hi,
            asm.INCHL,
            asm.LDAVHL,  # Apple's gun level
            asm.LDVA, gn_ap_lo, gn_hi,
            # now the current char gun level
            asm.LDAV, 0x27, 0xc1,  # current char
            asm.ADDAA,
            asm.ADDAA,
            asm.ADDAA,
            asm.ADDAA,
            asm.LDCA,  # c = 16 * current char
            asm.LDBI, 0x00,
            asm.LDHL, gn_jj_lo, gn_hi,
            asm.ADDHLBC,
            asm.LDAVHL,
            asm.LDVA, gn_cu_lo, gn_hi,
            asm.JP, after_gun_lo, after_gun_hi
        ])
        length = len(new_gun_code)  # 48
        new_code_addr = self.end_of_available - length
        self.end_of_available = new_code_addr
        print(f"programming {length} bytes for new gun code at {hex(new_code_addr)}")

        for i in range(length):
            write_addr = new_code_addr + i
            if self.verify:
                assert self.rom[write_addr] == 0xff
            self.writes[write_addr] = new_gun_code[i]

        gun_inc = rom_info.increment_gun_code_4af8

        # now change existing increment gun code to point at that new code
        changes: Dict[int, Tuple[int, int]] = {
            gun_inc + 0: (gn_cu_lo, new_gun_lo),  # increment at this address
            gun_inc + 1: (gn_hi, new_gun_hi),
            gun_inc + 4: (0x02, MAX_GUN_LEVEL_COUNT - 1),  # compare value for limit
            gun_inc + 8: (after_gun_lo, new_code_addr % 256),  # jump here if we incremented
            gun_inc + 9: (after_gun_hi, new_code_addr // 256)
        }
        for addr in changes:
            old, new = changes[addr]
            if self.verify:
                assert self.rom[addr] == old
            self.writes[addr] = new

    def all_fixes_and_options(self, options: Options) -> None:
        self.fix_floppy_display()
        self.fix_floppy_req()
        self.fix_rescue_tile_load()
        self.set_display_computer_codes_default(options.tutorial)
        self.set_start_char(options.start_char)
        self.set_required_floppies(options.floppy_req)
        self.set_new_opa_level_system(options.opas_per_level, 20, options.max_level)
        self.set_new_gun_system_and_levels(options.gun_levels)
        self.set_jump_levels(options.jump_levels)


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

    p.write("zillion_latest_gun_patch_test")


if __name__ == "__main__":
    test_patches()
