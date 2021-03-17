===============
Exceptions in C
===============

Exception handling in C doesn't exist. What's used instead to signify something
went wrong isn't set in stone but usually consists of returning an invalid error
value (such as a negative number for something that can't normally produce
negative numbers) and hoping whoever uses your code remembers to check for
them. Unfortunately, this is effectively what we'll have to do too.

But since we're in Python we can provide wrapper functions which turn our flimsy
error codes into proper Python exceptions which don't need to be continuously
tested for. Before we do that, however, we need to communicate back to Python
that something has gone wrong. This can be easy or very fiddly.

If your function currently returns nothing then you can just get it to return an
is ok* boolean.
If you have more than one way a function can go wrong then you may wish to
use a :class:`cslug.Header` to :ref:`define and share a series of error codes
<Sharing constants between Python and C>` for each case.
If the function does already return something then you'll have to use the
:ref:`return multiple values from a function <Return multiple values from a function>`
trick to give it a second return variable.

The following is an example that shows all the above, using an
automatically generated :class:`header <cslug.Header>` file to share status
constants and :func:`ctypes.byref` to provide both a status output as well as
the intended output of a function.

.. literalinclude:: ../demos/errors/pedantic-log.c
    :language: C
    :caption: pedantic-log.c

.. literalinclude:: ../demos/errors/errors.py
    :caption: accompanying Python code
    :start-at: import enum
    :end-at: return
