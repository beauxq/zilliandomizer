from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Deque, Dict, List, Set, Tuple, Union

from .base_maker import BaseMaker, Node

_safe_elevator_x = (0x10, 0x20, 0x30, 0x60, 0x80, 0xd0, 0xd0)
"""
all elevators in vanilla are at x pixels: 10, 20, 30, 60, 80, d0
so I don't know whether it's safe to put elevators at other x coordinates

in room_gen.py, we hide extra sprites at a0, so it's not safe there

The width of the elevator is 1.5 large tiles (so e0 isn't safe).

This is a distribution to `random.choice` from, so some are listed multiple times.
"""


class Corner(Enum):
    bl = auto()
    tl = auto()
    br = auto()
    tr = auto()


class DE(Enum):
    door = auto()
    elevator = auto()


@dataclass(frozen=True)
class Desc:
    de: DE
    y: int
    """ in door data structure units (0 - 5) """
    x: int
    """ in pixels (0x00 - 0xf0) """

    def corner_conflicts(self) -> List[Corner]:
        """ with possible conflicts (A door in a corner is not a possible conflict - only doors at 1 or 3.) """
        if self.de is DE.elevator:
            if self.y > 2:
                # bottom
                if self.x < 0x30:
                    return [Corner.bl]
                if self.x > 0xc0:
                    return [Corner.br]
                return []
            if self.y < 2:
                # top
                if self.x < 0x30:
                    return [Corner.tl]
                if self.x > 0xc0:
                    return [Corner.tr]
                return []
        else:
            assert self.de is DE.door  # TODO: assert_type
            if self.y == 3:
                # bottom
                if self.x < 0x30:
                    return [Corner.bl]
                if self.x > 0xc0:
                    return [Corner.br]
                return []
            if self.y == 1:
                # top
                if self.x < 0x30:
                    return [Corner.tl]
                if self.x > 0xc0:
                    return [Corner.tr]
                return []
        return []


# TODO: duplicate info in region_maker
_red_right_no_doors = {
    Node(0, 2),  # no computer  # TODO: implement changing which rooms have computers and doors?
    Node(0, 3),  # start hall
    Node(1, 2),  # hall
    Node(2, 1),  # no computer and no canisters
    Node(4, 3),  # hall
    Node(4, 4),  # no canisters
}

_requires_y_4: Set[Node] = {
    Node(1, 2),  # hall
    Node(4, 3),  # hall
}

_red_right_area_exits = {
    51: Desc(DE.door, 4, 0x18),
    67: Desc(DE.door, 4, 0x18),
    75: Desc(DE.door, 4, 0x18),
}


def make_edge_descriptions(bm: BaseMaker) -> Dict[Node, Dict[Node, Desc]]:
    """
    choose locations of doors and elevators

    The first `Desc` in the inner `dict` is the entrance to the room (the outer `Node`).
    """
    # print(bm.map_str())

    parents: Dict[Node, Union[Node, None]] = {
        Node(0, 3): None,
        Node(0, 2): Node(0, 3),
        Node(0, 4): Node(0, 3),
    }
    edge_descriptions: Dict[Node, Dict[Node, Desc]] = {
        Node(0, 3): {
            Node(0, 2): Desc(DE.door, 4, 0x08),
            Node(0, 4): Desc(DE.door, 4, 0xf0),
        },
    }

    def back_to_computer(node: Node) -> int:
        """ map_index of last keyword room in path """
        back: Union[Node, None] = node
        while back in _red_right_no_doors:
            back = parents[back]
        # TODO: should BaseMaker know the last door before arriving at this section?
        assert back, f"no keywords in path to elevator {node=}\n{bm.map_str()}"
        return (back.y + bm.row_offset) * 8 + (back.x + bm.col_offset)

    for row in range(bm.row_offset, bm.row_offset + bm.height):
        for col in range(bm.col_offset, bm.col_offset + bm.width):
            map_index = row * 8 + col
            bm.door_manager.del_room(map_index)

    done: Set[Node] = set()
    q: Deque[Node] = deque([Node(0, 3)])

    while len(q):
        here = q.popleft()
        if here in done:
            continue
        done.add(here)
        row = bm.row_offset + here.y
        col = bm.col_offset + here.x
        map_index = row * 8 + col
        adjs = list(bm.adjs(here))
        parent = parents[here]
        outs = [n for n in adjs if n != parent]
        if parent:
            assert here not in edge_descriptions, f"{here=}"
            edge_descriptions[here] = {}
            in_desc = edge_descriptions[parent][here]
            entrance_y, entrance_x = get_entrance_coords(here, parent, in_desc)
            out_through_in = Desc(in_desc.de, entrance_y, entrance_x)
            edge_descriptions[here][parent] = out_through_in
            corners_used_in_this_room = out_through_in.corner_conflicts()
            for out in outs:
                if here.x < out.x:  # going to right
                    y_choices = [0, 2, 4]
                    if Corner.tr not in corners_used_in_this_room:
                        y_choices.append(1)
                    if Corner.br not in corners_used_in_this_room:
                        y_choices.append(3)
                    exit_x = 0xf0
                    exit_y = 4 if out in _requires_y_4 or here in _requires_y_4 else bm.random.choice(y_choices)
                    out_desc = Desc(DE.door, exit_y, exit_x)
                    if here not in _red_right_no_doors:
                        bm.door_manager.add_door(map_index, exit_y, exit_x, map_index)
                elif here.x > out.x:  # going to left
                    y_choices = [0, 2, 4]
                    if Corner.tl not in corners_used_in_this_room:
                        y_choices.append(1)
                    if Corner.bl not in corners_used_in_this_room:
                        y_choices.append(3)
                    exit_x = 0x08
                    exit_y = 4 if out in _requires_y_4 or here in _requires_y_4 else bm.random.choice(y_choices)
                    out_desc = Desc(DE.door, exit_y, exit_x)
                    if here not in _red_right_no_doors:
                        bm.door_manager.add_door(map_index, exit_y, exit_x, map_index)
                elif here.y < out.y:  # going down
                    x_choices = [
                        x
                        for x in _safe_elevator_x
                        if ((x > 0x20 or Corner.bl not in corners_used_in_this_room) and
                            (x < 0xc0 or Corner.br not in corners_used_in_this_room))
                    ]
                    exit_x = bm.random.choice(x_choices)
                    exit_y = 5
                    out_desc = Desc(DE.elevator, exit_y, exit_x)
                    bm.door_manager.add_elevator(map_index, exit_y, exit_x, back_to_computer(here))
                elif here.y > out.y:  # going up
                    x_choices = [
                        x
                        for x in _safe_elevator_x
                        if ((x > 0x20 or Corner.tl not in corners_used_in_this_room) and
                            (x < 0xc0 or Corner.tr not in corners_used_in_this_room))
                    ]
                    exit_x = bm.random.choice(x_choices)
                    exit_y = 0
                    out_desc = Desc(DE.elevator, exit_y, exit_x)
                    bm.door_manager.add_elevator(map_index, exit_y, exit_x, back_to_computer(here))
                else:
                    raise ValueError(f"equal? {here=} {out=}")

                edge_descriptions[here][out] = out_desc
                corners_used_in_this_room.extend(out_desc.corner_conflicts())
                parents[out] = here
            area_exit = _red_right_area_exits.get(map_index)
            if area_exit:
                bm.door_manager.add_door(map_index, area_exit.y, area_exit.x, map_index)
        q.extend(outs)

    return edge_descriptions


def get_entrance_coords(here: Node, parent: Node, in_desc: Desc) -> Tuple[int, int]:
    """ y, x """
    if here.x < parent.x:  # came from right
        assert in_desc.de is DE.door and in_desc.x == 0x08, f"{here=}"
        entrance_x = 0xf0
        entrance_y = in_desc.y
    elif here.x > parent.x:  # came from left
        assert in_desc.de is DE.door and in_desc.x == 0xf0, f"{here=}"
        entrance_x = 0x08
        entrance_y = in_desc.y
    elif here.y < parent.y:  # came from below
        assert in_desc.de is DE.elevator and in_desc.y == 0, f"{here=}"
        entrance_x = in_desc.x
        entrance_y = 5
    elif here.y > parent.y:  # came from above
        assert in_desc.de is DE.elevator and in_desc.y == 5, f"{here=}"
        entrance_x = in_desc.x
        entrance_y = 0
    else:
        raise ValueError(f"equal? {here=} {parent=}")
    return entrance_y, entrance_x
