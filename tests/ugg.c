#include <Python.h>

const int x = sizeof(Py_buffer) + 1;

const int INDIRECT = PyBUF_INDIRECT;
const int STRIDES = PyBUF_STRIDES;
const int ND = PyBUF_ND;
const int SIMPLE = PyBUF_SIMPLE;
const int C_CONTIGUOUS = PyBUF_C_CONTIGUOUS;
const int F_CONTIGUOUS = PyBUF_F_CONTIGUOUS;
const int ANY_CONTIGUOUS = PyBUF_ANY_CONTIGUOUS;
const int FULL = PyBUF_FULL;
const int FULL_RO = PyBUF_FULL_RO;
const int RECORDS = PyBUF_RECORDS;
const int RECORDS_RO = PyBUF_RECORDS_RO;
const int STRIDED = PyBUF_STRIDED;
const int STRIDED_RO = PyBUF_STRIDED_RO;
const int CONTIG = PyBUF_CONTIG;
const int CONTIG_RO = PyBUF_CONTIG_RO;
