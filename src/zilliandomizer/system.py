from random import Random
from typing import FrozenSet, List, Mapping, Optional, Tuple, Union

from .alarms import Alarms
from .game import Game
from .logger import Logger
from .logic_components.region_data import make_regions
from .map_gen.base_maker import BaseMaker, get_red_base
from .map_gen.jump import room_jump_requirements
from .map_gen.room_data_maker import make_room_gen_data
from .options import Chars, Options, chars
from .patch import Patcher
from .randomizer import Randomizer
from .resource_managers import ResourceManagers
from .room_gen.common import RoomData
from .room_gen.data import GEN_ROOMS
from .room_gen.room_gen import RoomGen


class System:
    """ composition of the highest level components """
    randomizer: Optional[Randomizer] = None
    resource_managers: ResourceManagers
    patcher: Optional[Patcher] = None
    _modified_rooms: FrozenSet[int] = frozenset()
    _seed: Optional[Union[int, str]] = None
    _base: Optional[BaseMaker] = None
    _logger: Logger
    _room_gen_data: Mapping[int, RoomData]

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self._logger = logger if logger else Logger()
        self._random = Random()
        self.resource_managers = ResourceManagers()

    def seed(self, seed: Optional[Union[int, str]]) -> None:
        self._seed = seed
        self._random.seed(seed)

        # TODO: remove this when determinism is well tested without it
        import random
        random.seed(seed)

    def make_patcher(self, path_to_rom: str = "") -> Patcher:
        self.patcher = Patcher(path_to_rom)
        return self.patcher

    def make_randomizer(self, options: Options, logger: Optional[Logger] = None) -> Randomizer:
        self.randomizer = Randomizer(options, logger)
        return self.randomizer

    def make_map(self, options: Options) -> None:
        if options.map_gen == "full":
            self._base = get_red_base(self._random.randrange(1999999999))
            self._logger.spoil(self._base.map_str())
            self._room_gen_data = make_room_gen_data(self._base)
        elif options.map_gen == "rooms":
            self._base = None
            self._room_gen_data = GEN_ROOMS.copy()
        else:  # vanilla terrain
            self._base = None
            self._room_gen_data = {}

        regions = make_regions(self._base)

        self._modified_rooms = frozenset()
        if options.map_gen != "none":
            print("Zillion room gen enabled - generating rooms...")  # this takes time
            rm = self.resource_managers
            jump_req_rooms = room_jump_requirements()
            rm.aem.room_gen_mods()
            room_gen = RoomGen(rm.tm, rm.sm, rm.aem, self._logger, options.skill,
                               self._room_gen_data)
            room_gen.generate_all(jump_req_rooms)
            self.randomizer.reset(room_gen)
            self._modified_rooms = room_gen.get_modified_rooms()
            print("Zillion room gen complete")

    def make_map_old(self) -> None:
        assert self.randomizer, "initialization step was skipped"
        options = self.randomizer.options
        self._modified_rooms = frozenset()
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

        def choose_escape_time(skill: int, path_through_red: float) -> int:
            """
            based on skill - WR did escape in 160 - skill 5 could require 165-194

            `path_through_red` is the number of rooms that the right red area has to go through -
            vanilla is 7 (F-4 through E-7)
            """

            # adjusted with map_gen
            if path_through_red < 7:
                path_through_red = (path_through_red + 7) / 2
            m = 20.5  # var that I played with in desmos to get good numbers
            map_gen_multiplier = (path_through_red + m) / (7 + m)  # == 1 if path_through_red == 7

            low = round((300 - (skill * 27)) * map_gen_multiplier)
            return self._random.randrange(low, low + 30)

        path_through_red = self.randomizer.get_path_through_red()
        # print(f"{path_through_red=}")
        self.resource_managers.escape_time = choose_escape_time(options.skill, path_through_red)

        def choose_capture_order(start_char: Chars) -> Tuple[Chars, Chars, Chars]:
            """
            choose the order that the captured characters appear in the intro text

            returns `start_char, captured_1, captured_2`
            """
            captured: List[Chars] = [each_char for each_char in chars if each_char != start_char]
            assert len(captured) == 2, f"{captured=}"
            self._random.shuffle(captured)
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
