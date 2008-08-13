# pycamltop not included here
MLMODULES = mmv pycamlmmv
CMODULES = pycamlmmv

all: mmv pycamlmmv.so
clean:
	rm -rf bin obj
	rm -f a.out *.pyc *.o *.so 
	rm -rf build

CC = gcc
OCAMLC = ocamlc
OCAMLOPT = ocamlopt
OCAMLDEP = ocamldep
OCAMLMKTOP = ocamlmktop -custom

ifeq ($(shell uname),Darwin)
PREFIX = /opt/local
SOLINK = MACOSX_DEPLOYMENT_TARGET=10.3 $(CC) -bundle -undefined dynamic_lookup -read_only_relocs suppress
else
PREFIX = /usr
SOLINK = $(CC) -shared
endif

MLFLAGS = -g -I obj
MLLINKFLAGS = -cclib -L$(PREFIX)/lib -cclib -lpython2.5
CFLAGS = -Wall -I $(PREFIX)/lib/ocaml \
  -I $(PREFIX)/include/python2.5/
SOLINKLIBS = -L$(PREFIX)/lib/ocaml -lasmrun

vpath mmv bin
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

pycamlmmv.so: camlcode.o pycamlmmv_c.o
	$(SOLINK) -o $@ $(^F:%.o=obj/%.o) $(SOLINKLIBS)

mmv: $(CMODULES:=_c.o) pycamltop_c.o $(MLMODULES:=.cmo) pycamltop.cmo 
	mkdir -p bin
	$(OCAMLMKTOP) $(MLFLAGS) $(MLLINKFLAGS) -o bin/$@ $(^F:%.o=obj/%.o)

obj/DEPEND: $(MLMODULES:=.ml) pycamltop.ml
	mkdir -p obj
	$(OCAMLDEP) $^ > obj/DEPEND

-include obj/DEPEND
