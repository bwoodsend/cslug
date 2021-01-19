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
