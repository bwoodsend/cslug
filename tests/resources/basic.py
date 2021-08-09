import ctypes
import cslug

dll = ctypes.CDLL("./a.out")
Foo = cslug._struct.make_struct(
    "Foo",
    [("x", ctypes.c_int), ("y", ctypes.c_float)],
)
dll.make_foo.restype = Foo
dll.make_foo.argtypes = [ctypes.c_int, ctypes.c_float]
assert dll.add_1(10) == 11
foo = dll.make_foo(12, 5.)
print(foo)

dll.make_foo_ptr.restype = ctypes.c_void_p
dll.make_foo_ptr.argtypes = [ctypes.c_int, ctypes.c_float]

dll.get_add_x_times_y.restype = ctypes.c_void_p

add_x_times_y = dll._FuncPtr(dll.get_add_x_times_y())
add_x_times_y.argtypes = [ctypes.POINTER(Foo), ctypes.c_int]

print(f"{foo}.add_x_times_y(3)",
      f"({foo.x} + 3) * {foo.y}",
      f"{add_x_times_y(foo,3)}", sep=" = ")
