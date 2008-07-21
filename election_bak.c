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

struct project {
	char* name;
	double minimum;
	double maximum;
	funding_level* fundings;
}

static project CProjectFromPyProject(PyObject* dict)
{
	project p;
	
	p.name = PyString_AsString (PyDict_GetItemString(dict,"name"));
	p.minimum = PyFloat_AsDouble (PyDict_GetItemString(dict,"minimum"));
	
	return p;
}

static PyMethodDef ElectionMethods[] = {
    {"product", product, METH_VARARGS, "multiply two integers"},
	{"size", size, METH_VARARGS, "return tuple size"},
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initelection(void)
{
    (void) Py_InitModule("election", ElectionMethods);
}
