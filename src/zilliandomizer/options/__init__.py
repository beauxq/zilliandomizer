from dataclasses import dataclass, field
from enum import IntEnum
from random import choice
from typing import Dict, List, Literal, NoReturn, Tuple

Chars = Literal["JJ", "Apple", "Champ"]
VBLR = Literal["vanilla", "balanced", "low", "restrictive"]  # unpack operator in subscript require Python 3.11
""" `"vanilla"` `"balanced"` `"low"` `"restrictive"` """

VBLR_CHOICES: Tuple[VBLR, ...] = ("vanilla", "balanced", "low", "restrictive")
chars: Tuple[Chars, Chars, Chars] = ("JJ", "Champ", "Apple")
""" order in rom data """

options_filename = "options.yaml"


def error(s: str) -> NoReturn:
    raise ValueError(f"{options_filename}: {s}")


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

default_item_counts: ItemCounts = {
    ID.card: 50,
    ID.bread: 35,
    ID.opa: 26,
    ID.gun: 10,
    ID.floppy: 7,
    ID.scope: 4,
    ID.red: 2
}


def item_counts_factory() -> ItemCounts:
    """ default factory for dataclass item_counts """
    tr: ItemCounts = {}
    for id in default_item_counts:
        tr[id] = default_item_counts[id]
    return tr


def start_char_factory() -> Chars:
    """ default factory for dataclass start_char """
    return choice(chars)


@dataclass  # TODO: python 3.10 (kw_only=True)
class Options:
    item_counts: ItemCounts = field(default_factory=item_counts_factory)
    """ ids 5 through 11 """
    jump_levels: VBLR = "balanced"
    gun_levels: VBLR = "balanced"
    opas_per_level: int = 2
    """ how many opa-opas are required to level up """
    max_level: int = 8
    """ the highest level you can get """
    tutorial: bool = False
    skill: int = 2
    start_char: Chars = field(default_factory=start_char_factory)
    """ which character you start with """
    floppy_req: int = 5
    """ how many floppies are required """
    continues: int = -1
    """ number of continues before game over, -1 for infinity """
    randomize_alarms: bool = True
    """ whether to randomize the locations of alarm sensors """
    early_scope: bool = False
    """ whether to make sure there is a scope available early """
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
