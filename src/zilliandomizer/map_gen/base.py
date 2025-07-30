from collections.abc import Mapping, Set as AbstractSet
from dataclasses import dataclass

from .base_maker import BaseMaker, Node
from .door_manager import DoorManager


@dataclass
class Base:
    red: BaseMaker
    paperclip: BaseMaker
    dm: DoorManager
    pc_splits: Mapping[Node, Node]
    pudding_cans: AbstractSet[int] | None = None
    """ which map indexes have a can in the pudding """
