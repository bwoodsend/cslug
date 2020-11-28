// -*- coding: utf-8 -*-

#include <stdio.h>
#include <stdint.h>
#include <string.h>


typedef struct Deque{
  void * contents;
  int max_size;
  int itemsize;
  int head_index;
  int tail_index;
} Deque;


int append(Deque * self, void * item) {
  int index = self -> head_index;
  memcpy(self -> contents + index * self -> itemsize, item, self -> itemsize);
  self -> head_index += 1;
  self -> head_index %= self -> max_size;
  return index;
}


int prepend(Deque * self, void * item) {
  int index = self -> tail_index;
  memcpy(self -> contents + index * self -> itemsize, item, self -> itemsize);
  self -> tail_index -= 1;
  if (self -> tail_index < 0) self -> head_index += self -> max_size;
  return index;
}

