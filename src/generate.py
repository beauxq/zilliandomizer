import os
from random import randrange
import sys
from zilliandomizer.randomizer import Randomizer, some_options
from zilliandomizer.options import Options, parse_options
from zilliandomizer.logger import Logger
from zilliandomizer.patch import Patcher


def generate(seed: int) -> None:
    seed_str = f"{seed:016x}"
    p = Patcher()
    options: Options = some_options
    options_file = p.rom_path + os.sep + "options.yaml"
    if os.path.exists(options_file):
        print(f"found options file: {options_file}")
        with open(options_file) as file:
            options = parse_options(file.read())
    logger = Logger()
    logger.stdout = False
    logger.log(str(options))
    logger.log(f"seed {seed_str}")
    r = Randomizer(options, logger)
    r.roll(seed)

    p.write_locations(r.locations)
    p.all_fixes_and_options(options)
    filename = f"zilliandomizer-{seed_str}.sms"
    p.write(filename)
    # TODO: abstract out the spoiler writer (handling directory in a better way)
    with open(p.rom_path + os.sep + f"spoiler-{seed_str}.txt", "wt") as file:
        for line in logger.lines:
            file.write(line + "\n")
    print(f"generated: {filename}")


def main() -> None:
    if len(sys.argv) > 1:
        seed = int(sys.argv[1], 16)
    else:
        seed = randrange(0x10000000000000000)
    generate(seed)


if __name__ == "__main__":
    main()
