doors = {
    10: [b'\x00\x01<\x00\x00'],
    13: [b'\x00\x02(\x00\x00', b'\x00\x042\x00\x05'],
    15: [b'\x01\x01\x04\x05\x1e'],
    23: [b'\x01\x01\x04\x00\x1f'],
    26: [b'\x02\x01\x02\x04\x05', b'\x02\x02\x18\x05\x1e'],
    27: [b'\x03\x01\x02\x04\x05'],
    28: [b'\x04\x01\x02\x04\x05'],
    29: [b'\x05\x01\x02\x04\x05'],
    33: [b'\x06\x018\x04\x00'],
    34: [b'\x02\x02\x18\x00\x1f', b'\x07\x01<\x04\x00'],
    36: [b'\x08\x01<\x00\x00'],
    37: [b'\t\x01<\x04\x00'],
    41: [b'\n\x01\x02\x04\x0f', b'\n\x02 \x05 '],
    43: [b'\x0b\x01\x08\x05 ', b'\x0b\x02<\x04\n'],
    44: [b'\x0c\x012\x00\x0f'],
    47: [b'\r\x014\x05 '],
    49: [b'\n\x02 \x00!', b'\x0e\x014\x05 '],
    51: [b'\x0b\x01\x08\x00!', b'\x0f\x01\x02\x04\x0f'],
    52: [b'\x10\x01\x02\x04\x0f'],
    54: [b'\x11\x01\x02\x04\x0f', b'\x11\x024\x05 '],
    55: [b'\x12\x01\x02\x04\x0f', b'\r\x014\x00!'],
    57: [b'\x0e\x014\x00!', b'\x13\x01\x04\x05 ', b'\x14\x01\x02\x04\x0f'],
    59: [b'\x15\x01\x08\x05 '],
    61: [b'\x15\x02\x02\x04\x0f'],
    62: [b'\x16\x01\x02\x04\x0f', b'\x16\x02<\x04\n', b'\x11\x024\x00!'],
    63: [b'\x17\x014\x05 '],
    65: [b'\x13\x01\x04\x00!', b'\x13\x014\x05 '],
    67: [b'\x15\x01\x08\x00!', b'\x19\x02\x02\x04\x0f'],
    68: [b'\x1a\x02\x18\x05 '],
    69: [b'\x1b\x01\x02\x04\x0f'],
    70: [b'\x1c\x01\x02\x00\x0f'],
    71: [b'\x17\x014\x00!', b'\x1d\x01\x02\x04\x0f'],
    73: [b'\x13\x014\x00!'],
    75: [b'\x1e\x01\x06\x04\x0f'],
    76: [b'\x1a\x02\x18\x00!', b'\x1f\x01\x02\x04\x0f', b'\x1f\x02<\x04\n'],
    77: [b' \x01<\x04\n'],
    81: [b'%\x01\x0c\x05"'],
    82: [b'"\x014\x05"', b'"\x02\x02\x04\x19', b'"\x04<\x04\x14'],
    83: [b'#\x02<\x04\x14', b'"\x04\x02\x04\x19'],
    84: [b'$\x01\x18\x05"', b'$\x02\x02\x00\x19'],
    89: [b'%\x01\x0c\x00#'],
    90: [b'"\x014\x00#', b'%\x01\x02\x00\x19'],
    91: [b'&\x01\x02\x04\x19', b'&\x02<\x04\x14', b'&\x04\x0c\x05"'],
    92: [b'$\x01\x18\x00#', b"'\x01<\x04\x14"],
    93: [b'(\x01<\x04\x14'],
    94: [b')\x01\x02\x00\x19', b')\x024\x05"'],
    97: [b'*\x014\x05"'],
    98: [b'+\x014\x05"', b'+\x02<\x04\x14'],
    99: [b'&\x04\x0c\x00#', b',\x01<\x04\x14'],
    100: [b'-\x01<\x00\x14'],
    101: [b'.\x01<\x00\x14', b'.\x02<\x04\x14', b'.\x04\x08\x05"'],
    102: [b')\x024\x00#'],
    105: [b'*\x014\x00#'],
    106: [b'+\x014\x00#', b'/\x01\x02\x04\x19'],
    107: [b'0\x01\x08\x05"', b'0\x02\x02\x00\x19'],
    108: [b'1\x01\x08\x05"', b'1\x02\x02\x00\x19', b'1\x04<\x04\x14'],
    109: [b'.\x04\x08\x00#', b'2\x014\x05"', b'2\x02&\x04\x19'],
    110: [b'3\x014\x05"'],
    114: [b'4\x01\x08\x05"', b'4\x02\x02\x04\x19', b'4\x04<\x04\x14'],
    115: [b'0\x01\x08\x00#', b'5\x01\x08\x05"', b'5\x02<\x04\x14'],
    116: [b'1\x01\x08\x00#', b'6\x014\x05"'],
    117: [b'2\x014\x00#', b'7\x01\x08\x05"'],
    118: [b'3\x014\x00#', b'8\x01<\x04\x14', b'8\x02\x08\x05"'],
    122: [b'4\x01\x08\x00#', b'9\x014\x05"'],
    123: [b'5\x01\x08\x00#', b':\x01\x02\x04\x19'],
    124: [b'6\x014\x00#', b';\x01\x02\x04\x19'],
    125: [b'7\x01\x08\x00#', b'<\x01<\x04\x14'],
    126: [b'8\x02\x08\x00#', b'<\x02\x12\x00\x19'],
    130: [b'9\x014\x00#', b'=\x01<\x04\x14'],
}
