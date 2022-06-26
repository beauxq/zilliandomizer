import asyncio
import bisect
from dataclasses import dataclass
from typing import Dict, List, Tuple, ClassVar, Literal, Union, Iterable, Optional, overload

from zilliandomizer.low_resources import ram_info
from zilliandomizer.zri import asyncudp

OP = Literal["READ_CORE_RAM", "WRITE_CORE_RAM"]
DOOR_BYTE_COUNT = 62
CANISTER_ROOM_COUNT = 74

RangeName = Literal["basic", "new_ram", "door_can"]

# important that this is sorted by address
_range_reads: Dict[RangeName, Tuple[int, int]] = {
    "basic": (
        ram_info.current_scene_c11f,
        ram_info.map_current_index_c198 + 1
    ),
    "new_ram": (
        ram_info.external_item_trigger_c2ea,
        ram_info.opas_c2ee + 1
    ),
    "door_can": (
        ram_info.door_state_d600,
        ram_info.canister_state_d700 + CANISTER_ROOM_COUNT * 2
    )
}
""" name: (first address, last address + 1) """


def bcd_decode(x: int) -> int:
    """ from bcd hex to int """
    lo_n = x & 0x0f
    hi_n = x >> 4
    return hi_n * 10 + lo_n


def bcd_encode(x: int) -> int:
    """ from int to bcd hex (2 decimal digits only) """
    lo = x % 10
    hi = x // 10
    return (hi << 4) | lo


@dataclass
class RamData:
    data: List[bytes]
    base_addr: List[int]
    """ sorted list of the beginning of each range """

    @overload
    def __getitem__(self, addr: int) -> int: ...
    @overload
    def __getitem__(self, addr: slice) -> bytes: ...

    def __getitem__(self, addr: Union[int, slice]) -> Union[int, bytes]:
        slc = slice(addr, addr + 1, 1) if isinstance(addr, int) else addr
        chunk_index = bisect.bisect_right(self.base_addr, slc.start) - 1
        if chunk_index == -1:
            raise IndexError(f"{hex(slc.start)} below bottom range ({self.base_addr[0]})")

        chunk_length = len(self.data[chunk_index])
        chunk_start = self.base_addr[chunk_index]
        chunk_stop = chunk_start + chunk_length

        if slc.start >= chunk_stop:
            # out of range

            def range_str(start: int, stop: int) -> str:
                return f"[{hex(start)}, {hex(stop)})"

            this_range_str = range_str(chunk_start, chunk_stop)
            if chunk_index == len(self.base_addr) - 1:
                # last range
                message = f"above top range {this_range_str}"
            else:  # between ranges
                next_start = self.base_addr[chunk_index + 1]
                next_stop = next_start + len(self.data[chunk_index + 1])
                message = f"between {this_range_str} and {range_str(next_start, next_stop)}"
            raise IndexError(f"{hex(slc.start)} {message}")

        local_start = slc.start - chunk_start
        local_stop = slc.stop - chunk_start

        result = self.data[chunk_index][local_start: local_stop: slc.step]

        if isinstance(addr, int):
            return result[0]
        return result

    def all_present(self) -> bool:
        return all(len(each_data) for each_data in self.data)

    def in_win(self) -> bool:
        scene_selector = self[ram_info.cutscene_selector_c183]
        current_scene = self[ram_info.current_scene_c11f]

        # TODO: decide: currently end credits and curtain call are not
        # possible to detect because they're not in in_game set
        # should I consider end credits and curtain call in game?
        # or is it enough to just detect the 3 cutscenes before curtain call?
        #                   end credits               curtain call
        return (current_scene == 0x8d) or (current_scene == 0x8e) or (
            #               cutscene          oh great, ...., end text
            (current_scene == 0x86) and (scene_selector in (1, 8, 9))
        )

    def in_game_play(self) -> bool:
        """ in the state where can move/jump/shoot """
        return self[ram_info.current_scene_c11f] == 0x8b

    def current_hp(self) -> int:
        c143 = self[ram_info.current_hp_c143]
        # binary coded decimal / 10
        return bcd_decode(c143) * 10

    def check_item_trigger(self) -> bool:
        """ True if ram value 0 (available for sending an item) """
        return self[ram_info.external_item_trigger_c2ea] == 0

    def safe_to_write(self) -> bool:
        """ in game play and current hp > 0 and item trigger ready """
        return self.in_game_play() and \
            bool(self.current_hp()) and \
            self.check_item_trigger()


class RAInterface:
    sock: Optional[asyncudp.Socket]

    _read_messages: Dict[RangeName, Tuple[bytes, bytes]]

    RETROARCH: ClassVar[asyncudp.Address] = ("127.0.0.1", 55355)
    SMS_RAM_OFFSET: ClassVar[int] = 0xc000
    READ: ClassVar[OP] = "READ_CORE_RAM"
    WRITE: ClassVar[OP] = "WRITE_CORE_RAM"

    def __init__(self) -> None:
        self.sock = None
        self.lock = asyncio.Lock()

        self._read_messages = {
            name: RAInterface._build_message(RAInterface.READ, r[0], r[1] - r[0])
            for name, r in _range_reads.items()
        }

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

    async def _message(self, prefix: bytes, params: bytes) -> bytes:
        """ parameters from `_build_message` """
        res = b''
        write = prefix.startswith(b'W')
        attempt_count = 0
        message = prefix + params
        # gun_message = message.find(b" 0a") != -1
        # t = 0.0
        if not self.sock:
            self.sock = await asyncudp.create_socket(remote_addr=RAInterface.RETROARCH)
        async with self.lock:
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
                    res, _ = await self.sock.recvfrom()
                    # if gun_message:
                    #     t1 = time.perf_counter()
                    #     print(f" got res {res}  recv time {t1 - t}")
                except (asyncudp.ClosedError, ConnectionRefusedError) as e:
                    # if gun_message:
                    #     t1 = time.perf_counter()
                    #     print(f"timed out  time {t1 - t}")
                    print(e)
                    res = b''

                # if gun_message:
                #     print(f" res later {res}")
                if res.startswith(prefix):
                    break
                attempt_count += 1
                if attempt_count >= 3:
                    res = b''
                    break
                await asyncio.sleep(0.0625)

        if res == b'':
            return res

        split = res.strip().split(b' ')
        try:
            return bytes(int(x, 16) for x in split[2:])
        except ValueError:
            return b''

    async def write(self, addr: int, b: Union[bytes, List[int]]) -> None:
        prefix, params = self._build_message(RAInterface.WRITE, addr, b)
        await self._message(prefix, params)
        # print(f"write response: {list(res)}")

    async def read(self) -> RamData:
        """ returns the ram that I have registered to read """
        data_tr: List[bytes] = []
        bases_tr: List[int] = []
        for name in _range_reads:
            prefix, params = self._read_messages[name]
            res = await self._message(prefix, params)
            data_tr.append(res)
            bases_tr.append(_range_reads[name][0])
        return RamData(data_tr, bases_tr)
