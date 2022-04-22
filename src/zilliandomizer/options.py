from dataclasses import dataclass, field
from enum import IntEnum
from random import choice
from typing import Any, Dict, List, Literal, Tuple

VBLR_CHOICES = ("vanilla", "balanced", "low", "restrictive")
Chars = Literal["JJ", "Apple", "Champ"]
VBLR = Literal["vanilla", "balanced", "low", "restrictive"]  # unpack operator in subscript require Python 3.11
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

default_item_counts: ItemCounts = {
    ID.card: 50,
    ID.bread: 35,
    ID.opa: 26,
    ID.gun: 10,
    ID.floppy: 7,
    ID.scope: 4,
    ID.red: 2
}


def factory() -> ItemCounts:
    """ default factory for dataclass item_counts """
    tr: ItemCounts = {}
    for id in default_item_counts:
        tr[id] = default_item_counts[id]
    return tr


@dataclass  # TODO: python 3.10 (kw_only=True)
class Options:
    item_counts: ItemCounts = field(default_factory=factory)
    """ ids 5 through 11 """
    jump_levels: VBLR = "balanced"
    gun_levels: VBLR = "balanced"
    opas_per_level: int = 2
    max_level: int = 8
    tutorial: bool = False
    skill: int = 2
    start_char: Chars = "JJ"
    floppy_req: int = 5
    """ how many floppies are required """
    # TODO: hp - ? low2low(start low end low) low2high(start low end vanilla) high2low(vanilla)


# TODO: TypedDict
choices: Dict[str, Any] = {
    "jump_levels": VBLR_CHOICES,
    "gun_levels": VBLR_CHOICES,
    "opas_per_level": (1, 2, 3),
    "max_level": range(1, 9),
    "tutorial": (True, False),
    "skill": range(6),
    "start_char": chars,
    "floppy_req": range(9)
}

sub_options = {
    "item_counts": {
        "card": ID.card,
        "bread": ID.bread,
        "opa": ID.opa,
        "gun": ID.gun,
        "floppy": ID.floppy,
        "scope": ID.scope,
        "red": ID.red
    }
}


def parse_options(t: str) -> Options:
    # mypy doesn't know about __dataclass_fields__
    fields: Dict[str, Any] = Options.__dataclass_fields__  # type: ignore

    def get_typed_value(option: str, value: str) -> Any:
        if value == "random":
            return choice(choices[option])

        typed_value: Any = value
        if fields[option].type is bool:
            typed_value = (value.lower() in ("true", "yes", "on"))
        else:
            try:
                v = fields[option].type(value)
                typed_value = v
            except TypeError:
                # probably type Literal
                pass
        if typed_value not in choices[option]:
            raise ValueError(f"invalid value {value} for {option}")
        return typed_value

    tr = Options()
    parent_option = ""
    for line in t.split("\n"):
        # remove # comments
        try:
            line = line[:line.index("#")]
        except ValueError:
            pass  # no "#"

        line = line.strip()
        if len(line) == 0:
            continue
        split = line.split(":")
        if len(split) != 2:
            raise ValueError(f'invalid line in options: "{line}"')
        option = split[0].strip().strip('"')
        value = split[1].strip().strip('"')
        if option in fields and option not in sub_options:
            parent_option = ""
            typed_value = get_typed_value(option, value)
            tr.__setattr__(option, typed_value)
        elif option in sub_options:
            parent_option = option
        else:
            if parent_option == "":
                raise ValueError(f"invalid option: {option}")
            if option not in sub_options[parent_option]:
                raise ValueError(f"invalid sub-option {option} for option {parent_option}")

            # right now, the only suboption is item_counts
            try:
                int_value = int(value)
            except ValueError:
                raise ValueError(f"invalid value {value} for sub-option {option} under {parent_option}")
            tr.__getattribute__(parent_option)[sub_options[parent_option][option]] = int_value

    return tr


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
