import asyncio

from zilliandomizer.zri.memory import Memory


async def main() -> None:
    m = Memory()
    while True:
        ram = await m.read()
        await m.process_ram(ram)
        await asyncio.sleep(0.09375)


if __name__ == "__main__":
    asyncio.run(main())
