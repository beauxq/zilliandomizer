from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, TypedDict

from zilliandomizer.logic_components.items import Item

CharReq = tuple[Literal["JJ", "Apple", "Champ"], ...]
""" having any member of the tuple will meet requirement """


class Req:
    """
    requirement

    "and" of all of these, `union` used for "or"

    zero means nothing required for all ints

    can be used to represent what I have to test whether I meet requirements with `>=`
     - `door` and `union` are unused in the left side of this operator
     - `have_doors` is only used on the left side of this operator

    object is mutable, don't use one Req object for different access points
    """

    gun: int
    """ 1, 2, or 3 """
    jump: int
    """ vanilla values: jump 0 = 48 pixels, 1 = 64px, 2 = 80px, 3 = 96px """
    char: CharReq
    hp: int
    """ max hp, greater than this, not just this """
    door: int
    have_doors: set[int]
    """ used for comparing access with a requirement """
    skill: int
    """ get good bro """
    union: "tuple[Req, ...] | None"
    """ python can't use `or` as a property name """

    red: int
    """ how many red id cards """
    floppy: int
    """ how many floppies """

    def __init__(self, *,
                 gun: int = 0,
                 jump: int = 0,
                 char: CharReq = ("JJ", "Apple", "Champ"),
                 hp: int = 0,
                 door: int = 0,
                 skill: int = 0,
                 union: "tuple[Req, ...] | None" = None,
                 red: int = 0,
                 floppy: int = 0) -> None:
        self.gun = gun
        self.jump = jump
        self.char = char
        self.hp = hp
        self.door = door
        self.have_doors = set()
        self.skill = skill
        self.union = union
        self.red = red
        self.floppy = floppy

    def __or__(self, other: "Req") -> "Req":
        return Req(union=(self, other))

    def __hash__(self) -> int:
        return hash(id(self))

    def __eq__(self, __o: object) -> bool:
        return self is __o

    def __ge__(self, other: "Req") -> bool:
        """ self meets requirements of other """
        return (
            self.gun >= other.gun and
            self.jump >= other.jump and
            any(need in self.char for need in other.char) and
            (other.hp == 0 or self.hp > other.hp) and
            (other.door == 0 or other.door in self.have_doors) and
            self.skill >= other.skill and
            (other.union is None or any(self >= each for each in other.union)) and
            self.floppy >= other.floppy and
            self.red >= other.red
        )

    def __repr__(self) -> str:
        names = [name for name in dir(self) if not (name.startswith('_') or name == "have_doors")]
        names_and_values: list[str] = []
        for name in names:
            value: object = getattr(self, name)
            names_and_values.append(f"{name}={value!r}")
        return f'Req({", ".join(names_and_values)})'


class ReqArgs(TypedDict, total=False):
    gun: int
    """ 1, 2, or 3 """
    jump: int
    """ vanilla values: jump 0 = 48 pixels, 1 = 64px, 2 = 80px, 3 = 96px """
    char: CharReq
    hp: int
    """ max hp, greater than this, not just this """
    door: int
    skill: int
    """ get good bro """
    union: tuple[Req, ...] | None


@dataclass
class Location:
    name: str
    """ unique """
    req: Req
    """ requirement to get this location """
    after: Req | None = None
    """ requirement to get out of this location """
    item: Item | None = None
    """ the item that is at this location """

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Location) and self.name == other.name


@dataclass
class LocationData:
    name: str
    item: Item
    req_gun: int

    @staticmethod
    def from_location(location: Location) -> LocationData:
        item = location.item
        if not item:
            raise ValueError(f"location {location.name} didn't get item")
        return LocationData(
            location.name,
            item,
            location.req.gun
        )

    def to_jsonable(self) -> dict[str, object]:
        dct = asdict(self)
        dct["item"] = asdict(self.item)
        return dct

    @staticmethod
    def from_jsonable(dct: dict[str, Any]) -> LocationData:
        ld = LocationData(**dct)
        ld.item = Item(**dct["item"])
        return ld
