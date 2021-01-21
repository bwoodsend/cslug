#include <stddef.h>

void flatten_3D(double * in, double * out, size_t * shape) {
  /* Copy the contents of a contiguous 3D array into a flat array. */
  size_t n = 0;
  for (size_t i = 0; i < shape[0]; i++) {
    for (size_t j = 0; j < shape[1]; j++) {
      for (size_t k = 0; k < shape[2]; k++) {
        // Convert from 3D indices to flat index.
        size_t flat_index = (i * shape[1] + j) * shape[2] + k;
        // Copy the value.
        out[n++] = in[flat_index];
      }
    }
  }
}

// ---

void flatten_strided_3D(double * in, double * out, size_t * shape, size_t * strides) {
  /* Copy the contents of a non-contiguous 3D array into a flat array. */
  size_t n = 0;
  for (size_t i = 0; i < shape[0]; i++) {
    for (size_t j = 0; j < shape[1]; j++) {
      for (size_t k = 0; k < shape[2]; k++) {
        // Convert from 3D strided indices to flat.
        size_t flat_index = (i * strides[0] + j * strides[1] + k * strides[2]);
        // NumPy's stride offsets are in bytes rather than items.
        flat_index /= sizeof(double);
        // Copy the value.
        out[n++] = in[flat_index];
      }
    }
  }
}

// ---
