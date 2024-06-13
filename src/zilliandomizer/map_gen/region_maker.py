from collections import deque
from typing import Dict, List, Set

from zilliandomizer.logic_components.region_data import MapBuilder
from zilliandomizer.map_gen.base_maker import BaseMaker, Node

_exits = (Node(1, 0), Node(3, 0), Node(4, 0))

_no_doors: Set[str] = {
    "between_blue_red",  # start
    "r05c5",  # no computer  # TODO: implement changing which rooms have computers and doors?
    "r05c6",  # start hall
    "r06c5",  # hall
    "r07c4",  # no computer and no canisters
    "r09c6",  # hall
    "r09c7",  # no computer and no canisters
}


def make_red_right_bm(bm: BaseMaker, mb: MapBuilder) -> None:
    assert bm.height == 5 and bm.width == 5, f"{bm.height=} {bm.width=}"

    divided_rooms: List[str] = []
    parents: Dict[str, str] = {"r05c6": "between_blue_red"}
    done: Set[Node] = set()
    q = deque([Node(0, 3)])

    while len(q):
        node = q.popleft()
        if node in done:
            continue
        done.add(node)

        row, col = node
        map_row = row + 5
        map_col = col + 3
        region_name_base = f"r0{map_row}c{map_col}"
        adjs = list(bm.adjs(node))
        dead_end = (len(adjs) == 1) and (node not in _exits)
        computer_opens_door = region_name_base not in _no_doors
        divided = dead_end and computer_opens_door
        parent = parents[region_name_base]

        if divided:
            mb.split(map_row, map_col, {
                "enter": [loc_name for loc_name in mb.reg_name_to_loc_name[region_name_base]],
                "locked": [],
            }, True)
            enter_name = region_name_base + "enter"
            locked_name = region_name_base + "locked"
            divided_rooms.append(region_name_base)
            if parent in _no_doors:
                mb.r[parent].to(mb.r[enter_name])
            else:  # parent has door
                mb.r[parent].to(mb.r[enter_name], door=True)
            mb.r[enter_name].to(mb.r[locked_name], door=True)
        else:  # not divided
            mb.room(map_row, map_col, len(mb.reg_name_to_loc_name[region_name_base]), computer_opens_door)
            if parent in _no_doors:
                mb.r[parent].to(mb.r[region_name_base])
            else:  # parent has door
                mb.r[parent].to(mb.r[region_name_base], door=True)

        for adj in adjs:
            if adj not in done:
                row, col = adj
                map_row = row + 5
                map_col = col + 3
                child_name = f"r0{map_row}c{map_col}"
                parents[child_name] = region_name_base
                q.append(adj)

    mb.hall("red_elevator")

    mb.r["r09c3"].to(mb.r["red_elevator"], door=True)
    mb.r["r08c3"].to(mb.r["red_elevator"], door=True)
    mb.r["r06c3"].to(mb.r["red_elevator"], door=True)
