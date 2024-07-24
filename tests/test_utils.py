import pytest

from zilliandomizer.utils.deterministic_set import DetSet
from zilliandomizer.utils.disjoint_set import DisjointSet


def test_deterministic_set() -> None:
    ds = DetSet([30, 40, 50])

    listed = list(ds)
    assert listed == [30, 40, 50], f"{listed=}"

    ds.add(50)
    assert len(ds) == 3

    ds.add(6)
    listed = list(ds)
    assert listed == [30, 40, 50, 6], f"{listed=}"

    ds.discard(40)
    listed = list(ds)
    assert listed == [30, 50, 6], f"{listed=}"

    assert 40 not in ds
    assert 700 not in ds
    assert 700 not in ds

    ds.discard(3)
    listed = list(ds)
    assert listed == [30, 50, 6], f"{listed=}"

    with pytest.raises(KeyError):
        ds.remove(3)

    ds2 = ds.copy()
    assert ds2 == ds
    assert ds2 is not ds

    assert ds[1] == 50, f"{ds[1]}"

    # test pop
    ds = DetSet([700, 68000, 2])
    assert 2 in ds
    x = ds.pop()
    assert x == 700, f"{x=}"
    assert 700 not in ds, f"{ds=}"


def test_disjoint_set() -> None:
    uf: DisjointSet[int] = DisjointSet()

    three = uf.find(3)
    assert three == 3, f"{three=}"
    four = uf.find(4)
    assert four == 4, f"{four=}"

    uf.union(3, 4)

    a = uf.find(3)
    b = uf.find(4)
    assert a == b, f"{a=} {b=}"

    # also test transitivity
    a = uf.find(3)
    c = uf.find(2)
    assert a != c, f"{a=} {c=}"

    uf.union(2, 4)
    a = uf.find(3)
    c = uf.find(2)
    assert a == c, f"{a=} {c=}"


if __name__ == "__main__":
    test_deterministic_set()
    test_disjoint_set()
