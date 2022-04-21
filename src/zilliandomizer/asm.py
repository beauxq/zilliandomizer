""" z80 machine code instructions used """

LDHL = 0x21
""" load into hl these 2 bytes """
LDAVHL = 0x7e
""" load into a the value at memory address hl """
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
CP = 0xfe
""" compare """
JRZ = 0x28
""" jump relative if zero """
JP = 0xc3
""" jump """
JPNC = 0xd2
""" jump if no carry """
DAA = 0x27
""" adjust a for binary coded decimal """
