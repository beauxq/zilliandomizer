from random import random
from secrets import choice
from typing import List, Set
from zilliandomizer.alarm_data import ALARM_ROOMS, Alarm, alarm_data
from zilliandomizer.terrain_compressor import TerrainCompressor


class Alarms:
    tc: TerrainCompressor

    def __init__(self, tc: TerrainCompressor) -> None:
        self.tc = tc

    def choose_all(self) -> None:
        for map_index in ALARM_ROOMS:
            if map_index in alarm_data:
                self._choose_for_room(map_index)

    def _choose_for_room(self, map_index: int) -> None:
        this_room = alarm_data[map_index]
        chosen: Set[str] = set()
        eliminated: Set[str] = set()
        """ chosen already, or conflicting with chosen """
        lessened: Set[str] = set()
        prob = 1.0
        while (len(eliminated) < len(this_room)) and random() < prob:
            choices: List[Alarm] = [a for a in this_room if a.id not in eliminated]
            n = len(choices)  # not changing duration iteration
            for i in range(n):
                if choices[i].id not in lessened:
                    choices.append(choices[i])
                    choices.append(choices[i])

            this_choice = choice(choices)
            chosen.add(this_choice.id)
            eliminated.update(this_choice.disables)
            eliminated.add(this_choice.id)
            lessened.update(this_choice.lessens)

            prob *= 0.5
            # TODO: which rooms should have more/fewer alarm lines
            # change probability according to that

        print(f"chosen: {chosen}")
        _bytes = TerrainCompressor.decompress(self.tc.get_room(map_index))
        for a in this_room:
            for loc in a.blocks:
                row, col = loc
                off, on = a.blocks[loc]
                block_index = row * 16 + col
                if a.vanilla:
                    assert _bytes[block_index] == on
                    # can't assert off for non-vanilla because of crossing lines
                _bytes[block_index] = (on if a.id in chosen else off)
        space = self.tc.set_room(map_index, TerrainCompressor.compress(_bytes))
        print(f"space {space}")
