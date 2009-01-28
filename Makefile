# pycamltop not included here
MLMODULES = util mmv pycamlmmv
CMODULES = util pycamlmmv

all: mmv pycamlmmv_module
clean:
	rm -rf bin obj
	rm -f a.out *.pyc *.o *.so *.dll
	rm -rf build
test: pycamlmmv_module
	./tests.py

CC = gcc
OCAMLC = ocamlc
OCAMLOPT = ocamlopt
OCAMLDEP = ocamldep
OCAMLMKTOP = ocamlmktop -custom

UNAME = $(shell uname)

ifeq ($(UNAME),Darwin)
PYTHONINCDIR = /opt/local/include/python2.5
PYTHONLIBDIR = /opt/local/lib
CAMLDIR = /opt/local/lib/ocaml
SOLINK = MACOSX_DEPLOYMENT_TARGET=10.3 $(CC)  -mmacosx-version-min=10.4 -bundle -undefined dynamic_lookup -read_only_relocs suppress
SOLINKLIBS = -L$(CAMLDIR) -lasmrun
SOEXT = so
else
ifneq (,$(findstring CYGWIN,$(UNAME)))
PYTHONINCDIR = /usr/include/python2.5
PYTHONLIBDIR = /usr/bin
CAMLDIR = /usr/lib/ocaml
SOLINK = $(CC) -shared
SOLINKLIBS = -L$(CAMLDIR) -lasmrun -L$(PYTHONLIBDIR) -lpython2.5
SOEXT = dll
else
# Linux
PYTHONINCDIR = /usr/include/python2.5
PYTHONLIBDIR = /usr/lib
CAMLDIR = /usr/lib/ocaml/3.10.0
SOLINK = $(CC) -shared
SOLINKLIBS = -L$(CAMLDIR) -lasmrun -L$(PYTHONLIBDIR) -lpython2.5
SOEXT = so
endif
endif

MLFLAGS = -I obj
MLLINKFLAGS = -cclib -L$(PYTHONLIBDIR) -cclib -lpython2.5
CFLAGS = -Wall -I $(CAMLDIR) -I $(PYTHONINCDIR)
ifeq ($(UNAME),Darwin)
CFLAGS =  -mmacosx-version-min=10.4 -Wall -I $(CAMLDIR) -I $(PYTHONINCDIR)
endif

vpath %.o obj
vpath %.cmi obj
vpath %.cmo obj
vpath %.cmx obj

%_c.o: %.c
	$(CC) -c $(CFLAGS) -o obj/$@ $<

%.cmo: %.ml
	$(OCAMLC) -c $(MLFLAGS) -o obj/$@ $<

%.cmx: %.ml
	$(OCAMLOPT) -c $(MLFLAGS) -o obj/$@ $<

camlcode.o: $(MLMODULES:=.cmx)
	$(OCAMLOPT) -o $@ -output-obj $(^F:%.cmx=obj/%.cmx)
	mv $@ obj

pycamlmmv_module: pycamlmmv.$(SOEXT)

pycamlmmv.$(SOEXT): $(CMODULES:=_c.o) camlcode.o
	$(SOLINK) -o $@ $(^F:%.o=obj/%.o) $(SOLINKLIBS)

bin/mmv: $(CMODULES:=_c.o) pycamltop_c.o $(MLMODULES:=.cmo) pycamltop.cmo 
	mkdir -p bin
	$(OCAMLMKTOP) $(MLFLAGS) $(MLLINKFLAGS) -o $@ $(^F:%.o=obj/%.o)

mmv: bin/mmv
	touch mmv

obj/DEPEND: $(MLMODULES:=.ml) pycamltop.ml
	mkdir -p obj
	$(OCAMLDEP) $^ > obj/DEPEND

-include obj/DEPEND
