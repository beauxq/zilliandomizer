from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Deque, Dict, List, Literal, Set, Tuple, Union

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
    hallway_elevator = auto()


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
        elif self.de is DE.door:
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
        else:
            assert self.de is DE.hallway_elevator  # TODO: assert_type
            # TODO: review 
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

_pc_no_doors = {
    Node(0, 0), Node(1, 0), Node(2, 0), Node(3, 0), Node(4, 0), Node(5, 0), Node(6, 0),  # left
    Node(0, 1), Node(1, 1), Node(2, 1),             Node(4, 1), Node(5, 1), Node(6, 1),  # rooms and halls
    Node(0, 7), Node(1, 7), Node(2, 7), Node(3, 7), Node(4, 7), Node(5, 7), Node(6, 7),  # right
    Node(0, 5), Node(0, 6),  # main computer
    Node(6, 3), Node(6, 4), Node(6, 5), Node(6, 6),  # bottom hall
}

_red_requires_y: Dict[Node, int] = {
    Node(1, 2): 4,  # hall
    Node(4, 3): 4,  # hall
}

_pc_requires_y: Dict[Node, int] = {
    Node(1, 0): 4,
    Node(3, 0): 0,  # M-2
    Node(4, 0): 4,
    Node(5, 1): 4,
    Node(6, 1): 4,
    Node(6, 3): 4,
    Node(5, 7): 4,
    Node(4, 7): 4,
    Node(3, 7): 0,  # red card
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

    if bm.height == 5:  # red
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
        no_doors = _red_right_no_doors
        requires_y = _red_requires_y
        start_node = Node(0, 3)
    else:
        assert bm.height == 7, f"{bm.height=}"  # paperclip
        parents = {
            Node(0, 0): None,
            Node(1, 0): Node(0, 0),
        }
        edge_descriptions = {
            Node(0, 0): {
                Node(1, 0): Desc(DE.hallway_elevator, 0, 0),
            },
        }
        no_doors = _pc_no_doors
        requires_y = _pc_requires_y
        start_node = Node(0, 0)

    def back_to_computer(node: Node) -> int:
        """ map_index of last keyword room in path """
        back: Union[Node, None] = node
        while back in no_doors:
            back = parents[back]
        if back is None:
            return bm.prev_door
        return (back.y + bm.row_offset) * 8 + (back.x + bm.col_offset)

    for row in range(bm.row_offset, bm.row_offset + bm.height):
        for col in range(bm.col_offset, bm.col_offset + bm.width):
            map_index = row * 8 + col
            bm.door_manager.del_room(map_index)

    done: Set[Node] = set()
    q: Deque[Node] = deque([start_node])

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
            if (map_index - 8) in _red_right_area_exits:
                # don't allow going up into the extended softlock avoidance door
                corners_used_in_this_room.append(Corner.tl)
            if map_index in _red_right_area_exits:
                # when the extended softlock avoidance door opens,
                # it will disable the elevator that appears in the same place
                corners_used_in_this_room.append(Corner.bl)
            for out in outs:
                if here.x < out.x:  # going to right
                    y_choices = [0, 2, 4]
                    if Corner.tr not in corners_used_in_this_room:
                        y_choices.append(1)
                    if Corner.br not in corners_used_in_this_room:
                        y_choices.append(3)
                    exit_x = 0xf0
                    exit_y = requires_y.get(here, requires_y.get(out, bm.random.choice(y_choices)))
                    out_desc = Desc(DE.door, exit_y, exit_x)
                    if here not in no_doors:
                        bm.door_manager.add_door(map_index, exit_y, exit_x, map_index)
                elif here.x > out.x:  # going to left
                    y_choices = [0, 2, 4]
                    if Corner.tl not in corners_used_in_this_room:
                        y_choices.append(1)
                    if Corner.bl not in corners_used_in_this_room:
                        y_choices.append(3)
                    exit_x = 0x08
                    exit_y = requires_y.get(here, requires_y.get(out, bm.random.choice(y_choices)))
                    out_desc = Desc(DE.door, exit_y, exit_x)
                    if here not in no_doors:
                        bm.door_manager.add_door(map_index, exit_y, exit_x, map_index)
                elif here.y < out.y:  # going down
                    x_choices = [
                        x
                        for x in _safe_elevator_x
                        if ((x > 0x20 or Corner.bl not in corners_used_in_this_room) and
                            (x < 0xc0 or Corner.br not in corners_used_in_this_room))
                    ]
                    exit_x = bm.random.choice(x_choices)
                    # debug code
                    # if 0x10 in x_choices:
                    #     exit_x = 0x10
                    exit_y_5: Literal[5] = 5  # TODO: when mypy gets better literal narrowing, just use exit_y
                    out_desc = Desc(DE.elevator, exit_y_5, exit_x)
                    bm.door_manager.add_elevator(map_index, exit_y_5, exit_x, back_to_computer(here))
                elif here.y > out.y:  # going up
                    x_choices = [
                        x
                        for x in _safe_elevator_x
                        if ((x > 0x20 or Corner.tl not in corners_used_in_this_room) and
                            (x < 0xc0 or Corner.tr not in corners_used_in_this_room))
                    ]
                    exit_x = bm.random.choice(x_choices)
                    exit_y_0: Literal[0] = 0  # TODO: when mypy gets better literal narrowing, just use exit_y
                    out_desc = Desc(DE.elevator, exit_y_0, exit_x)
                    bm.door_manager.add_elevator(map_index, exit_y_0, exit_x, back_to_computer(here))
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
        assert in_desc.de is DE.hallway_elevator or (in_desc.de is DE.elevator and in_desc.y == 0), f"{here=}"
        entrance_x = in_desc.x
        entrance_y = 5
    elif here.y > parent.y:  # came from above
        assert in_desc.de is DE.hallway_elevator or (in_desc.de is DE.elevator and in_desc.y == 5), f"{here=}"
        entrance_x = in_desc.x
        entrance_y = 0
    else:
        raise ValueError(f"equal? {here=} {parent=}")
    return entrance_y, entrance_x
