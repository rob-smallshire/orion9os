=================================
Notes from reading Acorn MOS 1.20
=================================

Acorn MOS is the 6502 based operating system for the BBC Micro. It's high quality code, so I'm
mining it for ideas.

6850 ACIA serial port
=====================

Like the Orion 9, the BBC Micro uses a 6850-based serial port.

Serial communication is interrupt driven. From the BBC Micro Advanced User Guide:

    13.8 Serial interrupt processing

    The 6850 asynchronous communications interface adapter (see serial system chapter 20) will
    produce three types of interrupt:

    1. Receiver interrupt - a character has been received.

    2. Transmitter interrupt - a character has been transmitted.

    3. Data Carrier Detect (DCD) interrupt - a 2400Hz tone has been discontinued - at the end of a
       cassette block.

    The 6850 contains a status byte that enables the 6502 to locate
    the cause of the interrupt. This byte is organised as:

    bit 0 - This bit is set on a receiver interrupt. Bits four five and six are valid after this
            interrupt.

    bit 1 - This bit is set on a transmit interrupt.

    bit 2 - This bit is set on a DCD (data carrier detect) interrupt.

    bit 3 - This bit is set if the 6850 is not CLEAR TO SEND.

    bit 4 - Framing error. Receive error.

    bit 5 - Receiver overrun. Receive error.

    bit 6 - Parity error. Receive error.

    bit 7 - Set if the 6850 was the source of the current interrupt. This bit is the first to be
            checked by the operating system interrupt handling routine.

    13.8.1 The cassette serial system [omitted]

    13.8.2 The RS423 serial system

    The RS423 system uses the interrupts in the following ways:

    A transmitter interrupt causes a character to be sent to the 6850 from the RS423 transmit
    buffer, or the printer buffer if the RS423 printer is selected. If both buffers are empty, the
    RS423 system is flagged as available (see OSBYTE &BF) and transmitter interrupts are disabled.

    A receiver interrupt is used to cause a character to be read from the 6850 and inserted into the
    RS423 receive buffer (if enabled by use of OSBYTE &9C). If there is a receive error, (which can
    be ignored by use of OSBYTE &E8) event number 7 is generated, and the character is ignored. The
    character is also ignored if OSBYTE &CC has been made non-zero. The RTS line is pulled high if
    the receive buffer is getting full. The number of characters which need to be in the buffer to
    cause RTS to go high is set by OSBYTE &CB.

    A DCD interrupt cannot occur unless the RS423 has been switched to the cassette connector by use
    of OSBYTE &CD. The DCD interrupt is normally cleared by reading from the 6850 receive register.
    An event number 7 (RS423 receive error event) is then generated.

    The RS423 system can be made to ignore any of the above interrupts by use of OSBYTE &E8. The
    6850 status register is ANDed with the OSBYTE value.

    Any bit cleared by this is ignored, and passed over to the user interrupt vector. The user is
    then responsible for clearing the interrupt condition. This is done by either reading the
    receive data register or writing to the transmit data register of the 6850 (see serial hardware
    chapter 20).


Relevant OSBYTE calls
---------------------

OSBYTE 2 - Select input stream
OSBYTE 3 - Select output stream
OSBYTE 7 - Set RS423 baud rate for receiving
OSBYTE 8 - Set RS423 baud rate for transmission
OSBYTE 15 - Flush buffer class
OSBYTE 21 - Flush specific buffer




Important addresses for serial handling
---------------------------------------

RAM
~~~

00EA - RS423 countdown timer. == 0 ACIA used by RS423 has timed out  < 0  ACIA using, not timed out

020A - OSBYTE Vector


0250 - RAM copy of ACIA control register
0278 - 6850 ACIA IRQ mask - defaulted to &FF by the value at D9B8

0900
-09BF  RS423 output buffer

0A00
-0AFF  RS423 input buffer


ROM
~~~

D9B8 - the default 6850 ACIA IRQ bit mask

I/O
~~~

FE08 - 6850 ACIA control register / status register
FE09 - 6850 ACIA transmit data / receive data
FE10 - Serial ULA control register


Important routines for serial handling
--------------------------------------

DC93 - IRQ1V - Interrupt Request 1 Vector
       Serial ACIA is the first peripheral to be checked.

DCA9 - ACIA Interrupt or ACIA Parity Error - JSR &DCDE for RS423

DCB3 - ACIA Data Carrier Detect

DCBF = ACIA IRQ, TxRDY - Send a byte
       Read from the serial buffer (JSR &E460) and send it to the ACIA

DCDE - Parity Error or RxRDY interrupt occurred
       Apply ICIA IRQ mask is &0278
       Checks for errors and if none sends data using DCBF

E173 - Set up ?RS423 buffer

E17C - OSBYTE 156 - API wrapper for the routine at E189

E189 - Update ACIA setting and RAM copy


E4B3 - INSBV - INSert character in Buffer Vector
       Insert a character into a buffer. X is buffer number, A is character to be written

E6D3 - OSBYTE 2 - Select input stream


FB46 - Reset ACIA


FB65 - Set ACIA control register

FFF4 - OSBYTE System call API:  A, X, Y

