
ROM=dev
MAP=32k,bare
CC=../../Compilers/glcc/build/glcc
GT1Z=../../Utils/gt1z/gt1z

rotator.gt1: rotator.s
	${CC} -rom=$(ROM) -map=$(MAP) $< -o $@ \
           --gt1-exec-address=main --entry=main

clean: FORCE
	-rm 2>&1 *.gt1 *.g1tz

FORCE:

.PHONY: FORCE
