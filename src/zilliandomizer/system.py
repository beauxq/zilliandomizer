from random import Random
from typing import Dict, FrozenSet, List, Optional, Tuple, Union

from .alarms import Alarms
from .game import Game
from .logger import Logger
from .map_gen.base_maker import BaseMaker, Node, get_red_base
from .map_gen.jump import room_jump_requirements
from .map_gen.room_data_maker import make_room_gen_data
from .options import Chars, Options, chars
from .patch import Patcher
from .randomizer import Randomizer
from .resource_managers import ResourceManagers
from .room_gen.data import GEN_ROOMS
from .room_gen.room_gen import RoomGen


class System:
    """
    composition of the highest level components

    order of steps:

    - `set_options`
    - `seed`
    - `make_map`
    - `make_randomizer`
    - `post_fill`
    - `get_game`
    """
    randomizer: Optional[Randomizer] = None
    resource_managers: ResourceManagers
    patcher: Optional[Patcher] = None
    _modified_rooms: FrozenSet[int] = frozenset()
    _seed: Optional[Union[int, str]] = None
    _base: Optional[BaseMaker] = None
    _logger: Logger
    _room_gen: Optional[RoomGen] = None
    _options: Optional[Options] = None  # TODO: default options instead of None

    def __init__(self, logger: Optional[Logger] = None) -> None:
        self._logger = logger if logger else Logger()
        self._random = Random()
        self.resource_managers = ResourceManagers()

    def set_options(self, options: Options) -> None:
        self._options = options

    def seed(self, seed: Optional[Union[int, str]]) -> None:
        self._seed = seed
        self._random.seed(seed)

        # TODO: remove this when determinism is well tested without it
        import random
        random.seed(seed)

    def make_patcher(self, path_to_rom: str = "") -> Patcher:
        self.patcher = Patcher(path_to_rom)
        return self.patcher

    def make_randomizer(self) -> Randomizer:
        assert self._options, "must `set_options` first"
        self.randomizer = Randomizer(self._options, self._room_gen, self._base, self._logger)
        return self.randomizer

    def make_map(self) -> None:
        assert self._options, "must `set_options` first"
        if self._options.map_gen == "full":
            self._base = get_red_base(self._random.randrange(1999999999))
            self._logger.spoil(self._base.map_str())
            room_gen_data = make_room_gen_data(self._base)
        elif self._options.map_gen == "rooms":
            self._base = None
            room_gen_data = GEN_ROOMS.copy()
        else:  # vanilla terrain
            self._base = None
            room_gen_data = {}

        self._modified_rooms = frozenset()
        if self._options.map_gen != "none":
            print("Zillion room gen enabled - generating rooms...")  # this takes time
            rm = self.resource_managers
            jump_req_rooms = room_jump_requirements()
            rm.aem.room_gen_mods()
            self._room_gen = RoomGen(rm.tm, rm.sm, rm.aem, self._logger, self._options.skill, room_gen_data)
            self._room_gen.generate_all(jump_req_rooms)
            self._modified_rooms = self._room_gen.get_modified_rooms()
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

        path_through_red = self._get_path_through_red()
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
        writes.update(self._get_door_writes())
        return Game(
            self.randomizer.options,
            rm.escape_time,
            rm.char_order,
            self.randomizer.loc_name_2_pretty,
            self.randomizer.get_region_data(),
            writes
        )

    def _get_door_writes(self) -> Dict[int, int]:
        """ from `DoorManager` """
        if self._base:
            return self._base.door_manager.get_writes()
        return {}

    def _get_path_through_red(self) -> int:
        if self._base:
            top = self._base.path(Node(0, 3), Node(1, 0))
            mid = self._base.path(Node(0, 3), Node(3, 0))
            bot = self._base.path(Node(0, 3), Node(4, 0))
            return min(len(top), len(mid) + 1, len(bot) + 1)
        return 7  # vanilla
