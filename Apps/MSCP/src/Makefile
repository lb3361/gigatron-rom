ROM=dev7
MAP=128k
GLCC=glcc
PYTHON=python3
PGMS=../mscp_128k.gt1
OBJS=mscp.o core.o

all: ${PGMS}

../mscp_128k.gt1: mscp1.gt1 book.bin
	booklen=`ls -ln book.bin | awk '{ print($$5); }'` ;\
	${PYTHON} gt1merge.py $< --raw=book.bin@0x4000 --doke=$$booklen@0x42 -o $@

mscp1.gt1: ${OBJS} ${ASMS}
	${GLCC} -rom=${ROM} -map=${MAP} ${OBJS} ${ASMS} -o $@

mscp.o: mscp.c core.h
	${GLCC} -rom=${ROM} -c $<

core.o: core.c core.h
	${GLCC} -rom=${ROM} -c $<

book.bin: book.txt mscp.c Makefile
	${CC} -DSAVE_BOOK_BIN=1 -DSUBTRACTIVE_RND=1 mscp.c -o dumpbook
	./dumpbook

clean:
	-rm ${OBJS} *.gt1 *.prf *.frg prof.txt dumpbook mscp
