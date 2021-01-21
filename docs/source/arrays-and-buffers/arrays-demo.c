double sum(double * arr, int len_arr) {
  /* Calculate the sum of an array. */
  double total = 0.0;
  for (int i = 0; i < len_arr; i++)
    total += arr[i];
  return total;
}

#include <stdint.h>

void cumsum(int32_t * in, int32_t * out, int len) {
  /* Calculate the cumulative sums of an the array `in`
     and write to array `out`. */
  int32_t total = 0;
  for (int i = 0; i < len; i++) {
    total += in[i];
    out[i] = total;
  }
}

// ---
// vectorization

#include <stddef.h>

void add_1(int * in, int * out, size_t len) {
  /* Add 1 to every element in the 1D array `in`.
     Write to the 1D array `out`. */
  for (size_t i = 0; i < len; i++) {
    out[i] = in[i] + 1;
  }
}

// ---
