=============================================
Structs -- Almost Object-Oriented Programming
=============================================

Nothing makes you miss object-oriented programming more than being stuck without
it. Classes are C++ only (which |cslug| doesn't support) but you can get pretty
close using Structures.

|cslug| does relatively little to help here. All it does is parse struct
definitions from your source code and turn them into classes based on the
:class:`ctypes.Structure` template class.

Throughout this page snippets of an example C file will be included. You may
access the whole file with the link below:

.. toctree::

    demo-stubs/cards

Defining a Struct
-----------------

We'll start by writing a simple C file containing a struct definition:

.. literalinclude:: ../demos/structs/cards.c
    :language: C
    :caption: cards.c
    :end-before: /* ---

Note that the simpler ``struct Person {...};`` form of a struct definition is
intentionally not supported. You must use the above ``typedef`` form.


Using a Struct in Python
------------------------

Let's compile the above code and play with it.

.. code-block:: python

    from cslug import CSlug
    slug = CSlug("cards.c")

Structs are available as attributes in exactly the same way as functions. The
structure class forms a neat bucket class in Python::

    >>> slug.dll.Card(6, 2)
    Card(face=6, suit=2)

With sensible (albeit non-configurable) defaults::

    >>> slug.dll.Card(suit=1)
    Card(face=0, suit=1)

And writeable, type-checked attributes corresponding to struct fields::

    >>> slug.dll.Card(4).face
    4


Passing a Struct from Python to C
---------------------------------

First let's extend **cards.c** to define some uninspiring functions which take
our struct as an argument. (Remember to call ``slug.make()`` after modifying the
C code.) We can either pass a structure by value or with a pointer. The
following adds a function for each case.

.. literalinclude:: ../demos/structs/cards.c
    :language: C
    :start-after: /* --- Python to C
    :end-before: /* --- C to Python

To pass by value you can just pass the struct as-is to a C function::

    >>> slug.dll.get_card_face(slug.dll.Card(face=6))
    6

To pass by pointer you need its memory address which is kept for convenience in
a ``_ptr`` attribute. Its value is just the output of
:func:`ctypes.addressof(card)<ctypes.addressof>`.

    >>> card = slug.dll.Card(face=7)
    >>> slug.dll.get_card_ptr_face(card._ptr)
    7

.. warning::

    Using ``slug.dll.Card(face=6)._ptr`` causes the card itself to be
    immediately deleted, leaving a |dangling pointer|. You must retain a
    reference to the original object until after you no longer need the pointer.


Passing a Struct from C to Python
---------------------------------

By Value
........

Returning a struct by value from a C function is straight forward:

.. literalinclude:: ../demos/structs/cards.c
    :language: C
    :start-after: /* --- C to Python
    :end-before: /* --- C to Python by ptr


By Pointer
..........

Returning a struct by pointer is not straight forward. In fact it's highly
discouraged and considered bad C. If you're feeling brave, curious or foolhardy
enough to dismiss this then read on:

The following naive approach creates a :class:`!Card` and returns its
address. But the card is deleted at the end of the function leaving another
|dangling pointer| (your compiler should detect and warn you about this):

.. literalinclude:: ../demos/structs/cards.c
    :language: C
    :start-at: Card * make_card_ptr(
    :end-at: }

We can improve the situation by using ``malloc()``, to reserve memory beyond
the scope of this function call:

.. literalinclude:: ../demos/structs/cards.c
    :language: C
    :start-at: Card * make_card_ptr_safer(
    :end-at: }

This has two problems. First |cslug| doesn't implicitly dereference pointers::

    >>> slug.dll.make_card_ptr_safer(1, 2)
    90846685936

But this is easily solved::

    >>> slug.dll.Card.from_address(slug.dll.make_card_ptr_safer(1, 2))
    Card(face=1, suit=2)

Secondly, this is a |memory leak| because we allocate structs but never free
them again:

.. code-block:: python

    # Watch Python's memory usage go up and up...
    while True:
        slug.dll.make_card_ptr_safer(1, 2)

To deallocate, use ``free()`` to get the memory back once we no longer need the
struct:

.. literalinclude:: ../demos/structs/cards.c
    :language: C
    :start-at: void delete_card(
    :end-at: }

.. code-block:: python

    # This doesn't leak memory.
    while True:
        card = slug.dll.Card.from_address(slug.dll.make_card_ptr_safer(1, 2))
        # Do something with the card.
        # Then delete it safely:
        slug.dll.delete_card(card._ptr)


Warning for Structs Containing Pointers
---------------------------------------

Be vary careful for |dangling pointer|\ s if you're struct contains pointers.
This harmless looking structure, containing a string pointer, is deceptively
dangerous:

.. literalinclude:: ../demos/structs/person.c
    :language: C
    :caption: person.c

.. literalinclude:: ../demos/structs/person.py

Creating a :class:`!Person` in Python is Ok::

    >>> slug.dll.Person("Bill")
    Person(name='Bill')

But creating a :class:`!Person` in a C function isn't.

    >>> slug.dll.make_person("Bill")
    Person(name='璀Ｌ$')

What's happened here is that the string buffer we passed a pointer to is deleted
as soon as ``make_person()`` exits, leaving the ``name`` attribute a dangling
pointer. If you're calling ``make_person()`` from Python like above you can get
around this by maintaining a reference to the buffer in Python::

    >>> import ctypes
    >>> name = ctypes.create_unicode_buffer("Bill")
    >>> slug.dll.make_person(name)
    Person(name='Bill')

But bear in mind that this reference is mutable::

    >>> person = slug.dll.make_person(name)
    >>> person
    Person(name='Bill')
    >>> name.value = "Bob"  # Must be no longer than 'Bill' (<= 4 characters)
    >>> person
    Person(name='Bob')

And easily deletable::

    >>> del name
    >>> person
    Person(name='㟐］$')

This is more subtle when you remember that local variables are deleted at the
end of functions in Python::

    def make_person(name):
        name = ctypes.create_unicode_buffer(name)
        return slug.dll.make_person(name)  # `name` is automatically deleted here.

