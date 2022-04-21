import os
from random import choice, randrange
from zilliandomizer.randomizer import Randomizer, some_options
from zilliandomizer.options import Options
from zilliandomizer.logger import Logger
from zilliandomizer.patch import Patcher


def generate() -> None:
    s = randrange(0x10000000000000000)
    options: Options = some_options
    options.start_char = choice(["JJ", "Apple", "Champ"])
    logger = Logger()
    logger.stdout = False
    r = Randomizer(options, logger)
    r.roll(s)

    p = Patcher()
    p.write_locations(r.locations)
    p.all_fixes_and_options(options)
    filename = f"zilliandomizer-{s:016x}.sms"
    p.write(filename)
    # TODO: abstract out the spoiler writer (handling directory in a better way)
    with open(p.rom_path + os.sep + f"spoiler-{s:016x}.txt", "wt") as file:
        for line in logger.lines:
            file.write(line + "\n")
    print(f"generated: {filename}")


if __name__ == "__main__":
    generate()
