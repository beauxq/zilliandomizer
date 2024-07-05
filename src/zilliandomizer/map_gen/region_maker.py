from collections import deque
from typing import Dict, List, Set

from zilliandomizer.logic_components.region_data import MapBuilder
from zilliandomizer.map_gen.base_maker import BaseMaker, Node

_red_exits = (Node(1, 0), Node(3, 0), Node(4, 0))

_red_no_doors: Set[str] = {
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
        map_row = row + bm.row_offset
        map_col = col + bm.col_offset
        region_name_base = f"r0{map_row}c{map_col}"  # map row always < 10
        adjs = list(bm.adjs(node))
        dead_end = (len(adjs) == 1) and (node not in _red_exits)
        computer_opens_door = region_name_base not in _red_no_doors
        divided = dead_end and computer_opens_door
        parent = parents[region_name_base]

        if divided:
            locations_in_room = [loc_name for loc_name in mb.reg_name_to_loc_name[region_name_base]]
            # assert locations_in_room[-1][6:8] == "18", f"locked location should be top row {locations_in_room}"
            # ^ This assert doesn't work because of the double pass of `Randomizer.reset`
            mb.split(map_row, map_col, {
                "enter": locations_in_room[:-1],
                "locked": [locations_in_room[-1]],
            }, True)
            enter_name = region_name_base + "enter"
            locked_name = region_name_base + "locked"
            divided_rooms.append(region_name_base)
            if parent in _red_no_doors:
                mb.r[parent].to(mb.r[enter_name])
            else:  # parent has door
                mb.r[parent].to(mb.r[enter_name], door=True)
            mb.r[enter_name].to(mb.r[locked_name], door=True)
        else:  # not divided
            mb.room(map_row, map_col, len(mb.reg_name_to_loc_name[region_name_base]), computer_opens_door)
            if parent in _red_no_doors:
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


_pc_exits = {Node(0, 5)}

# TODO: get rid of copy paste of door decider - ssot
_pc_node_no_doors = {
    Node(0, 0), Node(1, 0), Node(2, 0), Node(3, 0), Node(4, 0), Node(5, 0), Node(6, 0),  # left
    Node(0, 1), Node(1, 1), Node(2, 1),             Node(4, 1), Node(5, 1), Node(6, 1),  # rooms and halls
    Node(0, 7), Node(1, 7), Node(2, 7), Node(3, 7), Node(4, 7), Node(5, 7), Node(6, 7),  # right
    Node(0, 5), Node(0, 6),  # main computer
    Node(6, 3), Node(6, 4), Node(6, 5), Node(6, 6),  # bottom hall
}

_pc_no_doors: Set[str] = {
    "big_elevator",
}


def make_paperclip_bm(bm: BaseMaker, mb: MapBuilder) -> None:
    assert bm.height == 7 and bm.width == 8, f"{bm.height=} {bm.width=}"

    def reg_name(node: Node) -> str:
        row, col = node
        map_row = row + bm.row_offset
        map_col = col + bm.col_offset
        return f"r{map_row}c{map_col}"

    no_doors = set(reg_name(node) for node in _pc_node_no_doors)
    no_doors.add("big_elevator")

    divided_rooms: List[str] = []
    parents: Dict[str, str] = {"r10c0": "big_elevator"}
    done: Set[Node] = set()
    q = deque([Node(0, 0)])

    while len(q):
        node = q.popleft()
        if node in done:
            continue
        done.add(node)

        row, col = node
        map_row = row + bm.row_offset
        map_col = col + bm.col_offset
        region_name_base = f"r{map_row}c{map_col}"  # map row always >= 10
        adjs = list(bm.adjs(node))
        dead_end = (len(adjs) == 1) and (node not in _pc_exits)
        computer_opens_door = region_name_base not in no_doors
        divided = dead_end and computer_opens_door
        parent = parents[region_name_base]

        print(f"making room {region_name_base}")
        if divided:
            locations_in_room = [loc_name for loc_name in mb.reg_name_to_loc_name[region_name_base]]
            # assert locations_in_room[-1][6:8] == "18", f"locked location should be top row {locations_in_room}"
            # ^ This assert doesn't work because of the double pass of `Randomizer.reset`
            mb.split(map_row, map_col, {
                "enter": locations_in_room[:-1],
                "locked": [locations_in_room[-1]],
            }, True)
            enter_name = region_name_base + "enter"
            locked_name = region_name_base + "locked"
            divided_rooms.append(region_name_base)
            if parent in no_doors:
                mb.r[parent].to(mb.r[enter_name])
            else:  # parent has door
                mb.r[parent].to(mb.r[enter_name], door=True)
            mb.r[enter_name].to(mb.r[locked_name], door=True)
        else:  # not divided
            mb.room(map_row, map_col, len(mb.reg_name_to_loc_name[region_name_base]), computer_opens_door)
            if parent in no_doors:
                mb.r[parent].to(mb.r[region_name_base])
            else:  # parent has door
                mb.r[parent].to(mb.r[region_name_base], door=True)

        for adj in adjs:
            if adj not in done:
                row, col = adj
                map_row = row + bm.row_offset
                map_col = col + bm.col_offset
                child_name = f"r{map_row}c{map_col}"
                parents[child_name] = region_name_base
                q.append(adj)

    assert "r10c5" in mb.r
