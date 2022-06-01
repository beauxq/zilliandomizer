import socket
import time
from typing import Dict, List, Tuple, ClassVar, Literal, Union, Iterable

from zilliandomizer.low_resources import ram_info

OP = Literal["READ_CORE_RAM", "WRITE_CORE_RAM"]
DOOR_BYTE_COUNT = 62
CANISTER_ROOM_COUNT = 74

# read messages for single bytes will be cached so no creating message each time
_common_byte_reads = [
    ram_info.current_scene_c11f,
    ram_info.current_hp_c143,
    ram_info.jj_status_c150,
    ram_info.jj_hp_c153,
    ram_info.champ_status_c160,
    ram_info.champ_hp_c163,
    ram_info.apple_status_c170,
    ram_info.apple_hp_c173,
    ram_info.cutscene_selector_c183,
    ram_info.external_item_trigger_c2ea,
    ram_info.guns_c2ec,
    ram_info.opas_c2ee,
    ram_info.game_started_flag_c300,
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
        self.sock.settimeout(0.125)

        self._build_cached_messages()

    def _build_cached_messages(self) -> None:
        # door data is in 62 bytes starting from d600
        self._door_read_message = self._build_message(RAInterface.READ,
                                                      ram_info.door_state_d600,
                                                      DOOR_BYTE_COUNT)
        # canister data is in 2 * 74 bytes starting from d700
        self._canister_read_message = self._build_message(RAInterface.READ,
                                                          ram_info.canister_state_d700,
                                                          2 * CANISTER_ROOM_COUNT)

        self._byte_read_messages = {}
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
        write = prefix.startswith(b'W')
        attempt_count = 0
        message = prefix + params
        # gun_message = message.find(b" 0a") != -1
        # t = 0.0
        while True:
            # if gun_message:
            #     print(f"rai message {message}")
            #     t = time.perf_counter()
            self.sock.sendto(message, RAInterface.RETROARCH)
            # if gun_message:
            #     t1 = time.perf_counter()
            #     print(f"sendto time {t1 - t}")
            if write:
                break
            # else need response
            try:
                # if gun_message:
                #     t = time.perf_counter()
                res = self.sock.recv(1024)
                # if gun_message:
                #     t1 = time.perf_counter()
                #     print(f" got res {res}  recv time {t1 - t}")
            except socket.timeout:
                # if gun_message:
                #     t1 = time.perf_counter()
                #     print(f"timed out  time {t1 - t}")
                res = b''

            # if gun_message:
            #     print(f" res later {res}")
            if res.startswith(prefix):
                break
            attempt_count += 1
            if attempt_count >= 3:
                res = b''
                break
            time.sleep(0.0625)

        if res == b'':
            return res

        split = res.strip().split(b' ')
        try:
            return bytes(int(x, 16) for x in split[2:])
        except ValueError:
            return b''

    def write(self, addr: int, b: Union[bytes, List[int]]) -> None:
        prefix, params = self._build_message(RAInterface.WRITE, addr, b)
        self._message(prefix, params)
        # print(f"write response: {list(res)}")

    def read(self, addr: int, n_bytes: int = 1) -> bytes:
        """
        this takes extra time to build the message,
        so don't use it for doors and canisters

        single byte read messages are cached
        """
        if n_bytes == 1 and addr in self._byte_read_messages:
            prefix, params = self._byte_read_messages[addr]
        else:
            prefix, params = self._build_message(RAInterface.READ, addr, n_bytes)
            if n_bytes == 1:
                self._byte_read_messages[addr] = (prefix, params)
        res = self._message(prefix, params)
        # print(f"read {hex(addr)} response: {list(res)}")
        return res

    def read_doors(self) -> bytes:
        """ d600 """
        prefix, params = self._door_read_message
        res = self._message(prefix, params)
        # print(f"read doors response: {list(res)}")
        return res

    def read_canisters(self) -> bytes:
        """ d700 """
        prefix, params = self._canister_read_message
        res = self._message(prefix, params)
        # print(f"read canisters response: {list(res)}")
        return res

    def read_char_status(self) -> Tuple[bytes, bytes, bytes]:
        """ return jj c150, ch c160, ap c170 """
        prefix, params = self._byte_read_messages[ram_info.jj_status_c150]
        jj_res = self._message(prefix, params)
        prefix, params = self._byte_read_messages[ram_info.champ_status_c160]
        ch_res = self._message(prefix, params)
        prefix, params = self._byte_read_messages[ram_info.apple_status_c170]
        ap_res = self._message(prefix, params)
        return jj_res, ch_res, ap_res
