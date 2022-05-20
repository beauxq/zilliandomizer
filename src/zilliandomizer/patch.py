import os
from random import shuffle
from typing import ClassVar, Dict, Generator, List, Tuple, cast
from zilliandomizer.logic_components.items import KEYWORD, NORMAL, RESCUE
from zilliandomizer.logic_components.locations import Location
from zilliandomizer.low_resources import asm, rom_info
from zilliandomizer.options import ID, VBLR, Chars, Options, char_to_jump, char_to_gun, chars
from zilliandomizer.terrain_compressor import TerrainCompressor
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


class Patcher:
    writes: Dict[int, int]  # address to byte
    verify: bool

    # limited valuable memory
    end_of_available_bank_independent: int

    # if I disable spoiling demos, i get the bonus of lots more memory in bank 6
    end_of_available_banked_6: int

    demos_disabled: bool

    BANK_6_OFFSET: ClassVar[int] = 0x10000

    rom_path: str
    rom: bytearray
    tc: TerrainCompressor

    def __init__(self) -> None:
        self.writes = {}
        self.verify = True
        self.end_of_available_bank_independent = rom_info.free_space_end_7e00  # 1st used byte after an unused section

        self.end_of_available_banked_6 = rom_info.bank_6_free_space_end_b5e6
        self.demos_disabled = False

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

        self.tc = TerrainCompressor(self.rom)

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

    def fix_spoiling_demos(self) -> None:
        """
        The arcade-style demos that are played if no one presses start
        can spoil randomized information.

        This fix makes it so only the first demo plays.
        The first demo doesn't show any rooms, only hallways.
        """
        if self.verify:
            assert self.rom[rom_info.demo_inc] == asm.INCVHL
        self.writes[rom_info.demo_inc] = asm.NOP

        # this has the side-effect of freeing up lots of space in bank 6
        # (the data used to control the demos)
        self.demos_disabled = True

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

        # In vanilla, if you have exactly 4 floppies,
        # you can use "continue" after you die one extra time.
        # (Normally, you can only use "continue" 3 times,
        #  but if you have 4 floppies, you can use "continue" a 4th time.)
        # I'm not changing this. No matter how many floppies are required
        # to win, 4 is still the number of floppies that gives an extra
        # continue.

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
        # c160 for Champ
        # c170 for Apple
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

        # starting text says who has been captured
        captured: List[str] = [each_char.upper() for each_char in chars if each_char != char]
        shuffle(captured)
        replace_text = f"{captured[0]} AND {captured[1]} ARE"
        need_space = len(rom_info.intro_rescue_text) - len(replace_text)
        replace_text += (" " * need_space)
        replace_text_bytes = replace_text.encode("ascii")
        for i in range(len(rom_info.intro_rescue_text)):
            addr = rom_info.intro_rescue_text_address + i
            if self.verify:
                assert self.rom[addr] == rom_info.intro_rescue_text[i]
            self.writes[addr] = replace_text_bytes[i]

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

    def item_count(self, rom_index: int) -> int:
        """ parameter is from `get_item_index_for_room` or `get_item_rooms` """
        return self.rom[rom_index]

    def get_items(self, rom_index: int) -> Generator[ItemData, None, None]:
        """ parameter is from `get_item_index_for_room` or `get_item_rooms` """
        start = rom_index + 1
        for _ in range(self.item_count(rom_index)):
            this_item: ItemData = cast(ItemData, tuple(self.rom[v] for v in range(start, start + 8)))
            yield this_item
            start += 8

    def write_locations(self, locations: Dict[str, Location], start_char: Chars) -> None:
        for room_no, room in enumerate(self.get_item_rooms()):
            for item_no, item_from_rom in enumerate(self.get_items(room)):
                if item_from_rom[0] in {KEYWORD, NORMAL, RESCUE}:
                    name = make_loc_name(room_no, item_from_rom)
                    loc = locations[name]
                    assert loc.item, "There should be an item placed in every location before writing locations."
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
                        if start_char == "Apple":
                            s = 0x16  # use Champ rescue sprite for both JJ and Champ
                        else:
                            s = loc.item.id * 2 + 0x14
                    g = max(0, loc.req.gun - 1)
                    new_item_data: ItemData = (loc.item.code, y, x, r, m, i, s, g)
                    self.set_item(room + 1 + 8 * item_no, new_item_data)

    def _use_bank_6(self, code: bytearray) -> int:
        """ returns banked address of new code """
        assert self.demos_disabled

        length = len(code)

        new_code_addr_banked = self.end_of_available_banked_6 - length  # 7e00 is 1st used byte after an unused section
        self.end_of_available_banked_6 = new_code_addr_banked
        new_code_addr = new_code_addr_banked + Patcher.BANK_6_OFFSET

        assert new_code_addr > rom_info.bank_6_second_demo_control_b14a

        print(f"programming {length} bytes for new banked code at {hex(new_code_addr)}")
        for i in range(length):
            write_addr = new_code_addr + i
            # no verify in bank 6
            self.writes[write_addr] = code[i]
        return new_code_addr_banked

    def _use_bank_independent(self, code: bytearray) -> int:
        """ returns the address that this code was put at """
        code_len = len(code)
        code_addr = self.end_of_available_bank_independent - code_len
        self.end_of_available_bank_independent = code_addr

        print(f"programming {code_len} bytes for new bank independent code at {hex(code_addr)}")
        for i in range(code_len):
            write_addr = code_addr + i
            if self.verify:
                assert self.rom[write_addr] == 0xff
            self.writes[write_addr] = code[i]
        return code_addr

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

        # subroutine that does the work of leveling up
        # separated because we don't want it taking space in bank independent memory
        # hl pointing at jj's level before calling
        lots_of_work_to_do = bytearray([
            # level up all chars
            asm.INCVHL,
            asm.LDHL, lv_ch_lo, lv_hi,
            asm.INCVHL,
            asm.LDHL, lv_ap_lo, lv_hi,
            asm.INCVHL,

            # load jumps into pause screen data so we can see them
            asm.LDAVHL,  # (Apple's) level into a
            asm.ADDAA,
            asm.ADDAA,  # multiply by 4
            asm.LDCA,  # put it in c
            asm.LDBI, 0x00,
            asm.LDHL, 0xc9, 0x7c,  # jj level 0 jump
            asm.ADDHLBC,  # jj current level jump
            asm.LDAVHL,
            asm.LDVA, 0x58, 0xc1,
            asm.LDCI, 0x20,  # difference between each character
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

            asm.RET
        ])

        work_addr_banked = self._use_bank_6(lots_of_work_to_do)

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

            # check if max level
            asm.XORA,
            asm.LDVA, opa_lo, opa_hi,
            asm.LDHL, lv_jj_lo, lv_hi,
            asm.LDAVHL,
            asm.CP, max_level - 1,  # memory values are 0 to 7
            asm.JPNC, _4ADF_plus_lo, _4ADF_plus_hi,

            # subroutine in bank 6 for lots of work
            asm.LDAV, 0xff, 0xff,
            asm.PUSHAF,
            asm.LDAI, 0x06,
            asm.LDVA, 0xff, 0xff,
            asm.CALL, work_addr_banked & 0xff, work_addr_banked >> 8,
            asm.POPAF,
            asm.LDVA, 0xff, 0xff,

            asm.JP, old_lo, old_hi
        ])
        # this has to use bank independent memory because
        # it jumps to different places that depend on the bank
        new_code_addr = self._use_bank_independent(new_code)

        # change jump table to point at new code
        # table at 4ABC, 2 bytes for each entry, we want entry 9 for opa-opa
        entry = rom_info.item_pickup_jump_table_4abc + 2 * ID.opa
        if self.verify:
            assert self.rom[entry] == old_lo
            assert self.rom[entry + 1] == old_hi
        self.writes[entry] = new_code_addr % 256
        self.writes[entry + 1] = new_code_addr // 256

    def set_jump_levels(self, jump_option: VBLR) -> None:
        # because of r13c1y98x10, this function also sets speed to 1 higher than jump
        # speed is the byte after jump in stats_per_level_table_7cc8
        # speed is the byte before jump in char_init_7b98

        # vanilla speed values for verification
        speed_values: Dict[Chars, List[int]] = {
            "JJ": [1, 1, 1, 1, 2, 2, 3, 3],
            "Champ": [0, 0, 0, 0, 1, 1, 2, 2],
            "Apple": [2, 2, 2, 2, 3, 3, 3, 3]
        }

        table_addr = rom_info.stats_per_level_table_7cc8
        jump_base = table_addr + 1

        init_table_jump = rom_info.char_init_7b98 + 8  # jump in initialization of char data

        for char_i, char in enumerate(chars):
            jump_addr = init_table_jump + char_i * 16
            speed_addr = jump_addr - 1
            if self.verify:
                # print(char)
                # print(self.rom[jump_addr], char_to_jump[char]["vanilla"][0] - 1)
                assert self.rom[jump_addr] == char_to_jump[char]["vanilla"][0] - 1
                assert self.rom[speed_addr] == speed_values[char][0]
            self.writes[jump_addr] = char_to_jump[char][jump_option][0] - 1
            self.writes[jump_addr - 1] = self.writes[jump_addr] + 1

            for level_i in range(8):
                addr = jump_base + char_i * 32 + level_i * 4
                if self.verify:
                    assert self.rom[addr] == char_to_jump[char]["vanilla"][level_i] - 1
                    assert self.rom[addr + 1] == speed_values[char][level_i]
                self.writes[addr] = char_to_jump[char][jump_option][level_i] - 1
                self.writes[addr + 1] = self.writes[addr] + 1  # speed

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
        # I haven't looked at moving gun code out of bank independent yet.
        # It probably can be moved if I need more space.
        table_addr = self._use_bank_independent(table)

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
        # length 48
        new_code_addr = self._use_bank_independent(new_gun_code)

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

    def set_continues(self, count: int) -> None:
        # TODO: change text that says "THE CONTINUE FEATURE CAN BE USED ONLY THREE TIMES"
        if count == -1:
            # infinity
            # it's important for this code that continue_count_init
            # doesn't get changed from it's vanilla 4 value
            code = [
                asm.BIT_B_HL_LO, asm.BIT_2_HL_HI,  # test bit 2 in (hl) (see if (hl) is 4)
                asm.JRZ, 0x100 - 13,               # jr z, -13
            ]
            for i in range(len(code)):
                addr = rom_info.continue_dec_addr_2523 + i
                if self.verify:
                    assert self.rom[addr] == rom_info.continue_dec_code[i]
                self.writes[addr] = code[i]
        else:  # not infinity
            if self.verify:
                assert self.rom[rom_info.continue_count_init_0af5] == 4
            self.writes[rom_info.continue_count_init_0af5] = count + 1

    def set_new_game_over(self, continue_count: int) -> None:
        """
        game over is no fun

        change to teleport back to ship on game over
         - keep items
         - cancel base explosion command
         - reset continues

        This feature requires `fix_spoiling_demos` (for memory space).
        """
        assert self.writes[rom_info.demo_inc] == asm.NOP, "set_new_game_over requires fix_spoiling_demos"

        bank_of_new_code = 0x06

        teleport_code = bytearray([
            asm.LDAV, 0xff, 0xff,  # bank number
            asm.PUSHAF,
            asm.LDAI, 0x04,
            asm.LDVA, 0xff, 0xff,
            asm.LDAI, 0x00,
            asm.LDVA, 0x29, 0xc3,  # map row
            asm.LDAI, 0x03,
            asm.JP, 0xeb, 0x1f,  # vanilla teleport code (used for both warp 6 and warp 7)
        ])

        # jumps to code that depends on bank
        teleport_addr = self._use_bank_independent(teleport_code)

        new_game_over_code = bytearray([
            asm.CALL, teleport_addr & 0xff, teleport_addr >> 8,
            # position initialized by c1ad flag
            # asm.LDAI, 0x50,
            # asm.LDVA, 0x05, 0xc3,  # y position
            # asm.LDAI, 0x18,
            # asm.LDVA, 0x03, 0xc3,  # x position
            asm.XORA,
            # if this flag is turned off,
            # it will think the beginning scene hasn't been initialized and initialize it
            asm.LDVA, 0xad, 0xc1,
            asm.CALL, 0x97, 0x20,  # cancel explosion command
            asm.LDAI, continue_count + 1,
            asm.LDVA, 0x12, 0xc1,  # numbers of continues in ram
            asm.CALL, 0xcc, 0x24,  # continue code that sets hp
            # asm.LDAI, 0x07,  # ship scene
            # asm.CALL, 0xd3, 0x24,  # continue code that sets hp
            asm.RET,
        ])
        # TODO: barrier  sound doesn't turn off with game over

        new_game_over_address_banked = self._use_bank_6(new_game_over_code)

        # wrapper for bank changing
        game_over_wrapper = bytearray([
            asm.LDAI, bank_of_new_code,
            asm.LDVA, 0xff, 0xff,
            asm.CALL, new_game_over_address_banked & 0xff, new_game_over_address_banked >> 8,
            asm.RET,
        ])

        # length 9
        new_code_addr = self._use_bank_independent(game_over_wrapper)

        # now call that new code when game over happens
        new_code = [asm.JP, new_code_addr & 0xff, new_code_addr >> 8]
        for i in range(len(new_code)):
            a = rom_info.game_over_code_retry_24c2 + i
            b = rom_info.game_over_code_0_continues_251a + i
            if self.verify:
                assert self.rom[a] == rom_info.game_over_code[i]
                assert self.rom[b] == rom_info.game_over_code[i]
            self.writes[a] = new_code[i]
            self.writes[b] = new_code[i]

        explode_jump_lo = 0x89
        explode_jump_hi = 0x06

        # in base explosion, change number of continues to 0
        explode_game_over_code = bytearray([
            asm.XORA,  # 0 into a
            asm.LDVA, 0x12, 0xc1,  # continues
            asm.LDAI, 0xa3,  # code that was going to be executed in vanilla
            asm.JP, explode_jump_lo, explode_jump_hi,
        ])

        # too short to be worth a wrapper to bank 6
        explode_addr = self._use_bank_independent(explode_game_over_code)

        # change jump location to that code
        if self.verify:
            assert self.rom[rom_info.base_explosion_jump_2112] == explode_jump_lo
            assert self.rom[rom_info.base_explosion_jump_2112 + 1] == explode_jump_hi
        self.writes[rom_info.base_explosion_jump_2112] = explode_addr & 0xff
        self.writes[rom_info.base_explosion_jump_2112 + 1] = explode_addr >> 8

        # go to scene with continues instead of scene without continues
        if self.verify:
            assert self.rom[rom_info.base_explosion_scene_210b] == 0x06
        self.writes[rom_info.base_explosion_scene_210b] = 0x07

    def fix_white_knights(self) -> None:
        original = b'=ZILLION= MEN'
        better = b'WHITE KNIGHTS'
        assert len(original) == len(better)
        for i in range(len(original)):
            for t_i in rom_info.zillion_men_1ae99_1af22:
                addr = t_i + i
                if self.verify:
                    assert self.rom[addr] == original[i]
                self.writes[addr] = better[i]

    def set_external_item_interface(self, start_char: Chars) -> None:
        """
        If another program can read and write the ram of this game,
        (RetroArch READ_CORE_RAM and WRITE_CORE_RAM)
        it can give items to the player.

        ram address c2ea
         - put an item id 5 or higher to give the player that item
         - put a 3 there to rescue apple (or jj if apple is the starting character)
         - put a 4 there to rescue champ (or jj if champ is the starting character)

        The game will set that address to 0 when it has finished processing that item.
        """
        # new ram going to use - hope it's not already used
        item_flag_hi = 0xc2
        item_flag_lo = 0xea

        # 3 into this interface is the apple rescue scene
        # 4 into this interface is the champ rescue scene
        # (These are normally keyword 4 and empty, which won't be sent.)
        rescue = {
            3: 0x70,
            4: 0x60,
        }
        if start_char == "Apple":
            rescue[3] = 0x50
        elif start_char == "Champ":
            rescue[4] = 0x50

        check_interface_code = bytearray([
            asm.LDAV, 0x1f, 0xc1,  # current scene
            asm.CP, 0x8b,
            asm.RETNZ,  # return if not in scene b (gameplay scene)

            asm.LDHL, item_flag_lo, item_flag_hi,
            asm.LDAVHL,
            asm.ORA,
            asm.RETZ,  # no external item

            # check if item or rescue
            asm.CP, 0x04,
            asm.JRZ, 14,  # champ
            asm.JRC, 19,  # apple

            # item
            # TODO: instead of canister sound, make a new cutscene for scene 6
            # for telling which item and who it came from
            # (based on cutscene 0 because that's a short cutscene that goes back to gameplay)
            # Maybe that should be optional because of the extra time it takes.
            asm.LDAI, 0x97,  # get canister sound
            asm.LDVA, 0x05, 0xc0,  # sound trigger ram
            asm.LDAVHL,  # item id to get
            asm.LDVHLI, 0x00,  # done processing this item
            # could save space, but use extra clock cycles to jump to where these next 2 lines are
            asm.LDHL, 0xbc, 0x4a,
            asm.JP, 0x20, 0x00,  # This jump leads to something with with `ret` instruction.

            # champ
            asm.LDHL, rescue[4], 0xc1,
            asm.JR, 0x03,  # after_apple
            # apple
            asm.LDHL, rescue[3], 0xc1,
            # after_apple
            asm.SET_B_HL_LO, asm.SET_0_HL_HI,

            asm.LDVA, 0x83, 0xc1,  # scene selector

            # set music
            # if c005 doesn't work well, can try this:
            # ld a, $84
            # call _SET_MUSIC_LABEL_689_
            asm.LDAI, 0x84,  # rescue music
            asm.LDVA, 0x05, 0xc0,  # sound trigger

            asm.LDAI, 0x06,  # cutscene
            asm.LDVA, 0x1e, 0xc1,  # scene trigger

            # done processing item
            asm.XORA,
            asm.LDVA, item_flag_lo, item_flag_hi,
            asm.RET,

            # copied from 4a1a, don't understand what this does
            # something to do with facing the canister and/or showing text box
            # 0xfd, 0x36, 0x16, 0x13,  # ld (iy+22), $13
            # 0xfd, 0xcb, 0x08, 0xde,  # set 3, (iy+8)
            # 0xfd, 0xcb, 0x08, 0xee,  # set 5, (iy+8)
            # set 3, (ix+8)  # this is for the local room, so not here
        ])

        check_address_banked = self._use_bank_6(check_interface_code)

        # I might want to move this after some of the other checks in this area.
        # I'm not sure what all of them do.
        # It's important that this points to a 3 byte instruction.
        common_gameplay_0x0c71 = 0x0c71
        splice = common_gameplay_0x0c71

        # don't know if I need to save current bank
        bank_wrapper = bytearray([
            asm.LDAI, 0x06,
            asm.LDVA, 0xff, 0xff,
            asm.CALL, check_address_banked & 0xff, check_address_banked >> 8,
            self.rom[splice], self.rom[splice + 1], self.rom[splice + 2],  # code replaced by jump here
            asm.JP, (splice + 3) & 0xff, (splice + 3) >> 8,
        ])

        # length 14
        new_code_addr = self._use_bank_independent(bank_wrapper)

        if self.verify:
            assert self.rom[splice] == bank_wrapper[-6]
            assert self.rom[splice + 1] == bank_wrapper[-5]
            assert self.rom[splice + 2] == bank_wrapper[-4]
        self.writes[splice] = asm.JP
        self.writes[splice + 1] = new_code_addr & 0xff
        self.writes[splice + 2] = new_code_addr >> 8

    def all_fixes_and_options(self, options: Options) -> None:
        self.writes.update(self.tc.get_writes())
        self.fix_floppy_display()
        self.fix_floppy_req()
        self.fix_rescue_tile_load()
        self.fix_spoiling_demos()
        self.fix_white_knights()
        self.set_display_computer_codes_default(options.tutorial)
        self.set_start_char(options.start_char)
        self.set_required_floppies(options.floppy_req)
        self.set_new_opa_level_system(options.opas_per_level, 20, options.max_level)
        self.set_new_gun_system_and_levels(options.gun_levels)
        self.set_jump_levels(options.jump_levels)
        self.set_continues(options.continues)
        self.set_new_game_over(options.continues)
