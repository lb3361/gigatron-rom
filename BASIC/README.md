# Basic demos

The `*.gtb` files are the tiny basic demo programs.

The `*.gt1` files were obtained with command `./Utils/gtbtogt1.py`. 
These GT1 files do not work with ROMv4 or earlier ROMs because 
they rely on the SYS call `SYS_ReadRomDir_v5_80` to locate the BASIC
interpreter. This SYS call was introduced in ROMv5a.

File `LEDs_ROMv1.gtb` illustrates the old way to control the LEDs.
This stopped working since ROMv2. See instead `LEDs.gtb`.

