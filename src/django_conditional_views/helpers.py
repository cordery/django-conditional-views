from inspect import isclass


def instantiate(seq, *args, **kwargs):
    """Replace all classes with instantiated versions and return the modified sequence.

    >>> instantiate([list, list((1, 2))], (3,4))
    [[3, 4], [1, 2]]
    """
    output = []
    for x in seq:
        if isclass(x):
            x = x(*args, **kwargs)
        output.append(x)
    return output
