from random import choice, sample, shuffle
from typing import Dict, FrozenSet, List, Set
from zilliandomizer.logic_components.location_data import make_locations
from zilliandomizer.logic_components.locations import Location, Req
from zilliandomizer.logic_components.region_data import make_regions
from zilliandomizer.logic_components.regions import Region
from zilliandomizer.room_gen.common import FOUR_CORNERS, Coord, coord_to_pixel
from zilliandomizer.room_gen.data import GEN_ROOMS
from zilliandomizer.room_gen.maze import Grid, MakeFailure
from zilliandomizer.terrain_compressor import TerrainCompressor
from zilliandomizer.utils import make_loc_name, make_reg_name
from zilliandomizer.logger import Logger


class RoomGen:
    """
    Anything else modifying terrain needs to be done before initializing this object,
    because this could use all of the space for terrain.
    """
    tc: TerrainCompressor
    # _space_pacer_init: Final[float]
    """ how many extra bytes we start with before choosing alarms """
    _space_pacer: float
    """ what the space available should be if using the space gradually """
    # _space_per_room: Final[float]
    """ the ideal number of extra bytes to use for each room """
    _logger: Logger

    _canisters: Dict[int, List[Coord]]
    """ placed canisters { map_index: [Coord, ...] } """

    _computers: Dict[int, Coord]
    """ placed computers { map_index: Coord } """

    _rooms: Set[int]
    """ rooms generated (map_index) """

    def __init__(self, tc: TerrainCompressor, logger: Logger) -> None:
        self.tc = tc
        self._logger = logger

        # testing
        logger.spoil_stdout = True
        logger.debug_stdout = True

    def reset(self) -> None:
        self._canisters = {}
        self._computers = {}
        self._rooms = set()

    def generate_all(self) -> None:
        if len(Region.all) == 0:
            locations = make_locations()
            make_regions(locations)

        # TODO: I haven't tested the tc save state and success loop yet
        self.tc.save_state()
        self.reset()

        # so the top rooms don't always have more space than the bottom
        shuffled_gen_rooms = list(GEN_ROOMS.keys())
        shuffle(shuffled_gen_rooms)

        success = False  # generated all rooms without going over the byte limit
        while not success:
            self._logger.spoil("generating rooms...")
            total_space_taken = 0
            total_space_limit = len(GEN_ROOMS) * 59
            for i, map_index in enumerate(shuffled_gen_rooms):
                print(f"generating room {i + 1} / {len(GEN_ROOMS)}")
                jump_block_ability = 2  # TODO: progressive jump requirements

                number_of_rooms_remaining = len(GEN_ROOMS) - i
                ideal_space_limit = (total_space_limit - total_space_taken) / number_of_rooms_remaining
                hard_space_limit = ideal_space_limit + (30 * (number_of_rooms_remaining - 1) / len(GEN_ROOMS))
                space_taken = self._generate_room(map_index, jump_block_ability, hard_space_limit)
                total_space_taken += space_taken
                self._logger.debug("over" if space_taken > 59 else "under")

                self._rooms.add(map_index)
            if self.tc.get_space() >= 0:
                success = True
            else:
                self._logger.debug(f"overused terrain memory by {-self.tc.get_space()} bytes")
                self.tc.load_state()
                self.reset()

    def _generate_room(self, map_index: int, jump_blocks: int, size_limit: float) -> int:
        """ returns the length of the compressed room data """
        this_room = GEN_ROOMS[map_index]
        exits = this_room.exits[:]
        if len(exits) < 2:
            row, col = exits[0]
            far_corners = [
                corner for corner in FOUR_CORNERS if (corner[0] != row or corner[1] != col)
            ]
            exits.append(choice(far_corners))
        g = Grid(exits, self.tc, self._logger)
        placed: List[Coord] = []

        while len(placed) == 0:  # TODO: not a good condition (some rooms don't have anything - r08c1)
            g.reset()
            try:
                g.make(jump_blocks, size_limit)
                g.fix_crawl_fall()
                g.optimize_encoding()
                g.optimize_encoding()
                softlock = g.softlock_exists(2) or g.softlock_exists(3)
                if not softlock:
                    # TODO: keep track of which canisters require jump 3
                    goables = g.get_standing_goables(jump_blocks)
                    placeables = [(y, x) for y, x, _ in goables if not g.in_exit(y, x)]
                    reg_name = make_reg_name(map_index)
                    assert reg_name in Region.all, f"generated terrain for non-region {reg_name}"
                    region = Region.all[reg_name]
                    placeable_count = len(region.locations) + this_room.computer
                    if len(placeables) > placeable_count + 1:
                        placed = sample(placeables, placeable_count)
                        # TODO: possible uncompletable seed: Make sure I can get to 2 places
                        # in the height of the lowest canister.
                        self._canisters[map_index] = placed[this_room.computer:]
                        if this_room.computer:
                            self._computers[map_index] = placed[0]
            except MakeFailure:
                print(".", end="")
        print()
        self._logger.debug(g.map_str(placed))

        compressed = g.to_room_data(map_index)
        self.tc.set_room(map_index, compressed)
        return len(compressed)

    def make_locations(self) -> Dict[str, Location]:
        # original = make_locations()
        locations: Dict[str, Location] = {}
        generated_regions: Set[str] = set()

        for map_index, placed in self._canisters.items():
            for can in placed:
                y, x = coord_to_pixel(can)
                reg_name = make_reg_name(map_index)
                generated_regions.add(reg_name)
                loc_name = make_loc_name(map_index, y, x)
                locations[loc_name] = Location(loc_name, Req(gun=1, jump=1))  # TODO: set jump

        for region in Region.all.values():
            if region.name not in generated_regions:
                for original_loc in region.locations:
                    locations[original_loc.name] = original_loc
        locations["main"] = locations["r10c5y98x18"]  # alias
        return locations

    def get_computer(self, map_index: int) -> bytes:
        """ see doc in utils for format of computer location data """
        if map_index in self._computers:
            y, x = coord_to_pixel(self._computers[map_index])
            v = y >> 3
            h = x >> 3
            tr = (v << 6) | (h << 1)
            return tr.to_bytes(2, 'little')
        else:
            return b'\xff'

    def get_modified_rooms(self) -> FrozenSet[int]:
        return frozenset(self._rooms)