from typing import List


class Logger:
    def __init__(self) -> None:
        self.lines: List[str] = []
        self.stdout: bool = True

    def log(self, line: str) -> None:
        self.lines.append(line)
        if self.stdout:
            print(line)
