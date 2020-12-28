#include <stdlib.h>

int * indices_of(char * x, int len_x, char y, int * count) {

  for (int i = 0; i < len_x; i++)
    *count += (x[i] == y);

  int * out = malloc(*count * sizeof(int));

  for (int i = 0, j = 0; j < *count; i++)
    if (x[i] == y)
      out[j++] = i;

  return out;
}


int * indices_of_no_precount(char * x, int len_x, char y, int * count) {
  int out_capacity = 10;
  int * out = malloc(out_capacity * sizeof(int));

  *count = 0;
  for (int i = 0; i < len_x; i++)
    if (x[i] == y) {
      if (*count == out_capacity) {
        // `out` is full. We need to resize it.
        out_capacity *= 2;
        out = realloc(out, out_capacity);
      }
      out[(*count)++] = i;
    }

  return out;
}
