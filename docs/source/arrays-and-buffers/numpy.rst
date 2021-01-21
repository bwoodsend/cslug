============
NumPy Arrays
============

NumPy's :class:`numpy.ndarray`\ s are similar to :ref:`arrays <Arrays>`
(please read :ref:`Buffers and Arrays` before reading this)
but with the following new conditions.

* NumPy has it's own type specifiers.
  Use :func:`numpy.asarray(arr, dtype=dtype) <numpy.asarray>` to enforce data
  types.
* Arrays are not generally C contiguous.
  Either C code should respect :attr:`numpy.ndarray.strides` or wrapping Python
  code should guard against non contiguous arrays using
  :func:`numpy.ascontiguousarray()` or
  :func:`numpy.asarray(arr, order="C") <numpy.asarray>`.
* Arrays may be multi-dimensional - something which C's general support for is
  pretty poor.
  Pointer arithmetic is needed to navigate a multidimensional array.


Basic 1D Examples
-----------------

Let's wrap the :c:`sum()` function from :any:`totals.c` but use NumPy instead of
:mod:`array`.
The C code remains the same but the type checking/normalisation in Python
differs.
The following is a correct way to wrap with NumPy.

.. literalinclude:: arrays-demo.py
    :name: numpy-wrap-sum
    :start-at: import numpy as np
    :end-at: return

* The ``dtype=np.double`` enforces correct data types (see :ref:`Data types`).
* The ``order="C"`` enforces contiguity (see :ref:`Contiguity`).

And for completeness, the :c:`cumsum()` :ref:`example <cumsum>` for writing an
array.

.. literalinclude:: arrays-demo.py
    :pyobject: cumsum


Contiguity
----------

Contiguity will be easier to explain when you see it go wrong.
Let's start by bypassing the contiguity enforcement in the :ref:`sum example
above <numpy-wrap-sum>`.
The following creates an array of the correct dtype
but without setting ``order``
and passes it to our C function. ::

    >>> arr = np.arange(10, dtype=np.double)
    >>> slug.dll.sum(ptr(arr), len(arr))
    45.0
    # Compare to the correct answer.
    >>> np.sum(arr)
    45.0

Hmm, everything seems to be working ok without the ``order="C"``. But...
that is only because NumPy writes C contiguous arrays by default so ``arr``
is already contiguous. ::

    >>> arr.flags.c_contiguous
    True

NumPy only creates non-contiguous arrays if it thinks it can avoid a redundant
copy operation by using a strided array instead.
Slicing with a *step* is one example of when this may happen. ::

    >>> arr[::2].flags.c_contiguous
    False

Instead of copying out every second element of ``arr`` into a new array,
NumPy has simply said "use the same raw data as :py:`arr` but skip every second
element". ::

    >>> np.shares_memory(arr, arr[::2])
    True

Whilst NumPy is smart enough to work with strided arrays::

    >>> arr = np.arange(10, dtype=np.double)[::2]
    >>> arr
    array([0., 2., 4., 6., 8.])
    >>> arr.sum()
    20.0  # <-- Yes, that is the correct answer.

Our C code isn't.
:func:`cslug.ptr()` actively prohibits us from making this mistake.
It raises a :class:`ValueError` error if its given a non-contiguity buffer::

    >>> ptr(arr)
    ValueError: ndarray is not C-contiguous and, by using `ptr()`,
    you have specified that a contiguous array is required. See
    the bottom of `help(cslug.ptr)` for how to resolve this.

To remove this safety net and see why ``arr`` should be contiguous, use
:func:`cslug.nc_ptr`::

    >>> from cslug import nc_ptr
    >>> slug.dll.sum(nc_ptr(arr), len(arr))
    10.0  # <-- This is the wrong answer.

Because ``arr`` was created using :py:`arr = np.arange(10, dtype=np.double)[::2]`,
under the hood ``arr`` is just :py:`np.arange(10, dtype=np.double)` but with a
flag set to say, "skip every second element".
The above code is therefore really running::

    >>> slug.dll.sum(ptr(np.arange(10, dtype=np.double)), 5)
    10.0

Another way you can see that a sliced array is the same array as the one it was
sliced from is to compare pointers.
Again, because ``arr[::2]`` is non-contiguous, you will have to use
:func:`~cslug.nc_ptr()`. ::

    >>> a = np.arange(10, dtype=np.double)
    >>> ptr(a)
    <Void Pointer 94425197003296>
    >>> nc_ptr(a[::2])
    <Void Pointer 94425197003296>
    >>> nc_ptr(a[::2]) == nc_ptr(a)
    True


Data types
----------

Data types are controlled in NumPy with the :attr:`~numpy.ndarray.dtype`
property.
The mapping of C types to :class:`numpy.dtype`\ s is relatively intuitive par a
few special cases.
Again there are no safety checks. If you get it wrong, anything can happen.

.. note::

    NumPy's default data types are platform dependent.
    For example, :py:`np.arange(10).dtype`
    returns ``int32`` on Windows but ``int64`` on Linux.
    If your code works perfectly on one OS but spits out nonsense on another
    then the cause is likely a forgotten explicit dtype.


Integers
........

.. None of NumPy's dtypes are intersphinx-able with :class:`numpy.type`.

* The basic :c:`int` in C is :py:`numpy.intc`. Not :py:`numpy.int` which is just
  the builtin Python :class:`int` type.
* Inexact integer types such as :c:`short`, :c:`long` and :c:`long long` are
  named the same (minus any spaces):
  :py:`numpy.short`, :py:`numpy.long`, :py:`numpy.longlong`.
* Exact types such as :c:`int32_t` have the ``_t`` stripped, giving
  :py:`numpy.int32`.
* Unsigned integers have a ``u`` prefix:
  :py:`numpy.ushort`, :py:`numpy.uint16`.
* :c:`ssize_t` and :c:`size_t` are :py:`numpy.intp` and :py:`numpy.uintp`
  respectively.


Floats
......

* :c:`float` is :py:`numpy.single`.
* :c:`double` is :py:`numpy.double`.


String-like types
.................

* :c:`char` is :py:`numpy.void`.
* :c:`wchar_t` is :py:`numpy.unicode_`.


Multidimensional arrays
-----------------------

Assuming C contiguity, multidimensional arrays are really just 1D arrays.
Each row is laid out end to end in memory.
For example the array::

    [[0, 1, 2], [3, 4, 5]]

Is in fact just::

    [0, 1, 2, 3, 4, 5]

With the metadata specifying that the array is shaped ``(2, 3)`` stored
elsewhere (in :attr:`numpy.ndarray.shape`).
Some basic arithmetic is needed to convert multidimensional indices into
one dimensional ones.

.. note::

    C does allow arrays of arrays but they're not fully featured.
    Most importantly, all but the outermost dimension must be known at compile
    time.
    This rules out almost all practical usages.


Contiguous Multidimensional Arrays
..................................

For the less :strikethrough:`masochistically` mathematically inclined,
below are the formula you will need to convert multidimensional indices
into flat ones.
In these formula, ``shape`` is the :attr:`numpy.ndarray.shape` attribute
which may be passed directly to C as an :c:`size_t *` using
:py:`ptr(arr.ctypes.shape)`.

==================  ====================================================
NumPy syntax        Convert dimensional indices (i, j, k) to flat index (n).
==================  ====================================================
:py:`arr[i]`        :c:`arr[i]`
:py:`arr[i, j]`     :c:`arr[i * shape[1] + j]`
:py:`arr[i, j, k]`  :c:`arr[(i * shape[1] + j) * shape[2] + k]`
==================  ====================================================

And, in the less likely case that you want to convert flat indices back to
multidimensional ones,
the formula below will undo the formula above.
Note that, in Python, you may simply use :func:`numpy.ravel_multi_index()` and
:func:`numpy.unravel_index()` which perform the same calculation as these
formula.

==================  ==================================================================
NumPy syntax        Convert flat index (n) to dimensional indices (i, j, k).
==================  ==================================================================
:py:`arr[i]`        :py:`arr[i]`
:py:`arr[i, j]`     :py:`arr[n // shape[1], n % shape[1]]`
:py:`arr[i, j, k]`  :py:`arr[n // (shape[1] * shape[2]), (n // shape[2]) % shape[1], n % shape[2]]`
==================  ==================================================================

The following trivial reimplementation of :func:`numpy.ravel`
demonstrates the above for a 3D array.

.. literalinclude:: flatten.c
    :language: C
    :name: flatten-3d
    :end-before: // ---

.. literalinclude:: flatten.py
    :pyobject: flatten_3D


Strided Arrays
..............

For those wanting to squeeze out every last clock cycle,
strided arrays can be supported directly (without conversion)
relatively easily if the number of dimensions is fixed.
Use the :attr:`numpy.ndarray.strides` attribute and the formula below
to locate elements.
In these formula,
``itemsize`` is the :attr:`arr.itemsize <numpy.ndarray.itemsize>` attribute.

==================  ====================================================
NumPy syntax        Convert dimensional indices (i, j, k) to flat index (n).
==================  ====================================================
:py:`arr[i]`        :c:`arr[(i * strides[0]) / itemsize]`
:py:`arr[i, j]`     :c:`arr[(i * strides[0] + j * strides[1]) / itemsize]`
:py:`arr[i, j, k]`  :c:`arr[(i * strides[0] + j * strides[1] + k * strides[2]) / itemsize]`
==================  ====================================================

To demonstrate, the code below is functionally equivalent to the
:ref:`flatten example <flatten-3d>` above except that it is faster for non
contiguous input.

.. literalinclude:: flatten.c
    :language: C
    :start-at: void flatten_strided
    :end-before: // ---

.. literalinclude:: flatten.py
    :pyobject: flatten_strided_3D


Vectorization
-------------

Often in NumPy, parallelizable functions are applied to arrays simply for speed,
rather than because they expect an array of inputs.
A simplest example of this is::

    arr + 1

which will work if ``arr`` is scalar or implicitly use a for loop if ``arr`` is
an array of any dimension.
Getting this to work for arbitrary dimensions and strided arrays efficiently
is far harder than it looks.
Travis E. Oliphant (the original author of NumPy) wrote his PhD on it.
There is cheat however that's almost as efficient.

* Ravel arbitrary dimensional arrays into 1D arrays.
* Write your C function to use a single for loop to traverse a 1D array.
* Unravel the output back to the original shape.

So to vectorize the :c:`add_1()` :ref:`hello cslug example <Hello cslug>`
add a single for loop to the C function:

.. literalinclude:: arrays-demo.c
    :language: C
    :start-after: // vectorization
    :end-before: // ---

Then to wrap it with:

.. literalinclude:: arrays-demo.py
    :pyobject: add_1

Ravelling and reshaping have no effect on the underlying contents of an array
provided that the array was C contiguous before being reshaped or ravelled.

In the above Python code, ``order="C"`` was explicitly specified,
meaning that ``arr`` and ``arr.ravel()`` use the same memory
and therefore ``ptr(arr) == ptr(arr.ravel())`` is guaranteed to be true.
A consequence of this is that the use of ``arr.ravel()`` and
``out.reshape(old_shape)`` is redundant and the above wrapper can be simplified
to:

.. literalinclude:: arrays-demo.py
    :pyobject: add_1_

