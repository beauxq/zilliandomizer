import socket
import time
from typing import Dict, Tuple, ClassVar, Literal, Union, Iterable

OP = Literal["READ_CORE_RAM", "WRITE_CORE_RAM"]
DOOR_BYTE_COUNT = 62
CANISTER_ROOM_COUNT = 74

_common_byte_reads = [
    0xc11f, 0xc150, 0xc160, 0xc170, 0xc183, 0xc300
]


class RAInterface:
    sock: socket.socket

    # cached messages so we don't create them on every read
    _door_read_message: Tuple[bytes, bytes]
    _canister_read_message: Tuple[bytes, bytes]
    _byte_read_messages: Dict[int, Tuple[bytes, bytes]]

    RETROARCH: ClassVar[Tuple[str, int]] = ("127.0.0.1", 55355)
    SMS_RAM_OFFSET: ClassVar[int] = 0xc000
    READ: ClassVar[OP] = "READ_CORE_RAM"
    WRITE: ClassVar[OP] = "WRITE_CORE_RAM"

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.25)

        self._build_cached_messages()

    def _build_cached_messages(self) -> None:
        # door data is in 62 bytes starting from d600
        self._door_read_message = self._build_message(RAInterface.READ,
                                                      0xd600,
                                                      DOOR_BYTE_COUNT)
        # canister data is in 2 * 74 bytes starting from d700
        self._canister_read_message = self._build_message(RAInterface.READ,
                                                          0xd700,
                                                          2 * CANISTER_ROOM_COUNT)

        for addr in _common_byte_reads:
            self._byte_read_messages[addr] = self._build_message(
                RAInterface.READ, addr, 1
            )

    @staticmethod
    def _build_message(op: OP, addr: int, params: Union[int, Iterable[int]]) -> Tuple[bytes, bytes]:
        def byte2hex(b: int) -> str:
            return ("0" if b < 16 else "") + hex(b)[2:]

        ram_address = addr - RAInterface.SMS_RAM_OFFSET
        prefix = op + ' ' + hex(ram_address)[2:] + ' '
        if op == RAInterface.READ:
            assert isinstance(params, int)
            params_str = str(params)
        else:  # WRITE
            assert isinstance(params, Iterable)
            params_str = " ".join(byte2hex(b) for b in params)

        return prefix.encode(), params_str.encode()

    def _message(self, prefix: bytes, params: bytes) -> bytes:
        """ parameters from `_build_message` """
        res = b''
        attempt_count = 0
        message = prefix + params
        while True:
            self.sock.sendto(message, RAInterface.RETROARCH)
            try:
                res = self.sock.recv(1024)
            except socket.timeout:
                res = b''

            if res.startswith(prefix):
                break
            if attempt_count >= 3:
                res = b''
                break
            attempt_count += 1
            time.sleep(0.0625)

        if res == b'':
            return res

        split = res.strip().split(b' ')
        try:
            return bytes(int(x, 16) for x in split[2:])
        except ValueError:
            return b''

    def write(self, addr: int, b: bytes) -> None:
        prefix, params = self._build_message(RAInterface.WRITE, addr, b)
        res = self._message(prefix, params)
        print(f"write response: {list(res)}")

    def read(self, addr: int, n_bytes: int = 1) -> bytes:
        """
        this takes extra time to build the message,
        so don't use it for doors and canisters
        """
        if n_bytes == 1 and addr in self._byte_read_messages:
            prefix, params = self._byte_read_messages[addr]
        else:
            prefix, params = self._build_message(RAInterface.READ, addr, n_bytes)
        res = self._message(prefix, params)
        # print(f"read {hex(addr)} response: {list(res)}")
        return res

    def read_doors(self) -> bytes:
        prefix, params = self._door_read_message
        res = self._message(prefix, params)
        # print(f"read doors response: {list(res)}")
        return res

    def read_canisters(self) -> bytes:
        prefix, params = self._canister_read_message
        res = self._message(prefix, params)
        # print(f"read canisters response: {list(res)}")
        return res

    def read_char_status(self) -> Tuple[bytes, bytes, bytes]:
        """ return jj c150, ch c160, ap c170 """
        prefix, params = self._byte_read_messages[0xc150]
        jj_res = self._message(prefix, params)
        prefix, params = self._byte_read_messages[0xc160]
        ch_res = self._message(prefix, params)
        prefix, params = self._byte_read_messages[0xc170]
        ap_res = self._message(prefix, params)
        return jj_res, ch_res, ap_res
