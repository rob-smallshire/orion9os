from asm68.asmdsl import AsmDsl
from asm68.mnemonics import (
    FDB, ORG, NOP, JMP, LDA, STA, BITA, BEQ, CALL, LDS, JSR, RTS, RTI,
    LDMD,
    FCB, LDX, LDB, STB, CLR, ORCC, ANDCC, LDE, LDF, STE, STF, INCE, INCF, TFR, CMPR, DECF)
from asm68.registers import A, X, E, F, W, Y

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

def word(hi, lo):
    return (hi << 8) | lo

system_stack_page = 0x01
system_stack_size = 0xFF
system_stack_base = (system_stack_page << 8) + system_stack_size + 1

# 0x02__ OS workspace
os_work_page = 0x02

def os_workspace(lo):
    return word(os_work_page, lo)

acia_control_register_copy = os_workspace(0x50)

buffer_input_offset_table_base = os_workspace(0x40)
buffer_output_offset_table_base = os_workspace(0x48)

serial_rx_buffer_number = 0
serial_rx_buffer_page = 0x30
serial_rx_buffer_input_ptr = os_workspace(0x10)
serial_rx_buffer_output_ptr = os_workspace(0x11)


serial_tx_buffer_number = 1
serial_tx_buffer_page = 0x40
serial_tx_buffer_input_ptr = os_workspace(0x12)
serial_tx_buffer_output_ptr = os_workspace(0x13)


aciacr = 0xA000  # 6850 control register
aciasr = 0xA000
aciadr = 0xA001


asm         (   ORG,    0xC000,         "Bottom of the top 16 K ROM"    )

# This table gives the hi-byte (i.e page number) of each of the 256 byte buffers.
asm .BUFFER_HI .SERIAL_RX_BUFFER_PAGE ( FCB, (serial_rx_buffer_page,) )
asm            .SERIAL_TX_BUFFER_PAGE ( FCB, (serial_tx_buffer_page,) )


# Reset Buffer. Buffer index in A.
# Stores zero offset (-127 from the base offset) into the buffer input offset and the buffer output offset
asm .RESET_BUFFER ( LDX, buffer_input_offset_table_base  )
asm               ( LDB, 0x80, "Minimum offset is -127"  )
asm               ( STB, {A:X}                           )
asm               ( LDX, buffer_output_offset_table_base )
asm               ( STB, {A:X}                           )
asm               ( RTS                                  )


# Insert byte in buffer.
#
# Entry:
#           Buffer index in A
#           Byte to be inserted in B
#
# Exit:
#           If buffer is full,
#                Carry = 1
#           else
#                Carry = 0
#
# Registers used: A, B, E, F, X, Y, CC
#
asm .INS_BUFFER   ( LDX, asm.BUFFER_HI, "Load the base of the buffer page table in X")
asm               ( LDE, {A:X}, "Load the page of buffer A into E (hi byte of W")
asm               ( LDF, 0x7F, "Load 0x7F - the midpoint of the buffer int F (lo byte of W)")
asm               ( TFR, (W, Y), "Transfer W (E, F) to Y" )

asm               ( LDX, buffer_output_offset_table_base            )
asm               ( LDF, {A:X},  "Load buffer output offset into F" )
asm               ( LDX, buffer_input_offset_table_base             )
asm               ( LDE, {A:X},  "Load buffer input offset into E"  )
asm               ( DECF, "Buffer full occurs when E == F - 1")
asm               ( CMPR, (E, F), "Compare input and output offsets")
asm               ( ORCC, 0x01,  "Indicate buffer full")
asm               ( BEQ,  asm.EXIT_INS_BUFFER, "If E and F are equal, buffer is full" )

asm               ( STB, {E:Y}, "Store the byte in the buffer at offset E" )
asm               ( INCE,       "Increment the buffer input offset" )
asm               ( STE, {A:X}, "Store the buffer input offset from E")
asm               ( ANDCC, 0xFE, "Success - Clear carry")
asm .EXIT_INS_BUFFER ( RTS )


# Remove byte from buffer. Buffer index in A. Byte returned in B.
asm .REM_BUFFER   ( LDX, asm.BUFFER_HI, "Load the base of the buffer page table in X")
asm               ( LDE, {A:X}, "Load the page of buffer A into E (hi byte of W")
asm               ( LDF, 0x7F, "Load 0x7F - the midpoint of the buffer int F (lo byte of W)")
asm               ( TFR, (W, Y), "Transfer W (E, F) to Y" )

asm               ( LDX, buffer_input_offset_table_base             )
asm               ( LDE, {A:X},  "Load buffer input offset into E"  )
asm               ( LDX, buffer_output_offset_table_base            )
asm               ( LDF, {A:X},  "Load buffer output offset into F" )
asm               ( CMPR, (E, F), "Buffer empty occurs when E == F" )
asm               ( ORCC, 0x01,  "Indicate buffer empty")
asm               ( BEQ,  asm.EXIT_REM_BUFFER, "If E and F are equal, buffer is empty")

asm               ( LDB, {F:Y}, "Load the byte from the buffer at offset F")
asm               ( INCF,       "Increment the buffer output offset")
asm               ( STF, {A:X}, "Store the buffer output offset from F")
asm               ( ANDCC, 0xFE, "Success - Clear carry")
asm .EXIT_REM_BUFFER ( RTS )


asm .ACIA_RESET (   LDA,    0b00000011,     "Master reset ACIA"         )
asm             (   STA,    {aciacr}                                    )
asm             (   RTS                                                 )

asm .ACIA_MODE  (   LDA,    0b00001010,     "ACIA Operating mode -- 7e1 - div 64"   ) # Gives 2400 baud with 153600 Hz clock
asm             (   STA,    {aciacr}                                                )
asm             (   RTS                                                             )


asm .BOOT   (   LDMD,   0b00000001,        "Enter native 6309 mode"        )
asm         (   LDS,    system_stack_base, "Setup system stack"            )
asm         (   NOP,                       "Do nothing"                    )
asm         (   NOP,                       "Do nothing"                    )
asm         (   NOP,                       "Do nothing"                    )
asm         (   JSR,    {asm.ACIA_RESET},  "Master reset ACIA"             )
asm         (   JSR,    {asm.ACIA_MODE},   "Set ACIA mode"                 )

asm .SEND   (   LDA,    0b00000010,     "Transmitter status flag"       )
asm .WAITR  (   BITA,   {aciasr},       "Test flag"                     )
asm         (   BEQ,    asm.WAITR,      "Branch if flag not set"        )
asm         (   LDA,    ord("x"),       "Load 'H' into A"               )
asm         (   STA,    {aciadr},       "Transmit character"            )
asm         (   JMP,    {asm.SEND},     "Send another character"        )
asm .END    (   JMP,    {asm.RESET},    "Jump back to the bottom"       )
asm         (   CALL,   print                                           )


asm .TRAP   (   JMP,    {asm.BOOT},     "TODO: Check for division by zero or bad instruction")
asm .SWI3   (   RTI,                    "Return from interrupt")
asm .SWI2   (   RTI,                    "Return from interrupt")
asm .FIRQ   (   RTI,                    "Return from interrupt")
asm .IRQ    (   RTI,                    "Return from interrupt")
asm .SWI    (   RTI,                    "Return from interrupt")
asm .NMI    (   RTI,                    "Return from interrupt")
asm .RESET  (   JMP,    {asm.BOOT},     "Boot!")


# Vector table at top of memory
asm         (   ORG,    0xFFF0,         "Bottom of the top 16 K ROM"    )
asm         (   FDB,   (asm.TRAP,   # TRAP (6309)
                        asm.SWI3,   # SWI3
                        asm.SWI2,   # SWI2
                        asm.FIRQ,   # /FIRQ
                        asm.IRQ,    # /IRQ
                        asm.SWI,    # SWI
                        asm.NMI,    # /NMI
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
