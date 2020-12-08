// Required to use ``wchar_t``.
#include <stddef.h>

size_t count(wchar_t * text, wchar_t character) {
  /* Count how many times ``character`` appears in ``text``. */
  size_t out = 0;
  for (size_t i = 0; text[i] != 0; i++) {
    if (text[i] == character) {
      out++;
    }
  }
  return out;
}

// ---

size_t count_(wchar_t * text, wchar_t character) {
  /* Same as ``count()`` but written more compactly. */
  size_t out = 0;
  for (; *text; text++)
    out += (character == *text);
  return out;
}
