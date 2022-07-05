from typing import ClassVar, Dict, List, Any
# some changes here for working on region connections
# from typing_extensions import Unpack  # type: ignore
from zilliandomizer.logic_components.locations import Req, Location  # , ReqArgs


class Region:
    name: str
    door: int
    connections: Dict["Region", Req]
    locations: List[Location]
    computer: bytes
    """ `0xff` for all non-generated rooms """

    # static
    all: ClassVar[Dict[str, "Region"]] = {}

    def __init__(self, name: str, door: int = 0) -> None:
        self.name = name
        self.door = door
        self.connections = {}
        self.locations = []
        self.computer = b'\xff'
        Region.all[name] = self

    # this is good for type checking when working with region connections
    # but it doesn't run (I think it's Python 3.11 or something...)
    # def to(self, other: "Region", **req_args: Unpack[ReqArgs]) -> None:
    def to(self, other: "Region", **req_args: Any) -> None:
        """
        make a connection

        both directions, same requirements for the return direction
        """
        self.connections[other] = Req(**req_args)
        other.connections[self] = Req(**req_args)  # Is it bad that I'm not making a deep copy of the union?
