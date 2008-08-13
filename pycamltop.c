#include <Python.h>
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/memory.h>

extern void initpycamlmmv();

static int done;

static PyObject*
pycaml_ocaml(PyObject *self, PyObject *args)
{
  if(!PyArg_ParseTuple(args, ""))
    return NULL;

  done = 1;
  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef PycamlMethods[] = {
  {"ocaml", pycaml_ocaml, METH_VARARGS, ""},
  {NULL, NULL, 0, NULL}
};

CAMLprim value ml_python(value unit)
{
  static int initialized = 0;

  if (!initialized) {
    Py_Initialize();
    PyRun_SimpleString("import sys");
    PyRun_SimpleString("sys.ps1 = '>>> '");
    PyRun_SimpleString("sys.ps2 = '... '");
    PyRun_SimpleString("sys.path.insert(0,'')");

    Py_InitModule("pycaml", PycamlMethods);
    PyRun_SimpleString("import pycaml");
    PyRun_SimpleString("from pycaml import ocaml");

    initpycamlmmv();

    PyRun_SimpleString("from autorun import *");

    initialized = 1;
  }

  done = 0;
  clearerr(stdin);
  while (!done && !feof(stdin)) {
    PyRun_InteractiveOne(stdin,"<stdin>");
  }
  /*  Py_Finalize();*/
  return Val_unit;
}

/* dummy function to allow linkage against modules that require this */
void caml_startup(char** argv)
{
}
