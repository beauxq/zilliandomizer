from dataclasses import dataclass

from zilliandomizer.np_sprite_manager import NPSpriteManager
from zilliandomizer.room_gen.aem import AlarmEntranceManager
from zilliandomizer.terrain_modifier import TerrainModifier


@dataclass
class ResourceManagers:
    tm: TerrainModifier
    sm: NPSpriteManager
    aem: AlarmEntranceManager
