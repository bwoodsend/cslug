// -*- coding: utf-8 -*-


class Foo
{
public:
  int add_x_times_y(int x) {
    return (x + this -> x) * this -> y;
  }
  int x;
  float y;
  Foo(int x, float y) {
    this -> x = x;
    this -> y = y;
  }
};


extern "C" {
  int add_1(int);
  float times_2(float);
  Foo make_foo(int x, float y);
  Foo * make_foo_ptr(int x, float y);
  int foo_size();
  auto get_add_x_times_y();
}


Foo make_foo(int x, float y) {
  return Foo(x, y);
}


Foo * make_foo_ptr(int x, float y) {
  return new Foo(x, y);
}

int foo_size() { return sizeof(Foo); }


int add_1(int x) {
  return x + 1;
  }

float times_2(float y) {
  return y * 2.0;
}


auto get_add_x_times_y() {
  return &Foo::add_x_times_y;
}

void (*methods[]) = {
   (void*) &Foo::add_x_times_y,
};
