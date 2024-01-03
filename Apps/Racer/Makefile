SHELL=/bin/sh

# Post-v3 racer is built as independent gt1 files to enable compression.
# To enable this, SYS_Racer.py must immediately follow Racer.gt1[z]
# providing a SYS call to reveal the addresses of both private sys calls
# and horizon image.
#
# In the rom compilation command line:
#
#		Racer=Apps/Racer/Racer.gt1z\
#		SYS_Racer.py\
#		zippedRacerHorizon=Apps/Racer/Horizon-256x16.gt1z\
#
# An error might occurs when SYS_Racer.py straddles a page boundary.
# The best solution is then to move things around, but always let
# SYS_Racer.py immediately follow Racer.gt1[z].

ifdef COMSPEC
E=.exe
else
E=
endif

TOP=../..
IMGTOGT1=${TOP}/Utils/imgtogt1.py
GT1Z=${TOP}/Utils/gt1z/gt1z${E}
COMPILEGCL=${TOP}/Core/compilegcl.py -s ${TOP}/interface.json

all: Horizon-256x16.gt1z Racer.gt1z

Horizon-256x16.gt1: Horizon-256x16.png
	${IMGTOGT1} -f --size=256x16 --start=0x1000 --aspect $< $@

%.gt1: %.gcl
	${COMPILEGCL} "$<" `dirname "./$@"`

%.gt1z: %.gt1 ${GT1Z}
	${GT1Z} -f "$<" "$@"

${TOP}/Utils/gt1z/gt1z${E}: ${TOP}/Utils/gt1z/gt1z.cpp
	${MAKE} -C ${TOP}/Utils/gt1z

.SECONDARY:
