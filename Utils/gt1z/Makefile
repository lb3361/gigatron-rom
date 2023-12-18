SHELL=/bin/sh
CXX=c++ -std=c++11
CXXFLAGS=-O3

ifdef COMSPEC
E=.exe
else
E=
endif

gt1z${E}: gt1z.cpp
	${CXX} ${CXXFLAGS} gt1z.cpp -o $@

clean: FORCE
	-rm gt1z

FORCE: .PHONY

.PHONY:

.PRECIOUS: gt1z${E}
