from random import choice, sample
from typing import Dict, FrozenSet, List, Set
from zilliandomizer.logic_components.location_data import make_locations
from zilliandomizer.logic_components.locations import Location, Req
from zilliandomizer.logic_components.region_data import make_regions
from zilliandomizer.logic_components.regions import Region
from zilliandomizer.low_resources.terrain_tiles import Tile
from zilliandomizer.room_gen.common import FOUR_CORNERS, Coord, coord_to_pixel
from zilliandomizer.room_gen.data import GEN_ROOMS
from zilliandomizer.room_gen.maze import Cell, Grid, MakeFailure
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

    _rooms: Set[int]
    """ rooms generated (map_index) """

    def __init__(self, tc: TerrainCompressor, logger: Logger) -> None:
        self.tc = tc

        """
        self._space_pacer_init = tc.get_space()
        self._space_pacer = self._space_pacer_init
        # This is assuming that we are the last step modifying terrain,
        # because this could use all of the space for terrain.
        # So, anything else modifying terrain needs to be done before initializing this object.
        self._space_per_room = self._space_pacer / len(ALARM_ROOMS)
        """

        self._logger = logger
        self._canisters = {}
        self._rooms = set()
        # testing
        logger.spoil_stdout = True
        logger.debug_stdout = True

    def generate_all(self) -> None:
        if len(Region.all) == 0:
            locations = make_locations()
            make_regions(locations)

        # TODO: I haven't tested the tc save state and success loop yet
        self.tc.save_state()
        self._canisters = {}
        self._rooms = set()
        success = False  # generated all rooms without going over the byte limit
        while not success:
            self._logger.spoil("generating rooms...")
            # self._space_pacer = self._space_pacer_init
            for i, map_index in enumerate(GEN_ROOMS):
                if map_index > 0x18:
                    continue  # testing
                print(f"generating room {i + 1} / {len(GEN_ROOMS)}")
                jump_block_ability = 2  # TODO: progressive jump requirements
                self._generate_room(map_index, jump_block_ability)
                # self._space_pacer -= self._space_per_room
                self._rooms.add(map_index)
            if self.tc.get_space() >= 0:
                success = True
            else:
                self._logger.debug(f"overused terrain memory by {-self.tc.get_space()} bytes")
                self.tc.load_state()
                self._canisters = {}
                self._rooms = set()

    def _generate_room(self, map_index: int, jump_blocks: int) -> None:
        this_room = GEN_ROOMS[map_index]
        exits = this_room.exits[:]
        if len(exits) < 2:
            row, col = exits[0]
            far_corners = [
                corner for corner in FOUR_CORNERS if (corner[0] != row or corner[1] != col)
            ]
            exits.append(choice(far_corners))
        g = Grid(exits, self._logger)
        placed: List[Coord] = []

        while len(placed) == 0:  # TODO: not a good condition (some rooms don't have anything - r08c1)
            g.reset()
            try:
                g.make(jump_blocks)
                g.fix_crawl_fall()
                g.optimize_encoding()
                softlock = g.softlock_exists(2) or g.softlock_exists(3)
                if not softlock:
                    # TODO: keep track of which canisters require jump 3
                    goables = g.get_standing_goables(jump_blocks)
                    placeables = [(y, x) for y, x, _ in goables if not g.in_exit(y, x)]
                    reg_name = make_reg_name(map_index)
                    assert reg_name in Region.all, f"generated terrain for non-region {reg_name}"
                    region = Region.all[reg_name]
                    placeable_count = len(region.locations)
                    if len(placeables) > placeable_count + 1:
                        placed = sample(placeables, placeable_count)
                        self._canisters[map_index] = placed
            except MakeFailure:
                print(".", end="")
        self._logger.debug(g.map_str(placed))

        self.tc.set_room(map_index, self._grid_to_room_data(g, map_index))

    def _grid_to_room_data(self, g: Grid, map_index: int) -> List[int]:
        """ to compressed """
        if map_index < 0x28:  # blue
            wall = Tile.b_walls
            floor_even = Tile.b_floor
            floor_odd = floor_even
            space_even = Tile.b_space
            space_odd = space_even
            ceiling_even = Tile.b_ceiling
            ceiling_odd = ceiling_even
            floor_ceiling_even = Tile.b_floor_ceiling
            floor_ceiling_odd = floor_ceiling_even
        elif map_index < 0x50:  # red
            wall = Tile.r_walls
            floor_even = Tile.r_light_floor
            floor_odd = Tile.r_dark_floor
            space_even = Tile.r_light_space
            space_odd = Tile.r_dark_space
            ceiling_even = Tile.r_light_ceiling
            ceiling_odd = Tile.r_dark_ceiling
            floor_ceiling_even = Tile.r_light_floor_ceiling
            floor_ceiling_odd = Tile.r_dark_floor_ceiling
        else:  # paperclip
            wall = Tile.p_walls
            floor_even = Tile.p_floor
            floor_odd = floor_even
            space_even = Tile.p_space
            space_odd = space_even
            ceiling_even = Tile.p_ceiling
            ceiling_odd = ceiling_even
            floor_ceiling_even = Tile.p_floor_ceiling
            floor_ceiling_odd = floor_ceiling_even

        original_data = TerrainCompressor.decompress(self.tc.get_room(map_index))

        tr: List[int] = []
        for row in range(len(g.data)):

            # left wall
            tr.append(original_data[len(tr)])

            for col in range(len(g.data[0])):
                if g.data[row][col] == Cell.wall:
                    tr.append(wall)
                else:  # not wall here
                    ceiling_here = (row == 0) or (g.data[row - 1][col] != Cell.space)
                    if not ceiling_here:
                        if g.data[row][col] == Cell.space:
                            tr.append(space_odd if (row & 1) else space_even)
                        else:  # floor with no ceiling
                            tr.append(floor_odd if (row & 1) else floor_even)
                    else:  # floor or space with ceiling above
                        if g.data[row][col] == Cell.space:
                            tr.append(ceiling_odd if (row & 1) else ceiling_even)
                        else:  # floor with no ceiling
                            tr.append(floor_ceiling_odd if (row & 1) else floor_ceiling_even)

            # right wall
            tr.append(original_data[len(tr)])

        return TerrainCompressor.compress(tr)

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

    def get_modified_rooms(self) -> FrozenSet[int]:
        return frozenset(self._rooms)
