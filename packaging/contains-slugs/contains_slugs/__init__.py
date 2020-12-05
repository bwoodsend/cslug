"""
A very underwhelming package.
"""

from cslug import CSlug, anchor

deep_thought = CSlug(anchor("deep-thought.c"))


def ultimate_answer():
    """The ultimate answer to life, the universe and everything."""
    return deep_thought.dll.ultimate_answer()

def _test():
    """Some sanity checks.

    You shouldn't need this in your code but if you have it, it should pass.
    """
    assert deep_thought.path.exists()
    assert deep_thought.types_dict.json_path.exists()
    assert not deep_thought.sources[0].exists()
    assert ultimate_answer() == 42
    print("ok")
