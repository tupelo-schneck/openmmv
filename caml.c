#include <Python.h>

int _product(int x, int y)
{
      return x * y;
}

static PyObject* product(PyObject* self, PyObject* args)
{
    int x, y;

    if (!PyArg_ParseTuple(args, "ii", &x, &y))
        return NULL;

    return Py_BuildValue("i", _product(x, y));
}

static PyObject* size(PyObject* self, PyObject* args)
{
	Py_ssize_t size = PyTuple_Size(args);
	
	return Py_BuildValue("i", size);
}

static PyMethodDef CamlMethods[] = {
    {"product", product, METH_VARARGS, "multiply two integers"},
	{"size", size, METH_VARARGS, "return tuple size"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initcaml(void)
{
    (void) Py_InitModule("caml", CamlMethods);
}
