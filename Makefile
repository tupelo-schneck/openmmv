MLMODULES = mmv pycamlmmv pycaml
CMODULES = pycaml pycamlmmv

OBJ = obj
BIN = bin

all: mmv
clean:
	rm -rf $(BIN) $(OBJ)

CC = gcc
OCAMLC = ocamlc
OCAMLOPT = ocamlopt
OCAMLDEP = ocamldep
OCAMLMKTOP = ocamlmktop

MLFLAGS = -g -custom -I $(OBJ)
MLLINKFLAGS = -cclib -L/opt/local/lib -cclib -lpython2.5
CFLAGS = -Wall -I /opt/local/lib/ocaml \
  -I /opt/local/include/python2.5/

vpath %.o $(OBJ)
vpath %.cmi $(OBJ)
vpath %.cmo $(OBJ)
vpath %.cmx $(OBJ)

%_c.o: %.c
	$(CC) -c $(CFLAGS) -o $(OBJ)/$@ $<

%.cmo: %.ml
	$(OCAMLC) -c $(MLFLAGS) -o $(OBJ)/$@ $<

%.cmx: %.ml
	$(OCAMLOPT) -c $(MLFLAGS) -o $(OBJ)/$@ $<

mmv: $(MLMODULES:=.cmo) $(CMODULES:=_c.o)
	mkdir -p $(BIN)
	$(OCAMLMKTOP) $(MLFLAGS) $(MLLINKFLAGS) -o $(BIN)/$@ $(^F:%.o=$(OBJ)/%.o)

$(OBJ)/DEPEND: $(MLMODULES:=.ml)
	mkdir -p $(OBJ)
	$(OCAMLDEP) $^ > $(OBJ)/DEPEND

-include $(OBJ)/DEPEND
