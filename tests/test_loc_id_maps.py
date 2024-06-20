from zilliandomizer.utils.loc_name_maps import loc_to_id, id_to_loc
from zilliandomizer.randomizer import Randomizer
from zilliandomizer.generator import some_options


def test_cross() -> None:
    for loc, id in loc_to_id.items():
        assert id_to_loc[id] == loc

    for id, loc in id_to_loc.items():
        assert loc_to_id[loc] == id


def test_with_data() -> None:
    r = Randomizer(some_options, None, None)
    # need to have ids for locations that are not in vanilla
    # for loc in loc_to_id:
    #     assert loc in r.locations
    for loc in r.loc_name_2_pretty.values():
        if loc != 'main':
            assert loc in loc_to_id
