#include <math.h>

void range_of(double * values, int len_values, double * min, double * max) {
  /* Get the minimum and maximum of an array of doubles. */

  // Set defaults for the min and max.
  *min = INFINITY;
  *max = -INFINITY;

  // Find the min and max.
  for (int i = 0; i < len_values; i++) {
    if (values[i] > *max) *max = values[i];
    if (values[i] < *min) *min = values[i];
  }
}  // Our outputs are in fact inputs so we don't return anything.
