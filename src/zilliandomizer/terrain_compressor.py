from typing import ClassVar, Dict, List, Literal

from zilliandomizer import rom_info


class TerrainCompressor:
    """
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

    def __init__(self, rom: bytes) -> None:
        self.load(rom)

    def load(self, rom: bytes) -> None:
        self._map_indexes = []
        self._rooms = {}
        self._size = 0

        # verified: Dict[int, int] = {}

        for row in range(17):
            for col in range(8):
                index_address = rom_info.terrain_index + row * 65 + 1 + col * 8
                data_lo = rom[index_address]
                # verified[index_address] = data_lo
                data_hi = rom[index_address + 1]
                # verified[index_address + 1] = data_hi
                map_index = rom[index_address + 3]
                # verified[index_address + 3] = map_index
                assert map_index == row * 8 + col, "terrain index matching map index"
                address = ((data_hi << 8) | data_lo) + TerrainCompressor.BANK_OFFSET

                assert (map_index != 0x0a) or (address == rom_info.terrain_begin), f"first room address {address}"

                if address < rom_info.terrain_begin or address >= rom_info.terrain_end:
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
                recompressed = TerrainCompressor.compress(decompressed)

                # update class data
                self._map_indexes.append(map_index)
                self._rooms[map_index] = recompressed
                self._size += len(recompressed)

        original_size = rom_info.terrain_end - rom_info.terrain_begin
        assert original_size - self._size == 77, f"original terrain size: {original_size}  recompressed: {self._size}"

        """
        with open("verified_.py", "wt") as file:
            file.write("verified = {\n")
            for key in verified:
                file.write(f"    {hex(key)}: {hex(verified[key])},\n")
            print("}\n")
        """

    def get_writes(self) -> Dict[int, int]:
        tr: Dict[int, int] = {}

        terrain_cursor = rom_info.terrain_begin

        for map_index in self._map_indexes:
            row = map_index // 8
            col = map_index % 8
            index_address = rom_info.terrain_index + row * 65 + 1 + col * 8
            banked_address = terrain_cursor - TerrainCompressor.BANK_OFFSET
            tr[index_address] = banked_address & 0xff
            tr[index_address + 1] = banked_address >> 8
            for byte in self._rooms[map_index]:
                tr[terrain_cursor] = byte
                terrain_cursor += 1

        assert terrain_cursor <= rom_info.terrain_end

        return tr
