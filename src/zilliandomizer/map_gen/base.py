from dataclasses import dataclass

from .base_maker import BaseMaker
from .door_manager import DoorManager


@dataclass
class Base:
    red: BaseMaker
    paperclip: BaseMaker
    dm: DoorManager
