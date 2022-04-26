from typing import Set
from zilliandomizer.locations import Req


def test_req() -> None:
    r1 = Req(skill=4)
    r2 = Req(skill=3) | Req(gun=2)
    assert r1 >= r2
    assert not (r2 >= r1)

    # test union doesn't satisfy requirements
    r3 = Req(skill=2)
    assert not (r2 >= r3)

    # test == only matches same object
    r4 = Req(skill=2)
    assert not (r3 == r4)

    rs: Set[Req] = set()
    rs.add(r3)
    rs.add(r3)
    rs.add(r4)
    assert len(rs) == 2


def test_char_req() -> None:
    """ chars as requirement means at least one of the chars is required """
    no_chars = Req(char=())
    all_chars = Req()
    # if something has a requirement of no chars, it's impossible
    assert not (all_chars >= no_chars)

    apple = Req(char=("Apple", ))
    assert not (apple >= no_chars)
    assert apple >= all_chars
    assert all_chars >= apple

    # there shouldn't be any way for no_chars to be on the left here,
    # because you start the game with 1 char,
    # but test anyway
    assert not (no_chars >= all_chars)
    assert not (no_chars >= apple)

    apple_jj = Req(char=("Apple", "JJ"))
    assert apple >= apple_jj
    assert apple_jj >= apple
    assert apple_jj >= all_chars

    champ = Req(char=("Champ", ))
    assert not (champ >= apple_jj)
    assert not (apple_jj >= champ)


def test_hp_req() -> None:
    have = Req(hp=50)
    req = Req(hp=50)

    # I die if my hp goes to zero
    assert not (have >= req)

    have = Req(hp=60)
    assert have >= req

    have = Req(hp=40)
    assert not (have >= req)


def test_door_req() -> None:
    have = Req()
    have.have_doors.add(7)
    have.have_doors.add(42)

    req = Req(door=13)

    assert not (have >= req)

    req = Req(door=42)

    assert have >= req
