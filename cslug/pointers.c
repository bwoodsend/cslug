#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "structmember.h"


static PyMethodDef methods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


static PyModuleDef this_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "cslug.__pointers",
    .m_size = -1,
    .m_methods = methods,
};


typedef struct PointerObject {
    PyObject_HEAD
    PyLongObject *_as_parameter_;
    Py_buffer buffer_info;
} PointerObject;


static PyMemberDef Pointer_members[] = {
    {"_as_parameter_", T_OBJECT_EX, offsetof(PointerObject, _as_parameter_), 0,
     "The raw address"},
    {NULL}  /* Sentinel */
};


static PyMethodDef Pointer_methods[] = {
    {NULL}  /* Sentinel */
};


static PyObject * Pointer_new(PyTypeObject *type, PyObject *args, PyObject *kwargs);
static void Pointer_dealloc(PointerObject *self);
PyObject *Pointer_repr(PyObject *self_obj);


static PyTypeObject PointerType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "cslug.Pointer",
    .tp_doc = PyDoc_STR("A raw pointer which inc-refs the buffer it points to."
    "\n\nPlease no not instantiate this class directly. Instead use the `ptr()`"
    " function."),
    .tp_basicsize = sizeof(PointerObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_FINALIZE,
    .tp_new = Pointer_new,
    .tp_repr = Pointer_repr,
    .tp_dealloc = (destructor) Pointer_dealloc,
    .tp_methods = Pointer_methods,
    .tp_members = Pointer_members,
};


static PyObject * Pointer_new(PyTypeObject *type, PyObject *args, PyObject *kwargs) {

    PyObject * buffer;
    int flags;
    if (!PyArg_ParseTuple(args, "Oi", &buffer, &flags))
        return NULL;

    PointerObject * self = (PointerObject *) type->tp_alloc(type, 0);
    if (PyObject_GetBuffer(buffer, &self->buffer_info, flags))
        return NULL;

    PyLongObject * address = (PyLongObject*) PyLong_FromVoidPtr(self->buffer_info.buf);
    self->_as_parameter_ = address;

    return (PyObject *) self;
}


static void Pointer_dealloc(PointerObject *self) {
    PyBuffer_Release(&self->buffer_info);
    Py_TYPE(self)->tp_free((PyObject *) self);
}


PyObject *Pointer_repr(PyObject *self_obj) {
    PointerObject * self = (PointerObject *) self_obj;
    size_t address = PyLong_AsSize_t((PyObject *) self->_as_parameter_);
    return PyUnicode_FromFormat("<Void Pointer %zu>", address);
}


PyMODINIT_FUNC PyInit___pointers(void) {
    PyObject *m;
    if (PyType_Ready(&PointerType) < 0)
        return NULL;

    m = PyModule_Create(&this_module);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PointerType);
    if (PyModule_AddObject(m, "Pointer", (PyObject *) &PointerType) < 0) {
        Py_DECREF(&PointerType);
        Py_DECREF(m);
        return NULL;
    }
    PyModule_AddIntConstant(m, "PyBUF_STRIDES", PyBUF_STRIDES);

    return m;
}
