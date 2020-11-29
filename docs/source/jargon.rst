========
Glossary
========


.. glossary::

    pointer

        The memory address of an object stored in another variable.

    dangling pointer

        A pointer whose target object has been deleted leaving it pointing to
        trash memory.

        Attempting to read or write the contents of this pointer will either
        yield incorrect results, raise an :class:`OSError` or cause a
        |seg-fault|.

    shared library

        An executable file containing definitions (function/variables/...) but
        no main method.

        Shared libraries are analogous to Python libraries.

    binaries

        Nick-name for |shared library|.

    DLL

        Windows only alias for a |shared library|.

        Stands for *dynamically linked library*.

    memory leak

        Memory allocated but never freed.

        In C this equates to a call to ``malloc()`` (or one of its siblings)
        without a later call to ``free()``. If enough memory is *leaked*, your
        program will eventually run into MemoryErrors.


    seg-fault

        A fatal error raised when trying to read/write memory that isn't owned
        by Python.

        This error is so deep that it immediately kills Python, bypassing
        Python's own error handling mechanisms meaning this error can not be
        caught by a ``try: ... except: ...`` clause. You also don't get a nice
        Python error stacktrace making it harder to diagnose.

        Windows is slightly nicer than Unix in that you usually get
        :class:`OSError`\ s (which are catchable) instead of seg-faults.

    null terminated

        Ends with a zero byte to signify end of string.

        Strings in C (just arrays of characters) don't know their own length. As
        a lazy alternative to having to keep track of string lengths in separate
        integer variables, a string can sometimes be null terminated instead. If
        the string contains zeros then this is not an option.

        Note that *zero* is ascii zero, denoted by ``'\x00'`` or ``chr(0)`` in
        Python or ``'\00'`` in C, not simply the character ``'0'`` (which is
        actually ``'\\30'`` or ``48`` in C).

