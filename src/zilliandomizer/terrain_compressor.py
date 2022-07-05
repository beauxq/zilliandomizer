from copy import deepcopy
from typing import ClassVar, Dict, List, Literal

from zilliandomizer.low_resources import rom_info


class TerrainCompressor:
    """
    This class holds the terrain data and lets us change it one room at a time.

    The original game does not have optimal compression for the terrain data.
    With better compression, it can be stored in 77 fewer bytes.
    This gives some room to make changes to the terrain.
    """
    BANK_OFFSET: ClassVar[int] = 0x8000

    @staticmethod
    def decompress(_bytes: List[int]) -> List[int]:
        tr: List[int] = []
        cursor = 0
        while cursor < len(_bytes):
            command = _bytes[cursor]
            cursor += 1
            if command & 0x80:
                number = command & 0x7f
                for _ in range(number):
                    tr.append(_bytes[cursor])
                    cursor += 1
            else:  # no MSB set
                number = command
                for _ in range(number):
                    tr.append(_bytes[cursor])
                cursor += 1

        return tr

    @staticmethod
    def compress(_bytes: List[int]) -> List[int]:
        assert len(_bytes) == 96
        tr: List[int] = []
        current_state: Literal["length", "copy"] = "length"
        cursor = 0
        copy_address = -1
        while cursor < len(_bytes):
            count = 1
            current_byte = _bytes[cursor]
            cursor += 1
            while cursor < len(_bytes) and _bytes[cursor] == current_byte:
                count += 1
                cursor += 1
            if current_state == "copy":
                if count < 3:
                    # stay copy
                    tr.extend([current_byte] * count)
                    tr[copy_address] += count
                else:  # count > 2
                    # change state
                    current_state = "length"
                    tr.append(count)
                    tr.append(current_byte)
            else:  # length
                if count == 1:
                    current_state = "copy"
                    copy_address = len(tr)
                    tr.append(0x81)
                    tr.append(current_byte)
                else:  # count > 1
                    # stay length
                    tr.append(count)
                    tr.append(current_byte)
        tr.append(0x00)
        return tr

    _map_indexes: List[int]
    """ rooms that aren't hallways """
    _rooms: Dict[int, List[int]]
    """ map index: recompressed bytes (including 0 on end) """
    _size: int
    """ total """

    # need to be able to save state this class, to try generating things multiple times
    _saved_rooms: Dict[int, List[int]]
    _saved_size: int

    def __init__(self, rom: bytes) -> None:
        self.load(rom)
        self.save_state()  # make sure there's always something to load

    def load(self, rom: bytes) -> None:
        self._map_indexes = []
        self._rooms = {}
        self._size = 0

        # verified: Dict[int, int] = {}

        for row in range(17):
            for col in range(8):
                index_address = rom_info.terrain_index_13725 + row * 65 + 1 + col * 8
                data_lo = rom[index_address]
                # verified[index_address] = data_lo
                data_hi = rom[index_address + 1]
                # verified[index_address + 1] = data_hi
                map_index = rom[index_address + 3]
                # verified[index_address + 3] = map_index
                # for now at least, this is the 1st assertion that someone with the wrong rom version runs into
                error = "terrain index matching map index - Is this the correct version of the rom?"
                assert map_index == row * 8 + col, error
                address = ((data_hi << 8) | data_lo) + TerrainCompressor.BANK_OFFSET

                assert (map_index != 0x0a) or (address == rom_info.terrain_begin_10ef0), f"first room address {address}"

                if address < rom_info.terrain_begin_10ef0 or address >= rom_info.terrain_end_120da:
                    continue  # hallways

                cursor = address
                original_compressed_bytes: List[int] = []
                while rom[cursor] != 0:
                    original_compressed_bytes.append(rom[cursor])
                    # verified[cursor] = rom[cursor]
                    cursor += 1
                original_compressed_bytes.append(0x00)  # just for consistency
                # verified[cursor] = 0x00

                decompressed = TerrainCompressor.decompress(original_compressed_bytes)
                if map_index == 0x0b:
                    # This room has 2 extra bytes past the end of the room.
                    # I'm guessing it's a typo in the rom.
                    #
                    # (Someone ended the room with 02 3b. That was a visible bug,
                    #  so some else said "It needs to end with 03 3b."
                    #  So someone tacked on a 03 3b after the 02 3b,
                    #  instead of replacing it.)
                    #
                    # And I'm guessing it doesn't have any effect on the game. 🤞
                    # (I don't know the effect of writing 2 bytes past the end of the room.)
                    decompressed = decompressed[:-2]
                assert len(decompressed) == 96
                recompressed = TerrainCompressor.compress(decompressed)

                # update class data
                self._map_indexes.append(map_index)
                self._rooms[map_index] = recompressed
                self._size += len(recompressed)
                # print(len(recompressed))

        original_size = rom_info.terrain_end_120da - rom_info.terrain_begin_10ef0
        assert original_size - self._size == 77, f"original terrain size: {original_size}  recompressed: {self._size}"
        # print(f"average compressed size: {self._size / len(self._map_indexes)}")
        # print(f"average original size: {original_size / len(self._map_indexes)}")
        # print(f"room count: {len(self._map_indexes)}")

        """
        with open("verified_.py", "wt") as file:
            file.write("verified = {\n")
            for key in verified:
                file.write(f"    {hex(key)}: {hex(verified[key])},\n")
            print("}\n")
        """

    def get_writes(self) -> Dict[int, int]:
        tr: Dict[int, int] = {}

        terrain_cursor = rom_info.terrain_begin_10ef0

        for map_index in self._map_indexes:
            row = map_index // 8
            col = map_index % 8
            index_address = rom_info.terrain_index_13725 + row * 65 + 1 + col * 8
            banked_address = terrain_cursor - TerrainCompressor.BANK_OFFSET
            tr[index_address] = banked_address & 0xff
            tr[index_address + 1] = banked_address >> 8
            for byte in self._rooms[map_index]:
                tr[terrain_cursor] = byte
                terrain_cursor += 1

        assert terrain_cursor <= rom_info.terrain_end_120da

        return tr

    def get_space(self) -> int:
        """ return number of bytes from limit (negative if over limit) """
        return (rom_info.terrain_end_120da - rom_info.terrain_begin_10ef0) - self._size

    def get_room(self, map_index: int) -> List[int]:
        """ compressed """
        return self._rooms[map_index][:]

    def set_room(self, map_index: int, data: List[int]) -> None:
        """ compressed, return number of bytes from limit (negative if over limit) """
        self._size -= len(self._rooms[map_index])
        self._size += len(data)
        self._rooms[map_index] = data[:]  # copy to make sure it doesn't get modified after setting

    def save_state(self) -> None:
        self._saved_rooms = deepcopy(self._rooms)
        self._saved_size = self._size

    def load_state(self) -> None:
        self._rooms = deepcopy(self._saved_rooms)
        self._size = self._saved_size
