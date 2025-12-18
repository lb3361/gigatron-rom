RM=rm
GTASM=../../Contrib/at67/tools/gtasm/gtasm

frogstroll.gt1: frogstroll.vasm inc/*.i inc/macros/*.i
	${GTASM} frogstroll.vasm inc

clean: FORCE
	${RM} frogstroll.gt1

FORCE:

.PHONY: FORCE
