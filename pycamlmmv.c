#include <Python.h>
#include <caml/mlvalues.h>
#include <caml/alloc.h>
#include <caml/memory.h>
#include <caml/callback.h>

#define CAMLreturnT(type, result) do{ \
  type caml__temp_result = (result); \
  caml_local_roots = caml__frame; \
  return (caml__temp_result); \
}while(0)

PyObject* class_FundingLevel = NULL;
value default_utility;

CAMLprim value ml_register_utility(value u)
{
  default_utility = u;
  caml_register_global_root (&default_utility);
  return Val_unit;
}

static PyObject*
pycamlmmv_register_class(PyObject *self, PyObject *args)
{
  if(!PyArg_ParseTuple(args, "O", &class_FundingLevel))
    return NULL;

  Py_INCREF(Py_None);
  return Py_None;
}

value 
ml_list_of_PyList (PyObject* pylist, value (*conv)(PyObject*)) 
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

PyObject* 
PyList_of_ml_list (value v, PyObject* (*conv)(value))
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
  PyObject* tmp;
  PyObject* res;
  if (class_FundingLevel == NULL) {
    PyRun_SimpleString("pycamlmmv.register_class(elections.FundingLevel)");
  }
  tmp = Py_BuildValue("(ffffff)",
		      Double_field(v,0),
		      Double_field(v,1),
		      Double_field(v,2),
		      Double_field(v,3),
		      Double_field(v,4),
		      Double_field(v,5));
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
  res = caml_alloc(6 * Double_wosize, Double_array_tag);
  tmp = PyObject_GetAttrString(p,"amount");
  Store_double_field(res,0,PyFloat_AsDouble(tmp));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"size");
  Store_double_field(res,1,PyFloat_AsDouble(tmp));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"vote");
  Store_double_field(res,2,PyFloat_AsDouble(tmp));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"lastVote");
  Store_double_field(res,3,PyFloat_AsDouble(tmp));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"support");
  Store_double_field(res,4,PyFloat_AsDouble(tmp));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"lastSupport");
  Store_double_field(res,5,PyFloat_AsDouble(tmp));
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

#define PyFloat_AsDouble_NoneZero(x) (x==Py_None ? 0.0 : PyFloat_AsDouble(x)) 

value
ml_ballot_item_of_PyBallotItem(PyObject* p)
{
  CAMLparam0();
  CAMLlocal1(res);
  PyObject* tmp;
  res = caml_alloc(7,0);
  tmp = PyObject_GetAttrString(p,"projectId");
  Store_field(res,0,Val_int(PyInt_AsLong(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"proposedFunding");
  Store_field(res,1,caml_copy_double(PyFloat_AsDouble_NoneZero(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"priorProposedFunding");
  Store_field(res,2,caml_copy_double(PyFloat_AsDouble_NoneZero(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"actualTotalFunding");
  Store_field(res,3,caml_copy_double(PyFloat_AsDouble_NoneZero(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"voterSupport");
  Store_field(res,4,caml_copy_double(PyFloat_AsDouble_NoneZero(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"voterFunding");
  Store_field(res,5,caml_copy_double(PyFloat_AsDouble_NoneZero(tmp)));
  Py_DECREF(tmp);
  Store_field(res,6,Val_unit); /* None */
  CAMLreturn(res);
}

void
PyBallotItem_gets_ml_ballot_item(PyObject* p, value v)
{
  PyObject* tmp;
  tmp = PyFloat_FromDouble(Double_val(Field(v,3)));
  PyObject_SetAttrString(p,"actualTotalFunding",tmp);
  Py_DECREF(tmp);
  tmp = PyFloat_FromDouble(Double_val(Field(v,4)));
  PyObject_SetAttrString(p,"voterSupport",tmp);
  Py_DECREF(tmp);
  tmp = PyFloat_FromDouble(Double_val(Field(v,5)));
  PyObject_SetAttrString(p,"voterFunding",tmp);
  Py_DECREF(tmp);
}

/* ugly hack allowing use of C functions pointers */
PyObject* gPyBallotItems;

value
ml_ballot_priority_of_key(PyObject* p)
{
  CAMLparam0();
  CAMLlocal1(res);
  res = caml_alloc(1,0);
  Store_field(res,0,
	      ml_list_of_PyList(PyDict_GetItem(gPyBallotItems,p), 
				ml_ballot_item_of_PyBallotItem));
  CAMLreturn(res);
}

value
ml_ballot_of_PyBallot(PyObject* p)
{
  CAMLparam0();
  CAMLlocal1(res);
  PyObject* tmp;
  PyObject* keys;
  res = caml_alloc(4,0);
  tmp = PyObject_GetAttrString(p,"id");
  Store_field(res,0,Val_int(PyInt_AsLong(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"name");
  Store_field(res,1,caml_copy_string(PyString_AsString(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"weight");
  Store_field(res,2,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"ballotItems");
  keys = PyDict_Keys(tmp);
  PyList_Sort(keys);
  gPyBallotItems = tmp;
  Store_field(res,3,ml_list_of_PyList(keys,
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
  priorities = Field(v,3);
  for (i = 0; i < PyList_Size(keys); i++) {
    items = PyDict_GetItem(tmp,PyList_GetItem(keys,i));
    mlitems = Field(Field(priorities,0),0);
    for (j = 0; j < PyList_Size(items); j++) {
      PyBallotItem_gets_ml_ballot_item(PyList_GetItem(items,j), Field(mlitems,0));
      mlitems = Field(mlitems,1);
    }
    priorities = Field(priorities,1);
  }
  Py_DECREF(keys);
  Py_DECREF(tmp);
}

value
ml_game_of_PyElection(PyObject* p)
{
  CAMLparam0();
  CAMLlocal1(res);
  PyObject* tmp;
  PyObject* values;
  res = caml_alloc(9,0);
  tmp = PyObject_GetAttrString(p,"totalResources");
  Store_field(res,0,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"projects");
  values = PyDict_Values(tmp);
  Store_field(res,1,ml_list_of_PyList(values,
				      ml_project_of_PyProject));
  Py_DECREF(values);
  Py_DECREF(tmp);
  Store_field(res,2,default_utility);
  tmp = PyObject_GetAttrString(p,"quota");
  Store_field(res,3,caml_copy_double(PyFloat_AsDouble(tmp)/100.0));
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"ballots");
  values = PyDict_Values(tmp);
  Store_field(res,4,ml_list_of_PyList(values,
				      ml_ballot_of_PyBallot));
  Py_DECREF(values);
  Py_DECREF(tmp);
  tmp = PyObject_GetAttrString(p,"roundToNearest");
  Store_field(res,5,caml_copy_double(PyFloat_AsDouble(tmp)));
  Py_DECREF(tmp);
  Store_field(res,6,caml_copy_double(0.0));
  Store_field(res,7,caml_copy_double(0.0));
  Store_field(res,8,caml_copy_double(0.0));
  CAMLreturn(res);
}

void
PyElection_gets_ml_game(PyObject* p, value v)
{
  int i;
  value mlitems;
  PyObject* tmp;
  PyObject* items;
  tmp = PyObject_GetAttrString(p,"projects");
  items = PyDict_Values(tmp);
  mlitems = Field(v,1);
  for (i = 0; i < PyList_Size(items); i++) {
    PyProject_gets_ml_project(PyList_GetItem(items,i), Field(mlitems,0));
    mlitems = Field(mlitems,1);
  }
  Py_DECREF(items);
  Py_DECREF(tmp);

  tmp = PyObject_GetAttrString(p,"ballots");
  items = PyDict_Values(tmp);
  mlitems = Field(v,4);
  for (i = 0; i < PyList_Size(items); i++) {
    PyBallot_gets_ml_ballot(PyList_GetItem(items,i), Field(mlitems,0));
    mlitems = Field(mlitems,1);
  }
  Py_DECREF(items);
  Py_DECREF(tmp);
}


static PyObject*
pycamlmmv_run_election(PyObject *self, PyObject *args)
{
  CAMLparam0();
  CAMLlocal1(g);
  static value * closure_f = NULL;
  PyObject* arg;
  if(!PyArg_ParseTuple(args, "O", &arg))
    return NULL;
  
  if (closure_f == NULL) {
    /* First time around, look up by name */
    closure_f = caml_named_value("run_election");
  }

  g = ml_game_of_PyElection(arg);
  caml_callback(*closure_f, g);
  PyElection_gets_ml_game(arg, g);

  Py_INCREF(arg);
  CAMLreturnT(PyObject*,arg);
}

static PyObject*
pycamlmmv_send_election(PyObject *self, PyObject *args)
{
  static value * closure_f = NULL;
  PyObject* arg;
  if(!PyArg_ParseTuple(args, "O", &arg))
    return NULL;
  
  if (closure_f == NULL) {
    /* First time around, look up by name */
    closure_f = caml_named_value("send_election");
  }

  caml_callback(*closure_f, ml_game_of_PyElection(arg));

  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef PycamlmmvMethods[] = {
  {"register_class", pycamlmmv_register_class, METH_VARARGS, ""},
  {"run_election", pycamlmmv_run_election, METH_VARARGS, ""},
  {"send_election", pycamlmmv_send_election, METH_VARARGS, ""},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initpycamlmmv(void)
{
  char* argv[] = {"<>"};
  Py_InitModule("pycamlmmv", PycamlmmvMethods);
  PyRun_SimpleString("import elections");
  PyRun_SimpleString("import pycamlmmv");
  caml_startup(argv);
}
