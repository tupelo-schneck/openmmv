#include <Python.h>
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/memory.h>

PyObject* class_FundingLevel;

static PyObject*
pycamlmmv_register_classes(PyObject *self, PyObject *args)
{
  if(!PyArg_ParseTuple(args, "O", &class_FundingLevel))
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

value ml_list_of_PyList (PyObject* pylist, value (*conv)(PyObject*)) 
{
  CAMLparam0();
  CAMLlocal2(res,curr);
  int i;
  int len = PyList_Size(pylist);
  res = Val_emptylist;

  for(i = 0; i < len; i++) 
    {
      if (i == 0) 
	{
	  res = caml_alloc(2,0);
	  curr = res;
	}
      else 
	{
	  Store_field(curr,1,caml_alloc(2,0));
	  curr = Field(curr,1);
	}
      Store_field(curr,0,(*conv)(PyList_GetItem(pylist,i)));
      Store_field(curr,1,Val_emptylist);
    }
  
  CAMLreturn(res);
}

PyObject* PyList_of_ml_list (value v, PyObject* (*conv)(value))
{
  CAMLparam1(v);
  CAMLlocal1(curr);
  PyObject* res = PyList_New(0);
  PyObject* item;

  curr = v;

  while (curr != Val_emptylist) {
    item = (*conv)(Field(curr,0));
    PyList_Append(res, item);
    Py_DECREF(item);
    curr = Field(curr,1);
  }
  
  CAMLreturnT(PyObject*,res);
}


PyObject* 
PyFundingLevel_of_ml_funding_level(value v)
{
  //  assert class_FundingLevel <> 0;
  PyObject* tmp;
  PyObject* res;
  tmp = Py_BuildValue("(fff)",
		      Double_field(v,0),
		      Double_field(v,1),
		      Double_field(v,2));
  res = PyInstance_New(class_FundingLevel,
		       tmp,
		       NULL);
  Py_DECREF(tmp);
  return res;
}

value
ml_funding_level_of_PyFundingLevel(PyObject* p)
{
  CAMLparam0();
  CAMLlocal1(res);
  PyObject* tmp;
  res = caml_alloc(3 * Double_wosize, Double_array_tag);
  tmp = PyObject_GetAttrString(p,"amount");
  Store_double_field(res,0,PyFloat_AsDouble(tmp));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"support");
  Store_double_field(res,1,PyFloat_AsDouble(tmp));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"prevSupport");
  Store_double_field(res,2,PyFloat_AsDouble(tmp));
  Py_DECREF(tmp);
  CAMLreturn(res);
}

value
ml_project_of_PyProject(PyObject* p)
{
  CAMLparam0();
  CAMLlocal1(res);
  PyObject* tmp;
  res = caml_alloc(6, 0);
  tmp = PyObject_GetAttrString(p,"id");
  Store_field(res,0,Val_int(PyInt_AsLong(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"name");
  Store_field(res,1,caml_copy_string(PyString_AsString(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"minimumBudget");
  Store_field(res,2,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"maximumBudget");
  Store_field(res,3,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"eliminated");
  Store_field(res,4,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"fundings");
  Store_field(res,5,ml_list_of_PyList(tmp,
				      ml_funding_level_of_PyFundingLevel));
  Py_DECREF(tmp);
  CAMLreturn(res);
}

void
PyProject_gets_ml_project(PyObject* p, value v)
{
  PyObject* tmp;
  tmp = PyFloat_FromDouble(Double_val(Field(v,4)));
  PyObject_SetAttrString(p,"eliminated",tmp);
  Py_DECREF(tmp);
  tmp = PyList_of_ml_list(Field(v,5), PyFundingLevel_of_ml_funding_level);
  PyObject_SetAttrString(p,"fundings",tmp);
  Py_DECREF(tmp);
}

value
ml_ballot_item_of_PyBallotItem(PyObject* p)
{
  CAMLparam0();
  CAMLlocal1(res);
  PyObject* tmp;
  res = caml_alloc(6,0);
  tmp = PyObject_GetAttrString(p,"projectId");
  Store_field(res,0,Val_int(PyInt_AsLong(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"proposedFunding");
  Store_field(res,1,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"priorProposedFunding");
  Store_field(res,2,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"actualTotalFunding");
  Store_field(res,3,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"voterSupport");
  Store_field(res,4,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"voterFunding");
  Store_field(res,5,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  CAMLreturn(res);
}

void
PyBallotItem_gets_ml_ballot_item(PyObject* p, value v)
{
  PyObject* tmp;
  tmp = PyFloat_FromDouble(Double_val(Field(v,4)));
  PyObject_SetAttrString(p,"actualTotalFunding",tmp);
  Py_DECREF(tmp);
  tmp = PyFloat_FromDouble(Double_val(Field(v,5)));
  PyObject_SetAttrString(p,"voterSupport",tmp);
  Py_DECREF(tmp);
  tmp = PyFloat_FromDouble(Double_val(Field(v,6)));
  PyObject_SetAttrString(p,"voterFunding",tmp);
  Py_DECREF(tmp);
}

/* ugly hack allowing use of C functions pointers */
PyObject* gPyBallotItems;

value
ml_ballot_priority_of_key(PyObject* p)
{
  return ml_list_of_PyList(PyDict_GetItem(gPyBallotItems,p), ml_ballot_item_of_PyBallotItem);
}

value
ml_ballot_of_PyBallot(PyObject* p)
{
  CAMLparam0();
  CAMLlocal1(res);
  PyObject* tmp;
  PyObject* keys;
  res = caml_alloc(6,0);
  tmp = PyObject_GetAttrString(p,"id");
  Store_field(res,0,Val_int(PyInt_AsLong(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"name");
  Store_field(res,1,caml_copy_string(PyString_AsString(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"ballotItems");
  keys = PyDict_Keys(tmp);
  PyList_Sort(keys);
  gPyBallotItems = tmp;
  Store_field(res,2,ml_list_of_PyList(keys,
				      ml_ballot_priority_of_key));
  Py_DECREF(keys);
  Py_DECREF(tmp);
  CAMLreturn(res);
}

void
PyBallot_gets_ml_ballot(PyObject* p, value v)
{
  int i, j;
  value priorities;
  value mlitems;
  PyObject* tmp;
  PyObject* keys;
  PyObject* items;
  tmp = PyObject_GetAttrString(p,"ballotItems");
  keys = PyDict_Keys(tmp);
  PyList_Sort(keys);
  priorities = Field(v,2);
  for (i = 0; i < PyList_Size(keys); i++) {
    items = PyList_GetItem(keys,i);
    mlitems = Field(priorities,0);
    for (j = 0; j < PyList_Size(items); j++) {
      PyBallotItem_gets_ml_ballot_item(PyList_GetItem(items,j), Field(mlitems,0));
      mlitems = Field(mlitems,1);
    }
    priorities = Field(priorities,1);
  }
  Py_DECREF(keys);
  Py_DECREF(tmp);
}


static PyObject*
pycamlmmv_back_and_forth(PyObject *self, PyObject *args)
{
  PyObject* arg;
  if(!PyArg_ParseTuple(args, "O", &arg))
    return NULL;

  PyProject_gets_ml_project(arg,ml_project_of_PyProject(arg));
  Py_INCREF(arg);
  return arg;
}

static PyMethodDef PycamlmmvMethods[] = {
  {"register_classes", pycamlmmv_register_classes, METH_VARARGS, ""},
  {"back_and_forth", pycamlmmv_back_and_forth, METH_VARARGS, ""},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initpycamlmmv(void)
{
  Py_InitModule("pycamlmmv", PycamlmmvMethods);
}
