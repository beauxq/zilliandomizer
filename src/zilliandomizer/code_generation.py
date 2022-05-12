"""
I used code to generate python code for location and region data.
Most of it is outdated and will not generate the correct format for the current code.
"""

from typing import List, Dict, Set
from zilliandomizer.logic_components.items import KEYWORD, NORMAL, RESCUE, MAIN
from zilliandomizer.utils import make_loc_name
from zilliandomizer.patch import Patcher  # for access to rom data
from zilliandomizer.logic_components.location_data import make_locations


def make_location_code() -> None:
    p = Patcher()
    locs: List[str] = []
    room_no = 0
    for room in p.get_item_rooms():
        for item in p.get_items(room):
            if item[0] in {KEYWORD, NORMAL, RESCUE, MAIN}:
                name = make_loc_name(room_no, item)
                if name.startswith("x"):
                    name = "0" + name[1:]
                locs.append(f'    "{name}": Location("{name}", Req(gun={item[7] + 1})),')
        room_no += 1
    for loc in locs:
        print(loc)


def region_code_maker() -> None:
    """ outdated way of creating code for `region_data` """
    locations = make_locations()

    rooms: Dict[str, Set[str]] = {}
    for key in locations:
        room = key[:5]
        if not (room in rooms):
            rooms[room] = set()
        rooms[room].add(key)

    # can't print these as we go because neighbor object might not be made yet
    connections: List[str] = []

    for room in rooms:
        split = room.split('c')
        col = int(split[1])
        row = int(split[0][1:])

        print()
        print(f'{room} = Region("{room}")')
        for loc in rooms[room]:
            print(f'{room}.locations.add(locations["{loc}"])')

        # .connections.add((r01c7, Req(door=23)))
        room_no = row * 8 + col

        up = room_no - 8
        if up > 0:
            r = up // 8
            conn = f"r{r if r > 9 else '0' + str(r)}c{up % 8}"
            if conn in rooms:
                connections.append(f'{room}.connections.add(({conn}, Req(door={room_no})))')
        down = room_no + 8
        if down < 136:
            r = down // 8
            conn = f"r{r if r > 9 else '0' + str(r)}c{down % 8}"
            if conn in rooms:
                connections.append(f'{room}.connections.add(({conn}, Req(door={room_no})))')
        left = room_no - 1
        if left % 8 != 7:
            r = left // 8
            conn = f"r{r if r > 9 else '0' + str(r)}c{left % 8}"
            if conn in rooms:
                connections.append(f'{room}.connections.add(({conn}, Req(door={room_no})))')
        right = room_no + 1
        if right % 8 != 0:
            r = right // 8
            conn = f"r{r if r > 9 else '0' + str(r)}c{right % 8}"
            if conn in rooms:
                connections.append(f'{room}.connections.add(({conn}, Req(door={room_no})))')

    print()
    for connection in connections:
        print(connection)


def add_doors_to_regions() -> None:
    lines: List[str]
    with open("src/region_data.py") as file:
        lines = file.readlines()
    for i, line in enumerate(lines):
        split1 = line.split('Region("r')
        if len(split1) > 1:
            room_coords = split1[1][:-3]
            split2 = room_coords.split('c')
            try:
                room_no = int(split2[0]) * 8 + int(split2[1])
                new_line = line[:-2] + f", {room_no})\n"
                lines[i] = new_line
            except ValueError:
                pass  # ignore divided rooms
    with open("src/region_data.py", "w") as file:
        file.writelines(lines)


if __name__ == "__main__":
    region_code_maker()
