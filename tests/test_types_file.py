# -*- coding: utf-8 -*-
"""
"""
import io
import json
import cslug

SOURCE = """
// Something simple.
void main()

// Arguments of just ``void`` should be ignored.
bool many_voids(void, void, void)

// Some random types.
int foo(char x)
float bar(int32_t a, int16_t b, uint64_t c)
short whack(unsigned long d, double e, long)

// All pointers reduce to just void pointer.
void * baz(float * a, int **, * Custom, *Custom, Custom*, Custom  *  )

// Invalid syntax defaults to ``None`` - leave the compiler to raise any issues.
char zap(I like cake)

// Likewise with invalid types.
void flop(long long long)

// Unicode shouldn't break anything...
byte ÀÂÄÆÈÊÌÎÐÒÔÖÙÛÝßáãåçéëíïñóõøùûýÿ(شيء * مخصص, 習俗 ** 事情)
"""

PARSED = {
    'main': ['None', []],
    'many_voids': ['c_bool', []],
    'foo': ['c_long', ['c_char']],
    'bar': ['c_float', ['c_long', 'c_short', 'c_ulonglong']],
    'whack': ['c_short', ['c_ulong', 'c_double', 'c_long']],
    'baz': ['c_void_p', ['c_void_p'] * 6],
    'zap': ['c_char', ['None']],
    'flop': ['None', ['None']],
    'ÀÂÄÆÈÊÌÎÐÒÔÖÙÛÝßáãåçéëíïñóõøùûýÿ': ['c_byte', ['c_void_p', 'c_void_p']]
}


def test_io():
    self = cslug.Types(io.StringIO(), io.StringIO(SOURCE))
    assert self.types == PARSED
    assert json.loads(self.json_path.getvalue()) == PARSED
