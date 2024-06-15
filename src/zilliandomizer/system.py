import random
from typing import FrozenSet, List, Optional, Tuple, Union

from .alarms import Alarms
from .game import Game
from .logger import Logger
from .map_gen.jump import room_jump_requirements
from .options import Chars, Options, chars
from .patch import Patcher
from .randomizer import Randomizer
from .resource_managers import ResourceManagers
from .room_gen.room_gen import RoomGen


class System:
    """ composition of the highest level components """
    randomizer: Optional[Randomizer] = None
    resource_managers: ResourceManagers
    patcher: Optional[Patcher] = None
    _modified_rooms: FrozenSet[int] = frozenset()
    _seed: Optional[Union[int, str]] = None

    def __init__(self) -> None:
        self.resource_managers = ResourceManagers()

    def seed(self, seed: Optional[Union[int, str]]) -> None:
        self._seed = seed
        random.seed(seed)

    def make_patcher(self, path_to_rom: str = "") -> Patcher:
        self.patcher = Patcher(path_to_rom)
        return self.patcher

    def make_randomizer(self, options: Options, logger: Optional[Logger] = None) -> Randomizer:
        self.randomizer = Randomizer(options, logger)
        return self.randomizer

    def make_map(self) -> None:
        assert self.randomizer, "initialization step was skipped"
        options = self.randomizer.options
        self._modified_rooms = frozenset()
        # TODO: 3-choice option for map_gen
        if options.map_gen != "none":
            print("Zillion room gen enabled - generating rooms...")  # this takes time
            rm = self.resource_managers
            jump_req_rooms = room_jump_requirements()
            rm.aem.room_gen_mods()
            room_gen = RoomGen(rm.tm, rm.sm, rm.aem, self.randomizer.logger, options.skill,
                               self.randomizer.regions, self.randomizer.room_gen_data)
            room_gen.generate_all(jump_req_rooms)
            self.randomizer.reset(room_gen)
            self._modified_rooms = room_gen.get_modified_rooms()
            print("Zillion room gen complete")

    def post_fill(self) -> None:
        assert self.randomizer, "initialization step was skipped"
        options = self.randomizer.options
        if options.randomize_alarms:
            a = Alarms(self.resource_managers.tm, self.randomizer.logger)
            a.choose_all(self._modified_rooms)

        def choose_escape_time(skill: int) -> int:
            """ based on skill - WR did escape in 160 - skill 5 could require 165-194 """
            # TODO: adjusted with map_gen
            low = 300 - (skill * 27)
            return random.randrange(low, low + 30)

        self.resource_managers.escape_time = choose_escape_time(options.skill)

        def choose_capture_order(start_char: Chars) -> Tuple[Chars, Chars, Chars]:
            """
            choose the order that the captured characters appear in the intro text

            returns `start_char, captured_1, captured_2`
            """
            captured: List[Chars] = [each_char for each_char in chars if each_char != start_char]
            assert len(captured) == 2, f"{captured=}"
            random.shuffle(captured)
            return (start_char, captured[0], captured[1])

        self.resource_managers.char_order = choose_capture_order(options.start_char)

    def get_game(self) -> Game:
        assert self.randomizer, "initialization step was skipped"
        rm = self.resource_managers
        writes = rm.get_writes()
        writes.update(self.randomizer.get_door_writes())
        return Game(
            self.randomizer.options,
            rm.escape_time,
            rm.char_order,
            self.randomizer.loc_name_2_pretty,
            self.randomizer.get_region_data(),
            writes
        )
