from zilliandomizer.options import parse_options, ID, VBLR_CHOICES, chars


def test_parse() -> None:
    t = """
    jump_levels: random
    gun_levels: restrictive
    opas_per_level: 3
    max_level:random
    tutorial: False
    start_char:  random
    floppy_req:3
    """
    o = parse_options(t)
    assert o.jump_levels in VBLR_CHOICES
    assert o.gun_levels == "restrictive"
    assert o.opas_per_level == 3
    assert 1 <= o.max_level <= 8
    assert o.tutorial is False
    assert o.start_char in chars
    assert o.floppy_req == 3


def test_parse_item_counts() -> None:
    t = """
    max_level: 2
    item_counts:
      card: 70
      opa: 27
      gun: 5
    start_char: Apple
    """
    o = parse_options(t)
    assert o.max_level == 2
    assert o.item_counts[ID.card] == 70
    assert o.item_counts[ID.opa] == 27
    assert o.item_counts[ID.gun] == 5
    assert o.start_char == "Apple"


# TODO: test parse exceptions
