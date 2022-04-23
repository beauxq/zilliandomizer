from random import randrange
import sys
from zilliandomizer.generator import generate


def main() -> None:
    if len(sys.argv) > 1:
        seed = int(sys.argv[1], 16)
    else:
        seed = randrange(0x10000000000000000)
    generate(seed)


if __name__ == "__main__":
    main()
