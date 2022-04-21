# zilliandomizer
--------------

![Tests](https://github.com/beauxq/zilliandomizer/actions/workflows/tests.yml/badge.svg)

---

Zillion is a metroidvania style game released in 1987 for the 8-bit Sega Master System.

It's based on the anime Zillion (赤い光弾ジリオン, Akai Koudan Zillion).

This is a randomizer for this game.

---

To use:

install [https://www.python.org/](https://www.python.org/)

download this code

put the original US/NTSC rom in the `roms` directory with this filename: `Zillion (UE) [!].sms`

edit `options.yaml` in the same directory as the rom

run `src/generate.py`

The randomized rom will output into the same directory as the original rom (with the seed number in the filename)

---

gameplay customizations:

Letting the player choose who to level up has a few drawbacks:
 - possible softlock from making bad choices (example: nobody has jump 3 when it's required)
 - In multiworld (Archipelago support coming soon), you won't be able to choose because you won't know it's coming beforehand.

So with this new system:
 - Everyone levels up together (even if they're not rescued yet).
 - You can choose how many opa-opas are required for a level up.
 - You can set a max level from 1 to 8.
 - The currently active character is still the only one that gets the health refill.
   - In the future, this might change to choose based on missing (effective) health, and/or an option to refill everyone.

---

You can set these options to choose when characters will be able to attain certain jump levels:

```
jump levels

vanilla         balanced        low             restrictive

jj  ap  ch      jj  ap  ch      jj  ap  ch      jj  ap  ch
2   3   1       1   2   1       1   1   1       1   1   1
2   3   1       2   2   1       1   2   1       1   1   1
2   3   1       2   3   1       2   2   1       1   2   1
2   3   1       2   3   2       2   3   1       1   2   1
3   3   2       3   3   2       2   3   2       2   2   1
3   3   2       3   3   2       3   3   2       2   2   1
3   3   3       3   3   3       3   3   2       2   3   1
3   3   3       3   3   3       3   3   3       2   3   2
```

Note that in "restrictive" mode, Apple is the only one that can get jump level 3.

---

You can set these options to choose when characters will be able to attain certain Zillion power (gun) levels:

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

Note that in "restrictive" mode, Champ is the only one that can get Zillion power level 3.
