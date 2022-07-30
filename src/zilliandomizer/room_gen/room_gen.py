from random import choice, random, randrange, sample, shuffle
from typing import Dict, FrozenSet, List, Optional, Set, Tuple
from zilliandomizer.logic_components.location_data import make_locations
from zilliandomizer.logic_components.locations import Location, Req
from zilliandomizer.logic_components.region_data import make_regions
from zilliandomizer.logic_components.regions import Region
from zilliandomizer.low_resources.sprite_types import AutoGunSub, BarrierSub, SpriteType
from zilliandomizer.np_sprite_manager import NPSpriteManager, RoomSprites
from zilliandomizer.room_gen.common import FOUR_CORNERS, Coord, coord_to_pixel
from zilliandomizer.room_gen.data import GEN_ROOMS
from zilliandomizer.room_gen.maze import Grid, MakeFailure
from zilliandomizer.room_gen.sprite_placing import auto_gun_places, barrier_places
from zilliandomizer.terrain_compressor import TerrainCompressor
from zilliandomizer.utils import make_loc_name, make_reg_name
from zilliandomizer.logger import Logger

floor_sprite_types = (
    SpriteType.mine,
    SpriteType.enemy,
    # moving falling enemies to the floor
    # because it's more complex to find a place for them to fall from
    # TODO: implement falling enemies
    SpriteType.falling_enemy
)


class RoomGen:
    """
    Anything else modifying terrain needs to be done before initializing this object,
    because this could use all of the space for terrain.
    """
    tc: TerrainCompressor
    sm: NPSpriteManager
    _logger: Logger
    _skill: int
    """ from options """

    _canisters: Dict[int, List[Tuple[Coord, float]]]
    """ placed canisters { map_index: [(Coord, jump_blocks_required), ...] } """

    _computers: Dict[int, Coord]
    """ placed computers { map_index: Coord } """

    _rooms: Dict[int, float]
    """ rooms generated {map_index: jump_blocks} """

    def __init__(self, tc: TerrainCompressor, sm: NPSpriteManager, logger: Logger, skill: int) -> None:
        self.tc = tc
        self.sm = sm
        self._logger = logger
        self._skill = skill

        # testing
        # logger.spoil_stdout = True
        # logger.debug_stdout = True

    def reset(self) -> None:
        self._canisters = {}
        self._computers = {}
        self._rooms = {}

    def generate_all(self, map_index_2_jump_level: Dict[int, int]) -> None:
        if len(Region.all) == 0:
            locations = make_locations()
            make_regions(locations)

        # TODO: I haven't tested the tc save state and success loop yet
        self.tc.save_state()
        self.sm.save_state()
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
                jump_block_ability = 2 if map_index_2_jump_level[map_index] == 1 else (
                    2.5 if map_index_2_jump_level[map_index] == 2 else 3
                )

                number_of_rooms_remaining = len(GEN_ROOMS) - i
                ideal_space_limit = (total_space_limit - total_space_taken) / number_of_rooms_remaining
                hard_space_limit = ideal_space_limit + (30 * (number_of_rooms_remaining - 1) / len(GEN_ROOMS))
                space_taken, jump_required = self._generate_room(map_index, jump_block_ability, hard_space_limit)
                total_space_taken += space_taken
                self._logger.debug("over" if space_taken > 59 else "under")

                self._rooms[map_index] = jump_required
            if self.tc.get_space() >= 0:
                success = True
            else:
                self._logger.debug(f"overused terrain memory by {-self.tc.get_space()} bytes")
                self.tc.load_state()
                self.sm.load_state()
                self.reset()

    def _generate_room(self,
                       map_index: int,
                       jump_blocks: float,
                       size_limit: float) -> Tuple[int, float]:
        """ returns (the length of the compressed room data, jump blocks required to traverse) """
        this_room = GEN_ROOMS[map_index]
        exits = this_room.exits[:]  # real exits
        ends = exits[:]  # places I want to be able to get to
        if len(ends) < 2:
            row, col = ends[0]
            far_corners = [
                corner for corner in FOUR_CORNERS
                if (corner[0] != row and abs(corner[1] - col) > 4)
            ]
            assert len(far_corners) == 1
            adjacent_corners = [
                corner for corner in FOUR_CORNERS
                if (corner[0] == row and abs(corner[1] - col) > 4)
                or (corner[0] != row and abs(corner[1] - col) < 4)
            ]
            assert len(adjacent_corners) == 2
            ends.extend(choice((far_corners, adjacent_corners)))

        def make_optimized_no_softlock() -> Grid:
            tr = Grid(exits,
                      ends,
                      map_index,
                      self.tc,
                      self._logger,
                      self._skill,
                      this_room.no_space)
            tr.make(jump_blocks, size_limit)
            if random() < 0.5:
                # I used to use this for softlock avoidance,
                # but after improving the movement adjacency function,
                # I don't need it for softlock avoidance anymore (maybe?).
                # But it makes a significantly different style of room,
                # so I include it randomly for variety.
                tr.fix_crawl_fall()
            tr.optimize_encoding()
            # place some new walkways after post-processing
            solved = False
            for _ in range(5 if tr.walkways else 1):
                if tr.walkways:
                    tr.place_walkways()
                if tr.solve(jump_blocks):
                    solved = True
                    break
            if tr.softlock_exists():
                raise MakeFailure("softlock")
            if not solved:
                # This is expected to happen changing walkways after optimization
                # self._logger.warn("WARNING: room generation post-processing removed navigability")
                raise MakeFailure("post-proc broke room")
            return tr

        # If all the ends are on the bottom, I want an extra chance to get high goables
        second_candidate_for_elevation = all(end[0] > 2 for end in ends)

        g: Optional[Grid] = None
        placed: List[Coord] = []

        while not g:
            try:
                candidate = make_optimized_no_softlock()
                candidate_goables = candidate.get_goables(jump_blocks)
                if second_candidate_for_elevation:
                    # lowest y coordinate is highest elevation
                    highest = min(c[0] for c in candidate_goables)
                    if highest > 1:
                        candidate_2 = make_optimized_no_softlock()
                        candidate_2_goables = candidate_2.get_goables(jump_blocks)
                        highest_2 = min(c[0] for c in candidate_2_goables)
                        if highest_2 < highest:
                            candidate = candidate_2
                            candidate_goables = candidate_2_goables
                # TODO: find out which exits require jump 2.5, 3
                standing = [g for g in candidate_goables if g[2]]
                placeables = [(y, x) for y, x, _ in standing if not candidate.in_exit(y, x)]
                reg_name = make_reg_name(map_index)
                assert (reg_name == "r08c1") or (reg_name in Region.all), \
                    f"generated terrain for non-region {reg_name}"
                region_locations = Region.all[reg_name].locations if reg_name in Region.all else []
                sprites = self.sm.get_room(map_index)
                floor_sprite_count = sum(s.type[0] in floor_sprite_types for s in sprites)
                placeable_count = (
                    len(region_locations) +
                    this_room.computer +
                    floor_sprite_count
                )
                self._logger.debug(f"need to place {placeable_count} in room {map_index}")
                if len(placeables) >= placeable_count:
                    if placeable_count > 0:
                        # take 2 samples, and choose whichever has higher coords
                        # (to counter the tendency of putting most on the lowest level)
                        placed_1 = sample(placeables, placeable_count)
                        placed_2 = sample(placeables, placeable_count)
                        sum_1 = sum(p[0] for p in placed_1)
                        sum_2 = sum(p[0] for p in placed_2)
                        placed = placed_1 if sum_1 < sum_2 else placed_2
                    self.place(placed, sprites, map_index, candidate)
                    g = candidate
                    # testing - TODO: make unit test for Grid.no_space
                    # if map_index in (0x4b, 0x21):
                    # if map_index < 0x28:
                    #     print(g.map_str())
            except MakeFailure:
                print(".", end="")
        print()
        # self._logger.debug(g.map_str(placed))

        jump_blocks_required = 2 if g.solve(2) else (2.5 if g.solve(2.5) else 3)
        # testing
        # if jump_blocks_required == 2.5:
        #     print(f"2.5 req {map_index}")
        #     print(g.map_str())
        compressed = g.to_room_data()
        self.tc.set_room(map_index, compressed)
        return len(compressed), jump_blocks_required

    def place(self,
              coords: List[Coord],
              sprites: RoomSprites,
              map_index: int,
              grid: Grid) -> None:
        """
        place the things that need to be placed in this room

        length of coords should be (
            the number of floor sprites in the non-player sprite table
            + the number of canisters in the room
            + 1 if there's a computer in the room
        )
        """
        # TODO: place alarm sensors
        # TODO: possible uncompletable seed: Make sure I can get to 2 places
        # in the height of the lowest canister.
        agp = auto_gun_places(grid)
        bp = barrier_places(grid, coords)
        cursor = 0
        for sprite in sprites:
            if sprite.type[0] in floor_sprite_types:
                # TODO: can I make it so it's always possible to jump over mines?
                y, x = coord_to_pixel(coords[cursor])
                cursor += 1
                if sprite.type[0] == SpriteType.mine:
                    y += 0x10
                elif sprite.type[0] == SpriteType.falling_enemy:
                    sprite.type = (SpriteType.enemy, sprite.type[1])
                sprite.x = x
                sprite.y = y
            elif sprite.type[0] == SpriteType.barrier:
                if len(bp.bars):
                    bar_place = bp.bars.pop()
                    new_subtype = (
                        (BarrierSub.hor_2, BarrierSub.hor_4)[bar_place.length - 1]
                        if bar_place.horizontal
                        else (BarrierSub.ver_4, BarrierSub.ver_8)[bar_place.length - 1]
                    )

                    sprite.type = (sprite.type[0], new_subtype)
                    y, x = coord_to_pixel(bar_place.c)
                    if bar_place.horizontal:
                        y += 0x20  # bottom of tile
                    else:  # vertical
                        y += 8
                        x += 8 * randrange(2)  # either left or right side of larger tile
                        # TODO: if one side is next to a wall, move x away from wall
                else:  # didn't find any good place to put a bar
                    # This mine will show up in next room,
                    # while screen scrolls to it going down elevator.
                    # But then it disappears when arriving (stop scrolling)
                    # and I didn't find any way to interact with it.
                    # So it's not a bad way of disposing of a sprite.
                    sprite.type = (SpriteType.mine, 0x00)
                    y = 0xbc  # half off screen
                    x = 0xa0  # where elevators don't reach
                    # TODO: need a better solution in case I change location of elevators
                    self._logger.debug(f"not enough good places for barrier in room {map_index}")
                sprite.y = y
                sprite.x = x
            elif sprite.type[0] == SpriteType.auto_gun:
                # TODO: can I avoid having them move over doors?
                # (I already avoid placing them on doors, but they can still move.)
                subtype = sprite.type[1]
                if subtype in (AutoGunSub.down, AutoGunSub.down_move):
                    if len(agp.down):
                        c = agp.down.pop()
                        y, x = coord_to_pixel(c)
                        y += 8
                    else:
                        y = 0
                        x = randrange(0x10, 0xe1)
                elif subtype in (AutoGunSub.right, AutoGunSub.right_move):
                    if len(agp.right):
                        c = agp.right.pop()
                        y, x = coord_to_pixel(c)
                        y += 16
                    else:
                        y = randrange(0x48, 0x69)
                        x = 0x10
                else:  # left facing
                    if len(agp.left):
                        c = agp.left.pop()
                        y, x = coord_to_pixel(c)
                        y += 16
                    else:
                        y = randrange(0x48, 0x69)
                        x = 0xe0
                sprite.x = x
                sprite.y = y
            else:
                self._logger.warn(f"sprite type {sprite.type[0]} unhandled in room {map_index}")
        this_room = GEN_ROOMS[map_index]
        if this_room.computer:
            self._computers[map_index] = coords[cursor]
            cursor += 1
        # canisters
        goables_2 = grid.get_standing_goables(2)
        goables_25 = grid.get_standing_goables(2.5)
        cans: List[Tuple[Coord, float]] = []
        for coord in coords[cursor:]:
            y, x = coord
            state = (y, x, True)
            jump = 2 if state in goables_2 else (
                2.5 if state in goables_25 else 3
            )
            cans.append((coord, jump))
        self._canisters[map_index] = cans

        self.sm.set_room(map_index, sprites)

    def make_locations(self) -> Dict[str, Location]:
        # original = make_locations()
        locations: Dict[str, Location] = {}
        generated_regions: Set[str] = set()

        for map_index, placed in self._canisters.items():
            for can in placed:
                coord, jump_blocks = can
                jump_level = 3 if jump_blocks == 3 else (
                    2 if jump_blocks == 2.5 else 1
                )
                y, x = coord_to_pixel(coord)
                reg_name = make_reg_name(map_index)
                generated_regions.add(reg_name)
                loc_name = make_loc_name(map_index, y, x)
                locations[loc_name] = Location(loc_name, Req(gun=1, jump=jump_level))

        # copy locations from rooms that I didn't generate
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

    def get_jump_blocks_required(self, map_index: int) -> float:
        """ returns 0 if this map index wasn't generated """
        if map_index in self._rooms:
            return self._rooms[map_index]
        return 0
