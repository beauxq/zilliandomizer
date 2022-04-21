from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Literal, Tuple

Chars = Literal["JJ", "Apple", "Champ"]
VBLR = Literal["vanilla", "balanced", "low", "restrictive"]
""" `"vanilla"` `"balanced"` `"low"` `"restrictive"` """

chars: Tuple[Chars, Chars, Chars] = ("JJ", "Champ", "Apple")  # order in rom data


class ID(IntEnum):
    """ item ids used in rom """
    key0 = 0
    key1 = 1
    key2 = 2
    key3 = 3
    empty = 4
    card = 5
    red = 6
    floppy = 7
    bread = 8
    opa = 9
    gun = 10
    scope = 11


ItemCounts = Dict[ID, int]


@dataclass  # TODO: python 3.10 (kw_only=True)
class Options:
    item_counts: ItemCounts
    """ ids 5 through 11 """
    jump: VBLR
    gun: VBLR
    opas_per_level: int
    max_level: int
    tutorial: bool
    skill: int
    start_char: Chars
    floppy_req: int
    """ how many floppies are required """
    # TODO: hp - ? low2low(start low end low) low2high(start low end vanilla) high2low(vanilla)


char_to_hp: Dict[Chars, int] = {
    "JJ": 700,
    "Apple": 600,
    "Champ": 800
}

char_to_gun: Dict[Chars, Dict[VBLR, List[int]]] = {
    "JJ": {
        "vanilla": [1, 2, 3],
        "balanced": [1, 2, 2, 3],
        "low": [1, 1, 2, 2, 2, 3],
        "restrictive": [1, 1, 2]
    },
    "Apple": {
        "vanilla": [1, 2, 3],
        "balanced": [1, 1, 2, 2, 3],
        "low": [1, 1, 1, 1, 2, 2, 3],
        "restrictive": [1, 1, 1, 1, 2]
    },
    "Champ": {
        "vanilla": [3],
        "balanced": [2, 2, 3],
        "low": [1, 2, 2, 3],
        "restrictive": [1, 2, 2, 3]
    }
}
"""
```
zillion power

vanilla         balanced        low             restrictive

jj  ap  ch      jj  ap  ch      jj  ap  ch      jj  ap  ch
1   1   3       1   1   2       1   1   1       1   1   1
2   2   3       2   1   2       1   1   2       1   1   2
3   3   3       2   2   3       2   1   2       2   1   2
                3   2   3       2   1   3       2   1   3
                3   3   3       2   2   3       2   2   3
                                3   2   3
                                3   3   3
```
"""

char_to_jump: Dict[Chars, Dict[VBLR, List[int]]] = {
    "JJ": {
        "vanilla": [2, 2, 2, 2, 3, 3, 3, 3],
        "balanced": [1, 2, 2, 2, 3, 3, 3, 3],
        "low": [1, 1, 2, 2, 2, 3, 3, 3],
        "restrictive": [1, 1, 1, 1, 2, 2, 2, 2]
    },
    "Apple": {
        "vanilla": [3, 3, 3, 3, 3, 3, 3, 3],
        "balanced": [2, 2, 3, 3, 3, 3, 3, 3],
        "low": [1, 2, 2, 3, 3, 3, 3, 3],
        "restrictive": [1, 1, 2, 2, 2, 2, 3, 3]
    },
    "Champ": {
        "vanilla": [1, 1, 1, 1, 2, 2, 3, 3],
        "balanced": [1, 1, 1, 2, 2, 2, 3, 3],
        "low": [1, 1, 1, 1, 2, 2, 2, 3],
        "restrictive": [1, 1, 1, 1, 1, 1, 1, 2]
    }
}
"""
```
vanilla         balanced        low             restrictive

jj  ap  ch      jj  ap  ch      jj  ap  ch      jj  ap  ch
2   3   1       1   2   1       1   1   1       1   1   1
2   3   1       2   2   1       1   2   1       1   1   1
2   3   1       2   3   1       2   2   1       1   2   1
2   3   1       2   3   2       2   3   1       1   2   1
3   3   2       3   3   2       2   3   2       2   2   1
3   3   2       ---------       3   3   2       2   2   1
3   3   3       3   3   3       ---------       2   3   1
3   3   3       ---------       3   3   3       2   3   2
```
"""
