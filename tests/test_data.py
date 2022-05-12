from zilliandomizer.logic_components.location_data import make_locations
from zilliandomizer.logic_components.region_data import make_regions


def test_make_locations_and_regions() -> None:
    locations = make_locations()
    make_regions(locations)
