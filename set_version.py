#!/usr/bin/env python3

"""
Run this in a pre-commit git hook.

(Don't make this script the pre-commit git hook,
 because that would be in the wrong directory.
 It needs to be in this directory.)
"""

from datetime import datetime, timezone
import os
import shlex
from subprocess import check_output, getoutput
import sys
import zlib

VERSION_FILE_NAME = 'src/zilliandomizer/ver.py'


def main() -> None:
    dir_name = os.path.dirname(os.path.abspath(__file__))
    os.chdir(dir_name)

    # make sure everything in src is staged
    git_status = getoutput('git status')
    changes_index = git_status.find('Changes not staged for commit:')
    if changes_index == -1:
        changes_index = len(git_status) - 1
    untracked_index = git_status.find('Untracked files:')
    if untracked_index == -1:
        untracked_index = len(git_status) - 1
    index = min(changes_index, untracked_index)
    src_index = git_status.find(' src/', index)
    if src_index != -1:
        lines = git_status[src_index:].splitlines()
        print(f"error: unstaged {lines[0]}")
        sys.exit(1)

    src_file_list = getoutput('git ls-files src').splitlines()
    assert len(src_file_list) > 15
    crc = 0
    for file_name in src_file_list:
        if file_name != VERSION_FILE_NAME:
            # print(file_name)
            with open(file_name, 'rb') as file:
                crc = zlib.crc32(file.read(), crc)
    text = f"version_hash = \"{format(crc, '02x')}\"\ndate = \"{datetime.now(timezone.utc)}\"\n"
    with open(VERSION_FILE_NAME, 'w') as file:
        file.write(text)
    check_output(shlex.split(f'git add {VERSION_FILE_NAME}'))


if __name__ == "__main__":
    main()
