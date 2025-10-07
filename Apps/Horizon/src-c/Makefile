
# compile c programs with GLCC
CC=../../../Compilers/glcc/build/glcc
ROM=dev

# use 32k map modified by overlay horizon.ovl
CFLAGS=-map=32k,./Horizon.ovl -rom=$(ROM)

# avoid runtime bss initialization to save code.
LDFLAGS=--no-runtime-bss-init

# target
TARGET=../Horizon_c.gt1

all: $(TARGET)

$(TARGET): Horizon.c Horizon.ovl
	${CC} ${CFLAGS} ${LDFLAGS} Horizon.c -o $@

clean:
	-rm $(TARGET)

