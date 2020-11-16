#include <stddef.h>

wchar_t * reverse(wchar_t * text, wchar_t * out, int length) {
  // Copies `text` into `out` in reverse order.
  for (int i = 0; i < length; i++) {
    out[length - i - 1] = text[i];
  }
  out[length] = 0;
  return out;
}
