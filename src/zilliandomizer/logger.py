from typing import List


class Logger:
    def __init__(self) -> None:
        self.spoiler_lines: List[str] = []
        self.spoil_stdout: bool = True
        self.debug_stdout: bool = False

    def spoil(self, line: str) -> None:
        self.spoiler_lines.append(line)
        if self.spoil_stdout:
            print(line)

    def debug(self, line: str) -> None:
        if self.debug_stdout:
            print(line)

    def warn(self, line: str) -> None:
        print(line)
