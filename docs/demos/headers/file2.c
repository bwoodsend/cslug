int do_nothing(int x);

int uses_do_nothing(int x) {
  /* Calls ``do_nothing()`` from ``file1.c``. */
  return do_nothing(x);
}
