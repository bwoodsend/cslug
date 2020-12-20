"""
A very underwhelming package.
"""

from cslug import CSlug, anchor

deep_thought = CSlug(anchor("deep-thought.c"))


def ultimate_answer():
    """The ultimate answer to life, the universe and everything."""
    return deep_thought._dll_.ultimate_answer()


def _test():
    """Some sanity checks.

    You shouldn't need this in your code but if you have it, it should pass.
    """
    assert deep_thought._path_.exists()
    assert deep_thought._type_map_.json_path.exists()
    assert not deep_thought._sources_[0].exists()
    assert ultimate_answer() == 42
    print("ok")
