========
Glossary
========


.. glossary::

    Pointer

        The memory address of an object stored in another variable.

        Pointers are also used in C to reference arrays. An array  ``a``  is
        simply a pointer to its first element ``&a[0]``. ``*a`` and ``a[0]`` are
        thereby also interchangeable.

        Pointers to arrays may be used with arithmetic to get other elements.
        ``*(a + 3)`` is the same as ``a[3]`` (even if the item size of ``a``\ s
        elements is not one).

    Dangling Pointer

        A pointer whose target object has been deleted leaving it pointing to
        trash memory.

        Attempting to read or write the contents of this pointer will yield
        incorrect results if the target memory is still owned by Python. If
        Python has released the memory it will raise an :class:`OSError` error
        on Windows or cause a |seg-fault| on Unix.

    Shared Library

        An executable file containing definitions (function/variables/...) but
        no main method.

        Shared libraries are analogous to Python libraries.

    Binaries

        Nick-name for |shared library|.

    DLL

        A Windows only alias for a |shared library|.

        Stands for *dynamically linked library*.

    Memory Leak

        Memory allocated but never freed.

        In C this equates to a call to ``malloc()`` (or one of its siblings)
        without a later call to ``free()``. If enough memory is *leaked*, your
        program will eventually run into MemoryErrors.


    Seg-fault

        A fatal error raised when trying to read/write memory that isn't (or no
        longer is) owned by Python.

        This error is so deep that it immediately kills Python, bypassing
        Python's own error handling mechanisms meaning that this error can not
        be caught by a ``try: ... except: ...`` clause. You also don't get a
        nice Python error stacktrace making it harder to diagnose.

        Windows is slightly nicer here than Unix in that you usually get
        :class:`OSError`\ s, which are native Python exceptions that can you
        which function went wrong, instead of seg-faults.

    NULL Terminated

        A Null terminated string has an additional zero character on the end to
        signify the end of the string.

        Strings in C, which are just arrays (which are just |pointers| to the
        first element) of characters, don't know their own length. As a somewhat
        lazy alternative to having to keep track of string lengths separately, a
        string can instead use zero (which isn't a type-able character) to mark
        the end. If the string is non-text and could already contain zeros then
        this is not an option.

        Note that *zero* in this context is ascii/unicode zero, denoted by
        ``'\x00'`` or ``chr(0)`` in Python, or ``'\00'`` or ``0`` in C, not
        simply the character ``'0'`` (which is actually ``'\\30'`` or ``48`` in
        C).

        See :ref:`Null terminated or not null terminated?` for when it safe to
        assume null-termination.
