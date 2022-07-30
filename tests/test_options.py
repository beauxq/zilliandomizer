import pytest
from zilliandomizer.options import ID, VBLR_CHOICES, chars
from zilliandomizer.options.parsing import parse_options


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


def test_parse_continues() -> None:
    t = """
    jump_levels: restrictive
    gun_levels: low
    opas_per_level: random
    max_level: "random"
    tutorial: "False"
    start_char:  random
    floppy_req: random
    continues: infinity
    """

    o = parse_options(t)
    assert o.jump_levels == "restrictive"
    assert o.gun_levels == "low"
    assert o.opas_per_level < 6
    assert 1 <= o.max_level <= 8
    assert o.tutorial is False
    assert o.start_char in chars
    assert o.floppy_req < 127
    assert o.continues == -1

    t = """
    jump_levels: "vanilla"
    gun_levels: "vanilla"
    opas_per_level: 5
    max_level: 1
    tutorial: True
    start_char:  random
    floppy_req: random
    continues: 0
    """

    o = parse_options(t)
    assert o.jump_levels == "vanilla"
    assert o.gun_levels == "vanilla"
    assert o.opas_per_level == 5
    assert o.max_level == 1
    assert o.tutorial is True
    assert o.start_char in chars
    assert o.floppy_req < 127
    assert o.continues == 0

    t = """
    continues: 1
    """

    o = parse_options(t)
    assert o.continues == 1


def test_parse_alarms() -> None:
    t = """
    jump_levels: restrictive
    gun_levels: low
    opas_per_level: random
    max_level: "random"
    tutorial: "False"
    randomize_alarms: "true"
    floppy_req: random
    continues: infinity
    """

    o = parse_options(t)
    assert o.jump_levels == "restrictive"
    assert o.gun_levels == "low"
    assert o.opas_per_level < 6
    assert 1 <= o.max_level <= 8
    assert o.tutorial is False
    assert o.start_char in chars
    assert o.floppy_req < 127
    assert o.continues == -1
    assert o.randomize_alarms is True

    t = """
    randomize_alarms: NO
    gun_levels: "vanilla"
    opas_per_level: 5
    tutorial: True
    start_char:  random
    floppy_req: random
    continues: 0
    """

    o = parse_options(t)
    assert o.randomize_alarms is False
    assert o.gun_levels == "vanilla"
    assert o.opas_per_level == 5
    assert o.tutorial is True
    assert o.start_char in chars
    assert o.floppy_req < 127
    assert o.continues == 0

    t = """
    randomize_alarms: NO
    gun_levels: "vanilla"
    opas_per_level: 5
    balance_defense: false
    start_char:  random
    floppy_req: random
    continues: 0
    """

    o = parse_options(t)
    assert o.randomize_alarms is False
    assert o.gun_levels == "vanilla"
    assert o.opas_per_level == 5
    assert o.balance_defense is False
    assert o.start_char in chars
    assert o.floppy_req < 127
    assert o.continues == 0

    t = """
    randomize_alarms: yes
    """

    o = parse_options(t)
    assert o.randomize_alarms is True


def test_parse_early_scope() -> None:
    t = """
    jump_levels: restrictive
    gun_levels: low
    opas_per_level: random
    max_level: "random"
    tutorial: "False"
    randomize_alarms: "true"
    floppy_req: random
    early_scope : "yes"
    """

    o = parse_options(t)
    assert o.jump_levels == "restrictive"
    assert o.gun_levels == "low"
    assert o.opas_per_level < 6
    assert 1 <= o.max_level <= 8
    assert o.tutorial is False
    assert o.start_char in chars
    assert o.floppy_req < 127
    assert o.early_scope is True
    assert o.randomize_alarms is True

    t = """
    randomize_alarms: NO
    gun_levels: "vanilla"
    opas_per_level: 1
    early_scope: nah
    start_char:  random
    floppy_req: random
    continues: 0
    """

    o = parse_options(t)
    assert o.randomize_alarms is False
    assert o.gun_levels == "vanilla"
    assert o.opas_per_level == 1
    assert o.early_scope is False
    assert o.start_char in chars
    assert o.floppy_req < 127
    assert o.continues == 0

    t = """
    early_scope: True
    """

    o = parse_options(t)
    assert o.early_scope is True


def test_parse_item_counts() -> None:
    t = """
    max_level: 3
    item_counts:
      card: 70
      opa: 27
      gun: 5
      floppy: 6
    start_char: Apple
    """
    o = parse_options(t)
    assert o.max_level == 3
    assert o.item_counts[ID.card] == 70
    assert o.item_counts[ID.opa] == 27
    assert o.item_counts[ID.gun] == 5
    assert o.start_char == "Apple"


def test_options_exceptions() -> None:
    with pytest.raises(ValueError):
        parse_options("""
        min_level:3
        """)

    with pytest.raises(ValueError):
        parse_options("""
        max_level: -3
        """)

    with pytest.raises(ValueError):
        parse_options("""
        max_level: 9
        """)

    with pytest.raises(ValueError):
        parse_options("""
        max_level : 4 : 5
        """)

    with pytest.raises(ValueError):
        parse_options("""
        hello
        """)

    with pytest.raises(ValueError):
        parse_options("""
        max_level = 8
        """)
    # TODO: make = valid?

    with pytest.raises(ValueError):
        # should be gun_level: balanced
        parse_options("""
        gun: balanced
        """)

    # TODO: fix
    # with pytest.raises(TypeError):
    #     # should be wrong type
    #     parse_options("""
    #     balance_defense: 2
    #     """)

    with pytest.raises(ValueError):
        parse_options("""
        hello: 3
        """)

    with pytest.raises(ValueError):
        parse_options("""
        item_counts:
          bomb: 10
        """)

    with pytest.raises(ValueError):
        parse_options("""
        item_counts:
          gun: apple
        """)


def test_validation_errors() -> None:
    # too many items
    with pytest.raises(ValueError):
        parse_options("""
        item_counts:
          opa: 50
          gun: 50
          floppy: 50
        """)

    # if default jump_levels is balanced, max_level 2 doesn't allow jump 3
    with pytest.raises(ValueError):
        parse_options("""
        max_level: 2
        item_counts:
          card: 70
          opa: 27
          gun: 5
        start_char: Apple
        """)
