SHELL=/bin/sh

# This makefile constructs a compressed gt1 file
# containing the basic program and a stub that
# loads basic from the rom and runs the program.

ifdef COMSPEC
E=.exe
else
E=
endif

TOP=../..
GTBTOGT1=${TOP}/Utils/gtbtogt1.py
GT1Z=${TOP}/Utils/gt1z/gt1z${E}

all: TicTac_v2.gt1 TicTac_v2.gt1z

%.gt1: %.gtb
	${GTBTOGT1} -f $< $@

%.gt1z: %.gt1 ${GT1Z}
	${GT1Z} -czf "$<" "$@"

${TOP}/Utils/gt1z/gt1z${E}: ${TOP}/Utils/gt1z/gt1z.cpp
	${MAKE} -C ${TOP}/Utils/gt1z

.SECONDARY:
