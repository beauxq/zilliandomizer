import random
from typing import FrozenSet, Optional, Union

from .alarms import Alarms
from .logger import Logger
from .map_gen.jump import room_jump_requirements
from .np_sprite_manager import NPSpriteManager
from .options import Options
from .patch import Patcher
from .randomizer import Randomizer
from .resource_managers import ResourceManagers
from .room_gen.aem import AlarmEntranceManager
from .room_gen.room_gen import RoomGen
from .terrain_modifier import TerrainModifier


class System:
    """ composition of the highest level components """
    randomizer: Optional[Randomizer] = None
    resource_managers: Optional[ResourceManagers] = None
    patcher: Optional[Patcher] = None
    _modified_rooms: FrozenSet[int] = frozenset()
    _seed: Optional[Union[int, str]] = None

    def seed(self, seed: Optional[Union[int, str]]) -> None:
        self._seed = seed
        random.seed(seed)

    def make_patcher(self, path_to_rom: str = "") -> Patcher:
        self.patcher = Patcher(path_to_rom)
        return self.patcher

    def make_randomizer(self, options: Options, logger: Optional[Logger] = None) -> Randomizer:
        """ and resource_managers """
        self.resource_managers = ResourceManagers(TerrainModifier(), NPSpriteManager(), AlarmEntranceManager())
        self.randomizer = Randomizer(options, logger)
        return self.randomizer

    def make_map(self) -> None:
        assert self.randomizer, "initialization step was skipped"
        options = self.randomizer.options
        self._modified_rooms = frozenset()
        if options.room_gen:
            print("Zillion room gen enabled - generating rooms...")  # this takes time
            rm = self.resource_managers
            assert rm, "initialization step was skipped - resource_manager"
            jump_req_rooms = room_jump_requirements()
            rm.aem.room_gen_mods()
            room_gen = RoomGen(rm.tm, rm.sm, rm.aem, self.randomizer.logger, options.skill, self.randomizer.regions)
            room_gen.generate_all(jump_req_rooms)
            self.randomizer.reset(room_gen)
            self._modified_rooms = room_gen.get_modified_rooms()
            print("Zillion room gen complete")

    def post_fill(self) -> None:
        assert self.resource_managers and self.randomizer, "initialization step was skipped"
        options = self.randomizer.options
        if options.randomize_alarms:
            a = Alarms(self.resource_managers.tm, self.randomizer.logger)
            a.choose_all(self._modified_rooms)
