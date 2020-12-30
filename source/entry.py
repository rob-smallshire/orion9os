from asm68.asmdsl import AsmDsl
from asm68.mnemonics import (
    FDB, ORG, NOP, JMP, LDA, STA, BITA, BEQ, CALL, LDS, JSR, RTS, RTI,
    LDMD
)

asm = AsmDsl()

# With a 153.600 kHz ACIA clock divided by 64 to give 2400 baud
# a continuous stream of "h" characters can be read with the picocom
# command:
#
#  picocom /dev/tty.usbserial-AI02KM9Y -b2400 -ye -d7 -p1


# Memory Map
# 0x00__ Zero page

# 0x01__ System stack

# The 6809 Stack grows downward (toward lower addresses); the Stack Pointer always contains the
# address of the last occupied location, rather than the next empty one as on some other
# microprocessors (including the 6800 and 6502). This means you must initialize the Stack Pointer
# to a value one higher than the largest address in the Stack area (e.g., initializing the Stack
# Pointer to 0100 16 means that the largest address in the Stack area will be 00FF ).

system_stack_page = 0x01
system_stack_size = 0xFF
system_stack_base = (system_stack_page << 8) + system_stack_size + 1

# 0x02__ OS workspace
os_work_page = 0x20
acia_control_register_copy = (os_work_page << 8) + 0x50


aciacr = 0xA000  # 6850 control register
aciasr = 0xA000
aciadr = 0xA001


asm         (   ORG,    0xC000,         "Bottom of the top 16 K ROM"    )

asm .ACIA_RESET (   LDA,    0b00000011,     "Master reset ACIA"         )
asm             (   STA,    {aciacr}                                    )
asm             (   RTS                                                 )

asm .ACIA_MODE  (   LDA,    0b00001010,     "ACIA Operating mode -- 7e1 - div 64"   )
asm             (   STA,    {aciacr}                                                )
asm             (   RTS                                                             )

asm .RESET  (   LDMD,   0b00000001,     "Enter native 6309 mode"    )
asm         (   LDS,    system_stack_base, "Setup system stack"         )
asm         (   NOP,                    "Do nothing"                    )
asm         (   JSR,    {asm.ACIA_RESET}, "Master reset ACIA"             )
asm         (   JSR,    {asm.ACIA_MODE},  "Set ACIA mode"                 )

asm .SEND   (   LDA,    0b00000010,     "Transmitter status flag"       )
asm .WAITR  (   BITA,   {aciasr},       "Test flag"                     )
asm         (   BEQ,    asm.WAITR,      "Branch if flag not set"        )
asm         (   LDA,    ord("h"),       "Load 'H' into A"               )
asm         (   STA,    {aciadr},       "Transmit character"            )
asm         (   JMP,    {asm.SEND},     "Send another character"        )
asm .END    (   JMP,    {asm.RESET},    "Jump back to the bottom"       )
asm         (   CALL,   print                                           )


asm .IRQ    (   RTI,                    "Return from interrupt")

asm .TRAP   (   JMP,    {asm.RESET},    "TODO: Check for division by zero or bad instruction")


# Vector table at top of memory
asm         (   ORG,    0xFFF0,         "Bottom of the top 16 K ROM"    )
asm         (   FDB,   (asm.TRAP,   # TRAP (6309)
                        0xC000,     # SWI3
                        0xC000,     # SWI2
                        0xC000,     # /FIRQ
                        asm.IRQ,    # /IRQ
                        0xC000,     # SWI
                        0xC000,     # /NMI
                        asm.RESET,  # /RESET
                        ))


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
