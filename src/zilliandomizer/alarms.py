from random import random
from secrets import choice
from typing import Dict, List, Literal, Set
from zilliandomizer.alarm_data import ALARM_ROOMS, Alarm, alarm_data, to_horizontal, to_vertical, to_none
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
        prob_mult = (map_index // 8) ** 0.5 * 0.1
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

            prob *= prob_mult
            # TODO: which rooms should have more/fewer alarm lines
            # change probability according to that

            # TODO: skill level could disable lessened and
            # change probability of more alarms

        # testing
        # chosen = {a.id for a in this_room if not a.vertical}
        # chosen = set()

        print(f"chosen: {chosen}")
        _bytes = TerrainCompressor.decompress(self.tc.get_room(map_index))
        assert len(_bytes) == 96

        # gather all the blocks involved
        blocks: Dict[int, Literal["v", "h", "n"]] = {}  # key block_index
        for a in this_room:
            for block_index in a.block_iter():
                # verify
                if a.vanilla:
                    if a.vertical:
                        assert _bytes[block_index] == to_vertical[_bytes[block_index]]
                    else:  # horizontal
                        assert _bytes[block_index] == to_horizontal[_bytes[block_index]]
                # else not vanilla - can't verify because it might cross a vanilla

                if a.id in chosen:
                    blocks[block_index] = "v" if a.vertical else "h"
                else:
                    if block_index not in blocks:
                        blocks[block_index] = "n"

        # set bytes
        for block_index in blocks:
            block = blocks[block_index]
            to = to_vertical if block == "v" \
                else (to_horizontal if block == "h" else to_none)
            _bytes[block_index] = to[_bytes[block_index]]

        space = self.tc.set_room(map_index, TerrainCompressor.compress(_bytes))
        print(f"terrain free space {space}")
