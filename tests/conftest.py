from pathlib import Path
import pytest
from typing import Iterator

from zilliandomizer.patch import ROM_NAME, Patcher
from zilliandomizer.utils.file_verification import set_verified_bytes


@pytest.fixture
def fake_rom() -> Iterator[None]:
    path = Path("roms") / ROM_NAME
    created = False
    if not path.exists():
        created = True
        b = bytearray(0x20000)
        set_verified_bytes(b)
        Patcher.checksum(b, True)
        path.write_bytes(b)
    yield
    if created:
        path.unlink()
