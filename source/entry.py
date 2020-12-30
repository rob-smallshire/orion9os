from asm68.asmdsl import AsmDsl
from asm68.mnemonics import (FDB, ORG, NOP, JMP, LDA, STA, BITA, BEQ, CALL)

asm = AsmDsl()

aciacr = 0xA000  # 6850 control register
aciasr = 0xA000
aciadr = 0xA001


def pad_until(address):

    def do_pad_until(assembler):

        while assembler.pos != address:
            stmt = asm.statement(NOP)
            assembler.assemble_statement(stmt)

    return do_pad_until


# With a 153.600 kHz ACIA clock divided by 64 to give 2400 baud
# a continuous stream of "h" characters can be read with the picocom
# command:
#
#  picocom /dev/tty.usbserial-AI02KM9Y -b2400 -ye -d7 -p1


asm         (   ORG,    0xC000,         "Bottom of the top 16 K ROM"    )

asm .BEGIN  (   NOP,                    "Do nothing"                    )
asm         (   NOP,                    "Do nothing"                    )
asm         (   NOP,                    "Do nothing"                    )
asm         (   LDA,    0b00000011,     "Master reset ACIA"             )
asm         (   STA,    {aciacr}                                        )
asm         (   LDA,    0b00001010,     "ACIA Operating mode -- 7e1 - div 64" )
asm         (   STA,    {aciacr}                                        )
asm .SEND   (   LDA,    0b00000010,     "Transmitter status flag"       )
asm .WAITR  (   BITA,   {aciasr},       "Test flag"                     )
asm         (   BEQ,    asm.WAITR,      "Branch if flag not set"        )
asm         (   LDA,    ord("h"),       "Load 'H' into A"               )
asm         (   STA,    {aciadr},       "Transmit character"            )
asm         (   JMP,    {asm.SEND},     "Send another character"        )
asm         (   CALL,   pad_until(address=0xFFFF - 16 - 3 + 1)          )
asm         (   CALL,   print                                           )

asm         (   JMP,    {asm.BEGIN},    "Jump back to the bottom"       )

# Vector table at top of memory
asm         (   FDB,   (0xC000,     # Reserved
                        0xC000,     # SWI3
                        0xC000,     # SWI2
                        0xC000,     # /FIRQ
                        0xC000,     # /IRQ
                        0xC000,     # SWI
                        0xC000,     # /NMI
                        0xC000)     # /RESET
            )

# Notes

# Point /IRQ interrupt handling vector at .IRQ

# In .RESET setup
# - An input buffer in page 0x03.
#    Store the buffer pointers in page 0

# - A output buffer in page 0x04.
#    Store the buffer pointers in page 0

# Configure the 6850

# .MAIN
#
# If the input buffer is not empty
#   Copy data from the input buffer into the output buffer


# .IRQ

#
