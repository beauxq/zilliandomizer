from collections import deque
from typing import Dict, List, Set

from zilliandomizer.logic_components.region_data import MapBuilder
from zilliandomizer.map_gen.base_maker import BaseMaker, Node
from zilliandomizer.map_gen.map_data import pc_no_doors, red_right_no_doors

_red_exits = (Node(1, 0), Node(3, 0), Node(4, 0))


def make_red_right_bm(bm: BaseMaker, mb: MapBuilder) -> None:
    assert bm.height == 5 and bm.width == 5, f"{bm.height=} {bm.width=}"
    node_no_doors = red_right_no_doors
    pre_entrance_region = "between_blue_red"
    start_node = Node(0, 3)
    exits = _red_exits

    def reg_name(node: Node) -> str:
        row, col = node
        map_row = row + bm.row_offset
        map_col = col + bm.col_offset
        return f"r{map_row:02}c{map_col}"

    no_doors = set(reg_name(node) for node in node_no_doors)
    no_doors.add(pre_entrance_region)

    entrance_name = reg_name(start_node)

    divided_rooms: List[str] = []
    parents: Dict[str, str] = {entrance_name: pre_entrance_region}
    done: Set[Node] = set()
    q = deque([start_node])

    while len(q):
        node = q.popleft()
        if node in done:
            continue
        done.add(node)

        row, col = node
        map_row = row + bm.row_offset
        map_col = col + bm.col_offset
        region_name_base = reg_name(node)
        adjs = list(bm.adjs(node))
        dead_end = (len(adjs) == 1) and (node not in exits)
        computer_opens_door = region_name_base not in no_doors
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
                child_name = reg_name(adj)
                parents[child_name] = region_name_base
                q.append(adj)

    mb.hall("red_elevator")

    mb.r["r09c3"].to(mb.r["red_elevator"], door=True)
    mb.r["r08c3"].to(mb.r["red_elevator"], door=True)
    mb.r["r06c3"].to(mb.r["red_elevator"], door=True)


_pc_exits = {Node(0, 5)}


def make_paperclip_bm(bm: BaseMaker, mb: MapBuilder) -> None:
    assert bm.height == 7 and bm.width == 8, f"{bm.height=} {bm.width=}"
    node_no_doors = pc_no_doors
    pre_entrance_region = "big_elevator"
    start_node = Node(0, 0)
    exits = _pc_exits

    def reg_name(node: Node) -> str:
        row, col = node
        map_row = row + bm.row_offset
        map_col = col + bm.col_offset
        return f"r{map_row:02}c{map_col}"

    no_doors = set(reg_name(node) for node in node_no_doors)
    no_doors.add(pre_entrance_region)

    entrance_name = reg_name(start_node)

    divided_rooms: List[str] = []
    parents: Dict[str, str] = {entrance_name: pre_entrance_region}
    done: Set[Node] = set()
    q = deque([start_node])

    while len(q):
        node = q.popleft()
        if node in done:
            continue
        done.add(node)

        row, col = node
        map_row = row + bm.row_offset
        map_col = col + bm.col_offset
        region_name_base = reg_name(node)
        adjs = list(bm.adjs(node))
        dead_end = (len(adjs) == 1) and (node not in exits)
        computer_opens_door = region_name_base not in no_doors
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
                child_name = reg_name(adj)
                parents[child_name] = region_name_base
                q.append(adj)

    assert "r10c5" in mb.r
