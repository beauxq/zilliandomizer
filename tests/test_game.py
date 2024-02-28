import json

from zilliandomizer.game import Game
from zilliandomizer.options import Options
from zilliandomizer.randomizer import Randomizer
from zilliandomizer.resource_managers import ResourceManagers


def test_to_from_json() -> None:
    o = Options()
    rm = ResourceManagers()
    r = Randomizer(o)
    r.roll()

    game_before = Game(o, rm.escape_time, rm.char_order, r.loc_name_2_pretty, r.get_region_data(), rm.get_writes())

    dict_before = game_before.to_jsonable()

    json_data = json.dumps(dict_before)

    dict_after = json.loads(json_data)

    game_after = Game.from_jsonable(dict_after)

    assert game_before.options == game_after.options, f"\n{game_before.options}\n{game_after.options}"
    assert game_before.escape_time == game_after.escape_time
    assert game_before.char_order == game_after.char_order
    assert game_before.loc_name_2_pretty == game_after.loc_name_2_pretty
    assert game_before.regions == game_after.regions, f"\n{game_before.regions[1]}\n{game_after.regions[1]}"
    assert game_before.resource_writes == game_after.resource_writes, (
        f"{len(game_before.resource_writes)} {len(game_after.resource_writes)}"
    )

    assert game_before == game_after


if __name__ == "__main__":
    test_to_from_json()
