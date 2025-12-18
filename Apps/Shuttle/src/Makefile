GLCC=glcc
RM=rm
ROM=dev7
MAP=32k
IMGTOGT1=../../../Utils/imgtogt1.py
GT1MERGE=../../MSCP/src/gt1merge.py


PGM=../shuttle.gt1

${PGM}: maze.gt1 splash.gt1
	${GT1MERGE} maze.gt1 splash.gt1 -o ${PGM}

splash.gt1: shuttle.png
	${IMGTOGT1} shuttle.png --size=160x120 --force splash.gt1

maze.gt1: maze.c
	${GLCC} -map=${MAP} -rom=${ROM} maze.c -o maze.gt1

clean: FORCE
	${RM} splash.gt1 maze.gt1
	${RM} ${PGM}

FORCE:

.PHONY: FORCE
