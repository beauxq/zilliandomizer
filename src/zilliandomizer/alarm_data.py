from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Tuple


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
    blocks: Dict[Tuple[int, int], Tuple[int, int]]
    """ (row, col): (off, on) """
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


alarm_data: Dict[int, List[Alarm]] = {
    0x0b: [
        Alarm("plat1top", True, {
            (0, 5): (0x3a, 0x40),
            (1, 5): (0x39, 0x3f),
            (2, 5): (0x3b, 0x41),
        }, False, fs(), fs(["plat1bot", "hor-high", "hor-mid"])),
        Alarm("plat1bot", True, {
            (3, 5): (0x3a, 0x40),
            (4, 5): (0x39, 0x3f),
            (5, 5): (0x3b, 0x41),
        }, True, fs(["hor-mid"]), fs(["plat1top", "hor-high"])),
        Alarm("hor-mid", False, {
            (4, 1): (0x39, 0x42),
            (4, 2): (0x39, 0x42),
            (4, 3): (0x39, 0x42),
            (4, 4): (0x39, 0x42),
            (4, 5): (0x39, 0x42),
            (4, 6): (0x39, 0x42),
            (4, 7): (0x39, 0x42),
        }, False, fs(["plat1bot"]), fs(["plat1top", "plat2top", "plat2bot"])),
        Alarm("hor-high", False, {
            (3, 1): (0x39, 0x42),
            (3, 2): (0x39, 0x42),
            (3, 3): (0x39, 0x42),
        }, False, fs(), fs(["plat1top", "plat1bot"])),
        Alarm("plat2top", True, {
            (0, 9): (0x3a, 0x40),
            (1, 9): (0x39, 0x3f),
            (2, 9): (0x39, 0x3f),
            (3, 9): (0x3b, 0x41),
        }, False, fs(), fs(["hor-mid", "plat2bot"])),
        Alarm("plat2bot", True, {
            (4, 9): (0x3a, 0x40),
            (5, 9): (0x3b, 0x41),
        }, False, fs(), fs(["hor-mid", "plat2top"])),
        Alarm("plat3top", True, {
            (0, 12): (0x3a, 0x40),
            (1, 12): (0x39, 0x3f),
            (2, 12): (0x39, 0x3f),
            (3, 12): (0x39, 0x3f),
            (4, 12): (0x3b, 0x41),
        }, False, fs(), fs(["plat3bot"])),
        Alarm("plat3bot", True, {
            (5, 13): (0x3b, 0x41),
        }, False, fs(), fs(["plat3top"]))
    ]
}
""" map_index: list of possible `Alarm` in room """
