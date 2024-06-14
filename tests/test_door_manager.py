import pytest
from zilliandomizer.map_gen.door_manager import DoorManager
from zilliandomizer.patch import Patcher


@pytest.mark.usefixtures("fake_rom")
def test_no_changes() -> None:
    p = Patcher()
    dm = DoorManager()
    writes = dm.get_writes()
    print(writes)
    new_rom = bytearray(0x14000)
    for a, v in writes.items():
        new_rom[a] = v
    for a, v in writes.items():
        equal = p.rom[a] == v
        if not equal:
            print(f"a {hex(a)}  r {hex(p.rom[a])}  v {hex(v)}")
            line_before = ((a // 16) - 1) * 16
            for line_no in range(line_before, line_before + 3*16, 16):
                print(list(new_rom[line_no:line_no+16]))
            assert equal, f"a {hex(a)}  r {hex(p.rom[a])}  v {hex(v)}"
