import os
from zilliandomizer.alarms import Alarms
from zilliandomizer.randomizer import Randomizer
from zilliandomizer.options import Options, ID
from zilliandomizer.options.parsing import parse_options
from zilliandomizer.logger import Logger
from zilliandomizer.patch import Patcher

some_options = Options(item_counts={
    ID.card: 50,
    ID.bread: 35,
    ID.opa: 26,
    ID.gun: 9,
    ID.floppy: 8,
    ID.scope: 4,
    ID.red: 2
}, jump_levels="balanced", gun_levels="balanced", opas_per_level=2, max_level=8, tutorial=False,
    skill=2, start_char="JJ", floppy_req=5)
""" default options if no options.yaml """


def generate(seed: int) -> None:
    seed_str = f"{seed:016x}"
    p = Patcher()
    options: Options = some_options
    options_file = p.rom_path + os.sep + "options.yaml"
    if os.path.exists(options_file):
        print(f"found options file: {options_file}")
        with open(options_file) as file:
            options = parse_options(file.read())
    else:
        print("no options file found, using default")
    logger = Logger()
    logger.spoil_stdout = False
    logger.spoil(str(options))
    logger.spoil(f"seed {seed_str}")
    r = Randomizer(options, logger)
    r.roll(seed)

    if options.randomize_alarms:
        a = Alarms(p.tc, logger)
        a.choose_all()

    p.write_locations(r.locations, options.start_char)
    p.all_fixes_and_options(options)
    filename = f"zilliandomizer-{seed_str}.sms"
    p.write(filename)
    # TODO: abstract out the spoiler writer (handling directory in a better way)
    with open(p.rom_path + os.sep + f"spoiler-{seed_str}.txt", "wt") as file:
        for line in logger.spoiler_lines:
            file.write(line + "\n")
    print(f"generated: {filename}")
