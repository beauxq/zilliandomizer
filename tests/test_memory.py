from zilliandomizer.zri.memory import bits, bytes_or


def test_bits() -> None:
    assert list(bits(0)) == []
    assert list(bits(5)) == [1, 4]
    assert list(bits(18)) == [2, 16]


def test_bytes_or() -> None:
    assert bytes_or(b"\x00\xff\x17\x42", b"\x00\x07\x4b\x00") == b"\x00\xff\x5f\x42"
