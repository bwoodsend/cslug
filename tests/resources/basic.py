import ctypes
import cslug

dll = ctypes.CDLL("./basic.dll")
Foo = cslug._struct.make_struct(
    "Foo",
    [("x", ctypes.c_int), ("y", ctypes.c_float)],
)
dll.make_foo.restype = Foo
dll.make_foo.argtypes = [ctypes.c_int, ctypes.c_float]
assert dll.add_1(10) == 11
foo = dll.make_foo(12, 4.)
print(foo)

dll.make_foo_ptr.restype = ctypes.c_void_p
dll.make_foo_ptr.argtypes = [ctypes.c_int, ctypes.c_float]
