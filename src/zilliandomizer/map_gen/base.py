from dataclasses import dataclass
from typing import Mapping

from .base_maker import BaseMaker, Node
from .door_manager import DoorManager


@dataclass
class Base:
    red: BaseMaker
    paperclip: BaseMaker
    dm: DoorManager
    pc_splits: Mapping[Node, Node]
