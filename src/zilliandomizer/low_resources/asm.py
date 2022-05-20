""" z80 machine code instructions used """

LDHL = 0x21
""" load into hl these 2 bytes """
LDAVHL = 0x7e
""" load into a the value at memory address hl """
LDVHLI = 0x36
""" load into address at hl, the immediate byte value """
LDAV = 0x3a
""" load into a, value at memory """
LDVA = 0x32
""" copy a into memory at """
LDAI = 0x3e
""" load into a, the immediate byte value """
LDBI = 0x06
""" load into b, the immediate byte value """
LDCA = 0x4F
""" load into c, value in a """
LDCI = 0x0e
""" load into c, immediate value """
LDDE = 0x11
""" load into de, immediate value """
INCA = 0x3c
""" increment a """
INCHL = 0x23
""" increment the (usually address) value in register hl """
INCVHL = 0x34
""" increment the value at memory hl """
ADDAA = 0x87
""" add a to a (a = 2 * a) """
ADDAC = 0x81
""" add c to a (a = a + c) """
ADDAI = 0xc6
""" add immediate value to a """
ADDHLBC = 0x09
""" add bc to hl """
XORA = 0xaf
""" xor a with itself (putting 0 in a) """
ORA = 0xb7
""" or a with itself (setting zero flag if zero) """
CP = 0xfe
""" compare """
BIT_B_HL_LO = 0xcb
""" test bit b of value in address hl, low byte """
BIT_2_HL_HI = 0x46 | (2 << 3)
""" test bit 2 of value in address hl, high byte """
SET_B_HL_LO = 0xcb
""" set bit b of value in address hl, low byte """
SET_0_HL_HI = 0xc6 | (0 << 3)
""" set bit 0 of value in address hl, high byte """
JRZ = 0x28
""" jump relative if zero """
JRC = 0x38
""" jump relative if carry """
JR = 0x18
""" jump relative """
JP = 0xc3
""" jump """
JPNZ = 0xc2
""" jump if not zero """
JPNC = 0xd2
""" jump if no carry """
JPC = 0xda
""" jump if carry """
CALL = 0xcd
""" subroutine call """
RET = 0xc9
""" return from subroutine """
RETZ = 0xc8
""" return from subroutine if zero flag is set """
RETNZ = 0xc0
""" return from subroutine if zero flag not set """
DAA = 0x27
""" adjust a for binary coded decimal """
NOP = 0x00
""" nop """
PUSHAF = 0xf5
""" push af onto stack """
POPAF = 0xf1
""" pop stack into af """
