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
LDBA = 0x47
""" load into b, value in a """
LDCA = 0x4F
""" load into c, value in a """
LDCI = 0x0e
""" load into c, immediate value """
LDDE = 0x11
""" load into de, immediate value """
LDHVHL = 0x66
""" load into h, value at memory address hl """
LDLA = 0x6f
""" load into l, value in a """
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
SUBVHL = 0x96
""" subtract the value at memory hl from a """
ANDN = 0xe6
""" logical byte with a into a """
XORA = 0xaf
""" xor a with itself (putting 0 in a) """
ORA = 0xb7
""" or a with itself (setting zero flag if zero) """
ORC = 0xb1
""" or a with c, into a """
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
JRNZ = 0x20
""" jump relative if not zero """
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
DJNZ = 0x10
""" decrement b and jump relative if not zero """
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
SRL_LO = 0xcb
""" shift right into carry, reset MSB """
SRL_A_HI = 0x3f
""" shift a right into carry, reset MSB """
RST10 = 0xd7
""" call 0x10 (dereference a data table in zillion) """
