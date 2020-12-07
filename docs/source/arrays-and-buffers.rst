================================
Buffers, Arrays and NumPy Arrays
================================

## Passing numpy arrays to and from C

Ctypes handles passing basic scalar types (`ints` and `floats`) nicely. For arrays it's more fiddly.

### Memory allocation

I've found the cleanest way is to leave numpy in charge of creating and allocating arrays then passing pointers into C in order to avoid having to inc-ref memory blocks in C and/or Python (both very ugly) manually. This includes functions that would output an array - instead of creating an array in C and returning it, allocate an array in Python using `out = np.empty(size, dtype)` and pass a pointer to `out`  to C to populate it.

### Multi-dimensional arrays and contiguity

C does allow multidimensional arrays as arrays of arrays but it's far more trouble than it's worth. Treat multidimensional arrays as flattened 1D arrays and use pointer arithmetic to ravel indices.

Numpy arrays aren't guaranteed to be C contiguous. If your function doesn't explicitly use `arr.strides` information to deal with this then use `arr = np.asarray(arr, order="C")` before passing to C.

## Matching Integer types

For obvious reasons it's important that numpy and C agree on what size integers you use in arrays. If you get it wrong there are no warning or fail-safes you just get nonsense. For this there are two options:

If you want an exact size (e.g. 16-bit ints), `#include <stdint.h>`, use `int16_t` instead of  `int` in C and ensure your numpy array in Python is of dtype `np.int16`.

Or to allow OS dependent int sizes (which can be faster on certain architectures) use regular `int` or `size_t` (requires `stdint.h` again) in C with `np.intc` or `np.intp` in numpy respectively. Other types such as `longs` or `shorts` should be avoided.

Float types are simpler. `float` in C is `np.float32` in numpy and `double` in C is `np.float64` in numpy.

Types can be enforced in numpy using any of `arr.astype(np.int32)` or `np.asarray(arr, dtype=np.int32)`.

