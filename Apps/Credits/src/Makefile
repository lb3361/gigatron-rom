
# compile c programs with GLCC
CC=glcc

# use 32k map modified by overlay horizon.ovl
CFLAGS=-map=32k -rom=dev7

# avoid runtime bss initialization to save code.
LDFLAGS=--no-runtime-bss-init

# target
TARGET=../Credits.gt1

all: $(TARGET)

$(TARGET): Credits.c scroll.s Makefile
	${CC} ${CFLAGS} ${LDFLAGS} Credits.c scroll.s -o $@

clean:
	-rm $(TARGET)

