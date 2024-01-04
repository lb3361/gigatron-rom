SHELL=/bin/sh

# This makefile constructs gt1 files
# containing the basic programs and a stub that
# loads basic from the rom and runs the program.

ifdef COMSPEC
E=.exe
else
E=
endif

TOP=..
GTBTOGT1=${TOP}/Utils/gtbtogt1.py
GT1Z=${TOP}/Utils/gt1z/gt1z${E}

GTBFILES=$(wildcard *.gtb)
GT1FILES=${patsubst %.gtb,%.gt1,${GTBFILES}}
GT1ZFILES=${patsubst %.gtb,%.gt1z,${GTBFILES}}

all: ${GT1FILES}

gt1z: ${GT1ZFILES}

%.gt1: %.gtb
	${GTBTOGT1} -f $< $@

%.gt1z: %.gt1 ${GT1Z}
	${GT1Z} -czf "$<" "$@"

${TOP}/Utils/gt1z/gt1z${E}: ${TOP}/Utils/gt1z/gt1z.cpp
	${MAKE} -C ${TOP}/Utils/gt1z

clean: FORCE
	-rm *.gt1 *.gt1z

FORCE:

.PHONY: FORCE
