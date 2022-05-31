import asyncio
import time
from zilliandomizer.zri.memory import Memory
from zilliandomizer.zri.events import EventFromGame, EventToGame


def main() -> None:
    q_out: "asyncio.Queue[EventFromGame]" = asyncio.Queue()
    q_in: "asyncio.Queue[EventToGame]" = asyncio.Queue()
    m = Memory(q_out, q_in)
    while True:
        m.check()
        try:
            q_out.get_nowait()
            q_out.task_done()
            q_in.get_nowait()
            q_in.task_done()
        except asyncio.QueueEmpty:
            pass
        time.sleep(0.09375)


if __name__ == "__main__":
    main()
