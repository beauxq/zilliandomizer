from zilliandomizer.map_gen.door_manager import DoorSprite


def test_door_sprites() -> None:
    assert DoorSprite.get_door(13, 0xf0 >> 2) == DoorSprite.BL
    assert DoorSprite.get_door(23, 0x08 >> 2) == DoorSprite.BR
    assert DoorSprite.get_door(44, 0xc0 >> 2) == DoorSprite.RL
    assert DoorSprite.get_door(79, 0xa8 >> 2) == DoorSprite.RR
    assert DoorSprite.get_door(81, 0xf0 >> 2) == DoorSprite.PL
    assert DoorSprite.get_door(98, 0x08 >> 2) == DoorSprite.PR


def test_elevator_sprites() -> None:
    assert DoorSprite.get_elevator(15, 0) == DoorSprite.BU
    assert DoorSprite.get_elevator(37, 5) == DoorSprite.BD
    assert DoorSprite.get_elevator(51, 0) == DoorSprite.RU
    assert DoorSprite.get_elevator(51, 5) == DoorSprite.RD
    assert DoorSprite.get_elevator(92, 0) == DoorSprite.PU
    assert DoorSprite.get_elevator(93, 5) == DoorSprite.PD
