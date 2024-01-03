"""Utils for chromadol."""

from functools import partial
from concurrent.futures import ThreadPoolExecutor


def vectorize(func, iterable=None, *, max_workers: int = 1):
    """Like builtin map, but returns a list,
    and if iterable is None, returns a partial function that can directly be applied
    to an iterable.
    This is useful, for instance, for making a data loader from any single-uri loader.

    Example:
    >>> vectorize(lambda x: x**2, [1,2,3])
    [1, 4, 9]
    >>> vectorized_square = vectorize(lambda x: x**2)
    >>> vectorized_square([1,2,3])
    [1, 4, 9]
    """
    if iterable is None:
        return partial(vectorize, func, max_workers=max_workers)
    if max_workers == 1:
        return list(map(func, iterable))
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(func, iterable))
