// -*- coding: utf-8 -*-


class Foo
{
public:
  int add_3(int x) {
    return x + 3;
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
  int Foo::add_3(int);
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
