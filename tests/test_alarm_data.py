from collections import defaultdict
import pytest
from typing import Dict, Iterator, List
from zilliandomizer.alarm_data import Alarm, alarm_data, to_vertical, to_horizontal, to_none
from zilliandomizer.patch import Patcher
from zilliandomizer.terrain_compressor import TerrainCompressor


def test_sets() -> None:
    """
    It would be easy to accidentally put a string
    as the iterable for the set constructor,
    instead of a list of strings.

    This is to make sure that doesn't happen.
    """
    for room in alarm_data.values():
        ids = {alarm.id for alarm in room}
        for alarm in room:
            assert len(alarm.id) > 1
            for other in alarm.disables:
                assert len(other) > 1
                assert other in ids
            for other in alarm.lessens:
                assert len(other) > 1
                assert other in ids


def test_unique_ids() -> None:
    for room in alarm_data.values():
        ids = {alarm.id for alarm in room}
        assert len(ids) == len(room)


def all_blocks(a: Alarm) -> Iterator[int]:
    """ across all variance """
    start_row, start_col = a.top_left
    for vary in range(0, a.vary + 1):
        row, col = start_row, start_col
        if a.vertical:
            col += vary
        else:
            row += vary
        block_index = row * 16 + col
        for _ in range(a.length):
            yield block_index
            if a.vertical:
                block_index += 16
            else:
                block_index += 1


def test_disable() -> None:
    for map_index, room in alarm_data.items():
        alarms_dict = {a.id: a for a in room}
        block_used_by: Dict[int, List[str]] = defaultdict(list)
        for a in room:
            for block in all_blocks(a):
                block_used_by[block].append(a.id)
        for a_ids in block_used_by.values():
            if len(a_ids) > 1:
                assert len(a_ids) == 2
                a_0 = alarms_dict[a_ids[0]]
                a_1 = alarms_dict[a_ids[1]]
                assert a_0.id in a_1.disables, f"room {map_index}: {a_0.id} not in disables of {a_1.id}"
                assert a_1.id in a_0.disables, f"room {map_index}: {a_1.id} not in disables of {a_0.id}"


@pytest.mark.usefixtures("fake_rom")
def test_can_change() -> None:
    p = Patcher()
    tc = TerrainCompressor(p.rom)
    for map_index, room in alarm_data.items():
        compressed = tc.get_room(map_index)
        uncompressed = TerrainCompressor.decompress(compressed)
        assert len(uncompressed) == 96
        for a in room:
            for block in all_blocks(a):
                assert block < 96, f"room {map_index}, alarm {a.id}"
                assert uncompressed[block] in to_none
                if a.vertical:
                    assert uncompressed[block] in to_vertical
                else:
                    assert uncompressed[block] in to_horizontal


def test_self_interaction() -> None:
    """
    make sure each alarm isn't disabling or lessening itself
    (This isn't a problem, but it indicates a mistake.)
    """
    for map_index, room in alarm_data.items():
        for a in room:
            assert a.id not in a.disables, f"room {map_index}: {a.id}"
            assert a.id not in a.lessens, f"room {map_index}: {a.id}"


# TODO: (different file test_alarms) Make sure it always chooses at least one
