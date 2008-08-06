#include <Python.h>
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/memory.h>

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
    Py_InitModule("pycaml", PycamlMethods);
    PyRun_SimpleString("import sys");
    PyRun_SimpleString("sys.ps1 = '>>> '");
    PyRun_SimpleString("sys.ps2 = '... '");
    PyRun_SimpleString("from pycaml import ocaml");
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
