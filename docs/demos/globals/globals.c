#include <stdint.h>
#include <stddef.h>

int an_int = 42;
float a_float = 1. / 3.;
double a_double = 1. / 3.;
int8_t an_8_bit_int = 43;

char a_bytes_array[] = "Hello, my name is Ned.";
wchar_t a_string[] = L"Сәлам. Минем исемем Нед.";

char contains_null[] = "This sentence has a \00 in the middle of it.";
int len_contains_null = sizeof(contains_null) / sizeof(char);

int get_an_int() {
  return an_int;
}
const int a_const_int = 3;
