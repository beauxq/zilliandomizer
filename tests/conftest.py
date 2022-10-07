import pytest
from typing import Iterator
import os

from zilliandomizer.patch import ROM_NAME, Patcher
from zilliandomizer.utils.file_verification import set_verified_bytes


@pytest.fixture
def fake_rom() -> Iterator[None]:
    path = "roms" + os.sep + ROM_NAME
    created = False
    if not os.path.exists(path):
        created = True
        b = bytearray(0x20000)
        set_verified_bytes(b)
        Patcher.checksum(b, True)
        with open(path, "wb") as file:
            file.write(b)
    yield
    if created:
        os.remove(path)
