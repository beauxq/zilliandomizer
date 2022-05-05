from collections import Counter, defaultdict, deque
from random import choice, randint, randrange, seed, shuffle
import time
from typing import Deque, Dict, List, Optional, Set, Counter as _Counter, cast

from zilliandomizer.location_data import make_locations
from zilliandomizer.logger import Logger
from zilliandomizer.options import ID, Chars, Options, char_to_hp, char_to_gun, char_to_jump
from zilliandomizer.region_data import make_regions
from zilliandomizer.regions import Region
from zilliandomizer.locations import Location, Req
from zilliandomizer.items import KEYWORD, MAIN, MAIN_ITEM, RESCUE, Item, items

# this is used in math, not just an id
# (in case someone is tempted to change it to 0 to match rom value)
MIN_GUN = 1
MAX_GUN = 3


class Randomizer:
    options: Options
    logger: Logger
    start: Region
    locations: Dict[str, Location]

    class RollFail(RuntimeError):
        """ randomizing algorithm failed """
        pass

    def __init__(self, options: Options, logger: Optional[Logger] = None) -> None:
        self.options = options
        if logger is None:
            logger = Logger()
            logger.spoil_stdout = True
        self.logger = logger

        self.reset()

    def reset(self) -> None:
        locations = make_locations()
        start = make_regions(locations)
        self.start = start
        self.locations = locations

        # I'm not that interested in requiring different numbers of red cards.
        locations['main'].req.red = 1
        locations['main'].req.floppy = self.options.floppy_req

    def room_door_gun_requirements(self) -> Dict[int, int]:
        """ returns map of room index to the gun requirement [1, 2, or 3] for that room """
        tr: Dict[int, int] = {}  # room index to gun requirement

        progression_path = [29, 28, 27, 26, 34, 36, 37, 47, 55, 54]  # down from 6666 until junction in red

        # tunable magic number
        extra_min_gun = 5  # inverse probability for gun requirements left and right of 6666
        # if progression path down is blocked early by gun,
        # there will be a higher chance of not blocking by gun left and right

        current_gun_requirement = MIN_GUN

        # tunable magic number
        escalation_chance = 10  # inverse prob of blocking the current gun in each room
        # expected number of requirement escalations for this section is approx. 1

        for room in progression_path:
            if randrange(escalation_chance * current_gun_requirement) == 0 \
                    and current_gun_requirement < MAX_GUN:
                current_gun_requirement += 1
            tr[room] = randint(MIN_GUN, current_gun_requirement)
            if current_gun_requirement == MIN_GUN:
                extra_min_gun -= 1  # tunable magic number
        lr_chances = list(range(MIN_GUN, MAX_GUN + 1))
        for _ in range(extra_min_gun):
            lr_chances.append(MIN_GUN)
        tr[10] = choice(lr_chances)
        tr[23] = choice(lr_chances)

        # from red junction
        red_progressions = [
            [52, 51],
            [62, 61, 59, 67],
            [62, 63, 71, 70, 69, 68, 76, 75]
        ]
        continued = [41, 49, 57, 114, 106]

        progression_path = choice(red_progressions) + continued
        for room in progression_path:
            # expected number of requirement escalations for this section is approx. 1
            if randrange(escalation_chance * current_gun_requirement) == 0 \
                    and current_gun_requirement < MAX_GUN:
                current_gun_requirement += 1
            tr[room] = randint(MIN_GUN, current_gun_requirement)

        # generated from rom data
        all_door_code_rooms = [
            10, 23, 26, 27, 28, 29, 33, 34, 36, 37, 41, 43, 44, 47, 49, 51, 52,
            54, 55, 57, 59, 61, 62, 63, 67, 68, 69, 70, 71, 75, 76, 77, 82, 83,
            84, 90, 91, 92, 93, 94, 98, 99, 100, 101, 102, 105, 106, 107, 108,
            109, 110, 114, 115, 116, 117, 118, 122, 123, 124, 125, 126, 130
        ]

        # everything not already assigned gets full random
        for room in all_door_code_rooms:
            if room not in tr:
                tr[room] = randint(MIN_GUN, MAX_GUN)

        return tr

    def place_canister_gun_reqs(self) -> None:
        """ and place keywords """
        gun_reqs = self.room_door_gun_requirements()
        for region_name in Region.all:
            region = Region.all[region_name]
            locs = region.locations[:]
            shuffle(locs)
            i = 0
            # after shuffle, the first 4 are key words for doors
            if region.door in gun_reqs:
                locs[i].req.gun = gun_reqs[region.door]
                locs[i].item = items[i]
                i += 1
                while i < 4:
                    locs[i].req.gun = randint(MIN_GUN, gun_reqs[region.door])
                    locs[i].item = items[i]
                    i += 1
            # other canisters random gun reqs
            while i < len(locs):
                if locs[i] != self.locations['main']:  # location_data might set gun reqs on main for final boss
                    locs[i].req.gun = randint(MIN_GUN, MAX_GUN)
                i += 1

    def _get_locations_inner(self, have: Req) -> List[Location]:
        """ adds doors to `have`  - see get_locations """
        # Python set order is determined by OS memory state,
        # making it "random" and not determined by random.seed()
        # Otherwise found_locations would be a set.
        found_locations: List[Location] = []
        todo_queue: Deque[Region] = deque()
        regions_finished: Set[str] = set()

        todo_queue.append(self.start)

        while len(todo_queue):
            this_region = todo_queue.popleft()
            if this_region.name in regions_finished:
                continue
            count_keywords = 0
            for loc in this_region.locations:
                if have >= loc.req:
                    found_locations.append(loc)
                    if loc.item and loc.item.code == KEYWORD:
                        count_keywords += 1
            if count_keywords > 3:
                have.have_doors.add(this_region.door)
            for neighbor in this_region.connections:
                conn_req = this_region.connections[neighbor]
                if neighbor.name not in regions_finished and have >= conn_req:
                    todo_queue.append(neighbor)
            regions_finished.add(this_region.name)

        return found_locations

    def get_locations(self, have: Req) -> List[Location]:
        """ locations that I have access to without getting any more items (1 sphere) """
        # I don't want a sphere for each door,
        # so I get the sphere modifying what doors I have access to repeatedly
        # until I don't get any more.
        last_count = -1
        locations: List[Location] = []
        while len(locations) != last_count:
            last_count = len(locations)
            locations = self._get_locations_inner(have)

        return locations

    def reachable_locations(self, items: List[Item], checking: bool = False) -> List[Location]:
        """ multiple spheres until I can't get any more items """
        items = items[:]  # don't mutate
        prev_item_count = len(items)
        # Python set order is determined by OS memory state,
        # making it "random" and not determined by random.seed()
        locations_found: Dict[Location, bool] = defaultdict(lambda: False)

        sphere = 0
        while True:
            if checking and sphere:
                self.logger.spoil(f"end of sphere: {sphere}")
            have = self.make_ability(items)
            locs = self.get_locations(have)
            for loc in locs:
                if not (locations_found[loc] or loc.item is None):
                    items.append(loc.item)
                    if loc.item.is_progression and loc.item.code != KEYWORD:
                        if checking:
                            self.logger.spoil(f"get {loc.item.name} from {loc.name}")
                locations_found[loc] = True
            if len(items) == prev_item_count:
                # didn't get anything new this sphere
                return [loc for loc in locations_found if locations_found[loc]]
            prev_item_count = len(items)
            sphere += 1

    def make_item_pool(self) -> List[Item]:
        """ from options """
        tr: List[Item] = []

        # normal items
        for i in range(5, 12):
            i = cast(ID, i)
            for _ in range(self.options.item_counts[i]):
                tr.append(items[i])

        # rescues
        tr.append(items[-2])
        tr.append(items[-1])
        locs = self.get_locations(Req(gun=3, jump=3, hp=990, skill=9001))
        remaining = [loc for loc in locs if self.can_put_item(loc)]
        self.logger.spoil(f"location count: {len(locs)}  after keywords: {len(remaining)}")
        if len(tr) > len(remaining):
            raise ValueError(f"too many items in options - {len(remaining) - 2} locations for {len(tr) - 2} items")
        empty_count = len(remaining) - len(tr)
        self.logger.spoil(f"filling remaining space with {empty_count} empty")
        for _ in range(empty_count):
            tr.append(items[4])  # empty

        return tr

    def can_put_item(self, location: Location) -> bool:
        return location.item is None and location != self.locations['main']

    def make_ability(self, item_list: List[Item]) -> Req:
        """ from just these items and options """
        have_chars: List[Chars] = [self.options.start_char]
        # whichever char I start with is replaced with JJ
        id_to_char: List[Chars] = [
            "JJ" if self.options.start_char == "Apple" else "Apple",
            "JJ" if self.options.start_char == "Champ" else "Champ"
        ]
        counts: _Counter[int] = Counter()
        for item in item_list:
            if item.code == RESCUE:
                have_chars.append(id_to_char[item.id])
            else:
                counts[item.id] += 1
        base_hp = max(char_to_hp[char] for char in have_chars)
        levels_gained = counts[ID.opa] // self.options.opas_per_level
        levels_gained = min(self.options.max_level - 1, levels_gained)
        added_hp = 20 * levels_gained
        gun = max(char_to_gun[char][self.options.gun_levels][
            min(counts[ID.gun], len(char_to_gun[char][self.options.gun_levels]) - 1)
        ] for char in have_chars)
        jump = max(char_to_jump[char][self.options.jump_levels][
            min(levels_gained, len(char_to_jump[char][self.options.jump_levels]) - 1)
        ] for char in have_chars)
        red = counts[ID.red]
        floppy = counts[ID.floppy]
        return Req(gun=gun,
                   jump=jump,
                   hp=(base_hp + added_hp),
                   skill=self.options.skill,
                   red=red,
                   floppy=floppy)

    def assume_fill(self) -> None:
        self.place_canister_gun_reqs()
        self.locations['main'].item = MAIN_ITEM
        to_place = self.make_item_pool()
        progressions: List[Item] = []
        non_progs: List[Item] = []
        for item in to_place:
            if item.is_progression:
                progressions.append(item)
            else:
                non_progs.append(item)
        shuffle(progressions)
        while len(progressions):
            item = progressions.pop()
            locs = [loc for loc in self.reachable_locations(progressions) if self.can_put_item(loc)]
            if len(locs) == 0:
                raise Randomizer.RollFail(f"no locations available for {item.name}")
            loc = choice(locs)
            loc.item = item
            if item.code == RESCUE:
                loc.req.gun = 0
        shuffle(non_progs)
        have = Req(gun=3, jump=3, hp=940, skill=9001)
        locs = [loc for loc in self.get_locations(have) if self.can_put_item(loc)]
        assert len(locs) == len(non_progs)
        for i in range(len(locs)):
            locs[i].item = non_progs[i]

    def check(self) -> bool:
        locs = self.reachable_locations([], True)
        found_main = False
        for loc in locs:
            if loc.item and loc.item.code == MAIN:
                found_main = True
                break
        return found_main

    def roll(self, _seed: int) -> None:
        seed(_seed)
        success = False
        fail_count = 0
        timeout = time.time() + 15
        while not success and time.time() < timeout:
            try:
                self.assume_fill()
            except Randomizer.RollFail:
                fail_count += 1
                self.logger.spoil(f"algorithm fail {fail_count}")
                self.reset()
                continue
            if self.check():
                success = True
            else:
                print("WARNING: check failed when algorithm didn't see failure")
        if not success:
            raise Randomizer.RollFail(f"roll attempts timed out with {fail_count} failures")
