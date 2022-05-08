# zilliandomizer
--------------

![Tests](https://github.com/beauxq/zilliandomizer/actions/workflows/tests.yml/badge.svg)

---

Zillion is a metroidvania style game released in 1987 for the 8-bit Sega Master System.

It's based on the anime Zillion (赤い光弾ジリオン, Akai Koudan Zillion).

This is a randomizer for this game.

---

You might be able to find me on the [Randomizer Central discord](https://discord.gg/QeP4wQQBdp) (username beauxq) There's a help-center there to get help with any randomizer. (Most other people there will not be familiar with this randomizer.)

---

## setup / install

1. install Python from [https://www.python.org/](https://www.python.org/)

2. download the code from this page
   1. green "Code" button in the top right portion of this page
   2. "Download ZIP"
   3. unzip it to a folder on your hard drive

3. put your original US/NTSC rom in the `roms` directory with this filename: `Zillion (UE) [!].sms`
   - I think version 1.1 of the rom is needed. (I don't know information about different versions of the rom.)
---

## usage

1. edit `options.yaml` in the same directory as the rom

2. in the `src` directory, run `generate.py`

The randomized rom will output into the same directory as the original rom (with the seed number in the filename).

---

## update

 - It should be enough to delete the old `src` directory and put the new one in it's place.
   - (Merging the new one into the old one could cause problems.)
 - You shouldn't need to overwrite your `roms` directory with your `options.yaml`, but you might want to check out the new `options.yaml` to see what new options are available.

---

## gameplay customizations:

The way the original game lets the player choose who to level up has a few drawbacks in a randomizer:
 - possible softlock from making bad choices (example: nobody has jump 3 when it's required)
 - In multiworld (Archipelago support coming soon), you won't be able to choose because you won't know it's coming beforehand.

So this randomizer uses a new level-up system:
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
