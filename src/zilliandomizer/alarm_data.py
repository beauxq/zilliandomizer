from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Tuple, Generator


ALARM_ROOMS: List[int] = [
    0x0b, 0x0f,
    0x17,
    0x1a, 0x1c,
    0x21, 0x22, 0x24,
    0x2c, 0x2d, 0x2f,  # TODO: fix enemy entrance of 0x2c (Apple's room)
    0x33,
    0x39, 0x3b, 0x3d, 0x3f,
    0x41, 0x43, 0x44, 0x45,  # TODO: decide whether to change enemy entrance of 0x44
    0x4b, 0x4d, 0x4f,
    0x51, 0x52, 0x54,
    0x59, 0x5a, 0x5b,
    0x64, 0x66,
    0x69, 0x6e,
    0x72, 0x75,
    # no alarm lines in bottom 2 rows
]

# TODO: list of alarm rooms ordered by compressed length variance from lowest to highest
# to adjust while looking at how many bytes are used

fs = frozenset


@dataclass
class Alarm:
    """ can look at vertical and the number of blocks to see how expensive it is """
    id: str
    """ referenced by `disables` and `lessens` """
    vertical: bool
    top_left: Tuple[int, int]
    """" (row, col) """
    length: int
    """ how many blocks is this alarm sensor in """
    vanilla: bool
    """ this alarm is present in vanilla """
    disables: FrozenSet[str]
    """
    ids of other alarms in the room
    that can't be present at the same time as this one
    """
    lessens: FrozenSet[str]
    """
    ids of other alarms in the room
    that are less likely to be present at the same time as this one
    """

    def block_iter(self) -> Generator[int, None, None]:
        """ yield block_index """
        row, col = self.top_left
        block_index = row * 16 + col
        for _ in range(self.length):
            assert block_index < 96, f"{self.id} {block_index}"
            yield block_index
            if self.vertical:
                block_index += 16
            else:
                block_index += 1


to_vertical = {
    # ceiling
    0x3a: 0x40,
    0x40: 0x40,
    # space
    0x39: 0x3f,
    0x3f: 0x3f,
    0x42: 0x3f,
    # floor
    0x3b: 0x41,
    0x41: 0x41,
    0x43: 0x41,
}

to_horizontal = {
    # space
    0x39: 0x42,
    0x3f: 0x42,
    0x42: 0x42,
    # floor
    0x3b: 0x43,
    0x41: 0x43,
    0x43: 0x43,
}

to_none = {
    # ceiling
    0x3a: 0x3a,
    0x40: 0x3a,
    # space
    0x39: 0x39,
    0x3f: 0x39,
    0x42: 0x39,
    # floor
    0x3b: 0x3b,
    0x41: 0x3b,
    0x43: 0x3b,
}

alarm_data: Dict[int, List[Alarm]] = {
    0x0b: [
        Alarm("plat1top", True, (0, 5), 3,
              False, fs(), fs(["plat1bot", "hor-high", "hor-mid"])),
        Alarm("plat1bot", True, (3, 5), 3,
              True, fs(["hor-mid"]), fs(["plat1top", "hor-high"])),
        Alarm("hor-mid", False, (4, 1), 7,
              False, fs(["plat1bot"]), fs(["plat1top", "plat2top", "plat2bot"])),
        Alarm("hor-high", False, (3, 1), 3,
              False, fs(), fs(["plat1top", "plat1bot"])),
        Alarm("plat2top", True, (0, 9), 4,
              False, fs(), fs(["hor-mid", "plat2bot"])),
        Alarm("plat2bot", True, (4, 9), 2,
              False, fs(), fs(["hor-mid", "plat2top"])),
        Alarm("plat3top", True, (0, 12), 5,
              False, fs(), fs(["plat3bot"])),
        Alarm("plat3bot", True, (5, 13), 1,
              False, fs(), fs(["plat3top"]))
    ],
    0x0f: [
        Alarm("vTopLeft", True, (0, 3), 2,
              False, fs(), fs()),
        Alarm("vMidLeftOri", True, (2, 2), 2,
              True, fs(), fs(["vMidLeft"])),
        Alarm("vMidLeft", True, (2, 3), 2,
              False, fs(["hTopLeft"]), fs(["vMidLeftOri"])),
        Alarm("vTopMid", True, (0, 10), 2,
              False, fs(), fs(["hTopLeft", "hMidRight"])),
        Alarm("vBotMid", True, (4, 9), 2,
              False, fs(["hBotRight"]), fs()),
        Alarm("vMidRight", True, (3, 12), 2,
              False, fs(["hBotRight", "hMidRight"]), fs()),
        Alarm("vBotRight", True, (4, 14), 2,
              False, fs(), fs(["hBotRight"])),
        Alarm("hTopLeft", False, (2, 3), 7,
              False, fs(["vMidLeft"]), fs(["vMidLeftOri", "hBotLeft", "vTopMid"])),
        Alarm("hBotLeft", False, (4, 3), 3,
              False, fs(), fs(["hTopLeft", "vTopMid", "hMidRight", "hBotRight"])),
        Alarm("hMidRight", False, (3, 12), 3,
              False, fs(["vMidRight"]), fs(["hTopLeft", "vTopMid", "hBotLeft", "hBotRight"])),
        Alarm("hBotRight", False, (4, 9), 5,
              False, fs(["vBotMid", "vMidRight"]), fs(["hTopLeft", "vTopMid", "hBotLeft", "hMidRight"]))
    ],
    0x17: [
        Alarm("v-top-left", True, (0, 5), 2, False, fs(), fs(["h-mid", "h-bot"])),
        Alarm("v-top-right", True, (0, 11), 2, True, fs(), fs(["h-mid", "h-bot"])),
        Alarm("v-left", True, (2, 4), 2, False, fs(), fs(["h-bot"])),
        Alarm("v-right", True, (2, 12), 3, False, fs(["h-bot"]), fs(["v-bot-right"])),
        Alarm("v-bot-left", True, (4, 7), 2, False, fs(), fs()),
        Alarm("v-bot-right", True, (5, 13), 1, False, fs(), fs(["v-right", "h-bot"])),
        Alarm("h-mid", False, (2, 6), 3, False, fs(), fs(["h-bot", "v-top-left", "v-top-right"])),
        Alarm("h-bot", False, (4, 11), 3, False, fs(["v-right"]), fs(["v-bot-right"]))
    ],
    0x1a: [
        Alarm("v-top-left", True, (0, 6), 2, False, fs(), fs(["h-top", "v-mid-left"])),
        Alarm("v-top-mid", True, (0, 11), 3, False, fs(["h-top"]), fs(["v-mid", "v-bot", "v-mid-left"])),
        Alarm("v-top-right", True, (0, 13), 2, False, fs(), fs(["h-top", "v-mid-left"])),
        Alarm("v-mid-left", True, (2, 7), 2, False, fs(), fs()),  # lessened in all others because blocks computer
        Alarm("v-mid", True, (3, 11), 2, False, fs(), fs(["v-top-mid", "v-bot", "v-mid-left"])),
        Alarm("v-mid-right", True, (2, 13), 2, True, fs(), fs(["v-mid-left"])),
        Alarm("v-bot-left", True, (4, 3), 2, False, fs(["h-left"]), fs(["v-mid-left"])),
        Alarm("v-bot", True, (5, 12), 1, False, fs(), fs(["v-top-mid", "v-mid", "v-mid-left"])),
        Alarm("h-top", False, (2, 8), 5, False, fs(["v-top-mid"]), fs(["v-top-left", "v-top-right", "v-mid-left"])),
        Alarm("h-left", False, (4, 3), 2, False, fs(["v-bot-left"]), fs(["v-mid-left"])),
    ],
    0x1c: [
        Alarm("v-top-1", True, (0, 5), 3, False, fs(["h-top"]), fs(["v-mid-1", "v-bot-1", "h-mid-1"])),
        Alarm("v-top-2", True, (0, 8), 2, False, fs(["h-top"]), fs(["v-mid-2", "v-bot-2", "h-mid-2"])),
        Alarm("v-top-3", True, (0, 10), 3, False, fs(["h-top"]), fs(["v-bot-3"])),
        Alarm("v-top-4", True, (0, 14), 2, False, fs(["h-top"]), fs()),
        Alarm("v-mid-1", True, (3, 5), 2, False, fs(["h-mid-1"]), fs(["v-top-1", "v-bot-1"])),
        Alarm("v-mid-2", True, (2, 8), 2, True, fs(["h-mid-2"]), fs(["v-top-2", "v-bot-2", "h-top"])),
        #      v-mid-3 is not missing, it's just combined with v-bot-3
        Alarm("v-mid-4", True, (2, 14), 2, False, fs(), fs(["v-bot-3"])),
        Alarm("v-bot-1", True, (5, 6), 1, False, fs(), fs(["v-top-1", "v-mid-1", "h-mid-1"])),
        Alarm("v-bot-2", True, (4, 7), 2, False, fs(), fs(["v-top-2", "h-top", "v-mid-2", "h-mid-2"])),
        Alarm("v-bot-3", True, (3, 11), 3, False, fs(["h-mid-3"]), fs(["v-mid-4"])),
        Alarm("h-top", False, (1, 1), 14, False, fs(["v-top-1", "v-top-2", "v-top-3", "v-top-4"]),
              fs(["v-mid-2", "h-mid-2", "v-bot-2"])),
        Alarm("h-mid-1", False, (4, 2), 5, False, fs(["v-mid-1"]), fs(["v-top-1", "v-bot-1", "h-mid-3"])),
        Alarm("h-mid-2", False, (3, 6), 4, False, fs(["v-mid-2"]), fs(["v-top-2", "h-top", "v-bot-2"])),
        Alarm("h-mid-3", False, (4, 9), 5, False, fs(["v-bot-3"]), fs(["h-mid-1"])),
    ],
    0x21: [
        Alarm("v-mid-left", True, (3, 3), 2, False, fs(), fs(["v-bot-left", "h-bot"])),
        Alarm("v-bot-left", True, (5, 3), 1, False, fs(["h-bot"]), fs(["v-mid-left"])),
        Alarm("v-top-right", True, (0, 13), 2, False, fs(), fs(["h-top", "h-mid"])),
        Alarm("v-mid-right", True, (4, 13), 1, False, fs(), fs(["v-bot-right", "h-bot"])),
        Alarm("v-bot-right", True, (5, 13), 1, False, fs(), fs(["v-mid-right", "h-bot"])),
        Alarm("h-top", False, (2, 9), 4, False, fs(), fs(["v-top-right", "h-mid"])),
        Alarm("h-mid", False, (3, 7), 6, False, fs(), fs(["v-top-right", "h-top"])),
        Alarm("h-bot", False, (5, 3), 9, True, fs(["v-bot-left"]),
              fs(["v-mid-left", "v-mid-right", "v-bot-right"])),
    ],
    0x22: [
        Alarm("v-top-left", True, (0, 2), 2, False, fs(), fs()),
        Alarm("v-mid-left", True, (3, 5), 1, False, fs(["h-mid"]), fs(["v-top-mid", "h-left"])),
        Alarm("v-top-mid", True, (0, 4), 3, False, fs(["h-top"]), fs(["v-mid-left", "h-left"])),
        Alarm("v-top-right", True, (0, 9), 2, False, fs(), fs()),
        Alarm("v-mid-right", True, (3, 12), 1, False, fs(["h-right"]), fs()),
        Alarm("v-bot", True, (4, 9), 2, False, fs(), fs()),
        Alarm("h-top", False, (2, 2), 4, False, fs(["v-top-mid"]), fs()),
        Alarm("h-left", False, (3, 1), 3, False, fs(),
              fs(["v-top-mid", "v-mid-left", "h-mid", "h-right"])),
        Alarm("h-mid", False, (3, 5), 6, True, fs(["v-mid-left"]),
              fs(["h-left", "h-right", "v-top-mid", "v-mid-left", "v-mid-right"])),
        Alarm("h-right", False, (3, 12), 3, False, fs(["v-mid-right"]), fs(["h-left", "h-mid"])),
    ],
}
""" map_index: list of possible `Alarm` in room """
