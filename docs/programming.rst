===========
Programming
===========

To assemble into a 32 K ROM (of which the top half is mapped into memory)::

  $ python -m asm68 --verbosity=INFO asm source/entry.py --output=object/entry.bin --repeat=2

This puts concatenates two copies of the assembled 16 K code into the 32 K image for programming
into a 32 K EEPROM.

To flash the EEPROM, check the programmer is connected and detected::

  $ minipro -k
  tl866a: TL866A

Program with::

  $ minipro -p "AT28C256" -w object/entry.bin
  Found TL866A 03.2.86 (0x256)
  Erasing... 0.02Sec OK
  Protect off...OK
  Writing Code...  6.85Sec  OK
  Reading Code...  0.59Sec  OK
  Verification OK
  Protect on...OK

Verify with::

  $ minipro -p "AT28C256" -m object/entry.bin
  Found TL866A 03.2.86 (0x256)
  Reading Code...  0.59Sec  OK
  Verification OK

