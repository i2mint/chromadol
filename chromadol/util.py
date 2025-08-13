"""Utils for chromadol."""

from functools import partial
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar, Optional, Iterable, Union, Mapping
from collections.abc import Container
from chromadb import Collection
from chromadb.api.types import ID

from i2 import Sig

T = TypeVar('T')
Some = Union[T, Iterable[T]]
MaybeSome = Optional[Some[T]]
IDs = MaybeSome[ID]


def identity(x: T) -> T:
    """The identity function. Returns what it is given."""
    return x


def mapped_list(func, iterable=None, *, max_workers: int = 1):
    """Like builtin map, but returns a list,
    and if iterable is None, returns a partial function that can directly be applied
    to an iterable.
    This is useful, for instance, for making a data loader from any single-uri loader.

    Example:
    >>> mapped_list(lambda x: x**2, [1,2,3])
    [1, 4, 9]
    >>> squares = vectorize(lambda x: x**2)
    >>> squares([1,2,3])
    [1, 4, 9]
    """
    if iterable is None:
        return partial(mapped_list, func, max_workers=max_workers)
    if max_workers == 1:
        return list(map(func, iterable))
    else:
        if max_workers is None:
            # Take the number of CPUs as the max_workers
            max_workers = __import__('multiprocessing').cpu_count()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(func, iterable))


def subdict(d: Mapping, keys: Container) -> dict:
    """return a subdict with only the given keys

    >>> subdict(dict(a=1, b=2, c=3), ['a', 'c'])
    {'a': 1, 'c': 3}
    """
    return {k: v for k, v in d.items() if k in keys}


def indices_of_id_not_in_collection(collection: Collection, ids: MaybeSome[ID]):
    found_ids = set(collection.get(ids=ids, include=[]).get('ids', []))
    return [i for i, id_ in enumerate(ids) if id_ not in found_ids]


def ids_not_in_collection(collection: Collection, ids: MaybeSome[ID]):
    found_ids = set(collection.get(ids=ids, include=[]).get('ids', []))
    return [id_ for id_ in ids if id_ not in found_ids]


@(Sig(Collection.add).ch_names(self='collection'))
def add_if_missing(collection: Collection, ids: MaybeSome[ID], **kwargs):
    """Add to collection if not already there."""

    if ids:
        missing_indices = indices_of_id_not_in_collection(collection, ids)
        get_missing = lambda array, idx: [array[i] for i in missing_indices]
        # take the get_missing_only subset of each array-valued kwarg value
        if missing_indices:
            kwargs = dict(kwargs, ids=ids)
            kwargs = {k: get_missing(v, missing_indices) for k, v in kwargs.items()}
            return collection.add(**kwargs)


from inspect import signature
from functools import wraps


def map_arguments(func, args, kwargs):
    """
    Get a `{argname: argval, ...}` dict from the args and kwargs of a function call.

    >>> func = lambda x, y, z=42: None
    >>> map_arguments(func, [1], {'y': 2})  # x as positional, y as keyword, z not given
    {'x': 1, 'y': 2, 'z': 42}
    >>> map_arguments(func, [1, 2], {'z': 4})  # z given, so use that
    {'x': 1, 'y': 2, 'z': 4}
    >>> map_arguments(func, [1, 2, 3], {})  # y given as positional, so use that
    {'x': 1, 'y': 2, 'z': 3}
    """
    b = signature(func).bind(*args, **kwargs)
    b.apply_defaults()
    return b.arguments


def argument_value(argname, func, args, kwargs):
    """
    Extract the argument value from a function call, or the default if not given.

    Note that this

    >>> func = lambda x, y, z=42: None
    >>> argument_value('z', func, [1, 2], {})  # z not given, so use default
    42
    >>> argument_value('z', func, [1, 2], {'z': 4})  # z given, so use that
    4
    >>> argument_value('z', func, [1, 2, 3], {})  # y given as positional, so use that
    3
    """
    kwargs = map_arguments(func, args, kwargs)
    return kwargs[argname]


def keep_only_include_keys(method):
    """Return wrapped method that only subdicts it's outputs to only `include` keys."""

    @wraps(method)
    def _wrapped(*args, **kwargs):
        kwargs = map_arguments(method, args, kwargs)
        include = list(kwargs.get('include', []))
        keep_keys = ['ids'] + include
        return subdict(method(*args, **kwargs), keep_keys)

    return _wrapped


# TODO: The pydantic.BaseModel parent class of Collection forbids me to re-assign methods
#  so I need to wrap the whole Collection
class Delegator:
    """Delegates all attributes to the wrapped object"""

    def __init__(self, wrapped_obj):
        self.wrapped_obj = wrapped_obj

    def __getattr__(self, attr):  # delegation: just forward attributes to wrapped_obj
        return getattr(self.wrapped_obj, attr)


def _methods_containing_include_argument(obj, argname='include'):
    """Outputs all (non-underscored) method names of an object that contain
    a specific argument (by default, 'include').

    At the time of writing this, I get:

    >>> sorted(
    ...     _methods_containing_include_argument(
    ...         __import__('chromadb').Collection,
    ...         argname='include'
    ...     )
    ... )
    ['copy', 'dict', 'get', 'json', 'query']

    """
    return [
        method_name
        for method_name in dir(obj)
        if not method_name.startswith('_')
        and callable(method := getattr(obj, method_name))
        and argname in signature(method).parameters
    ]


def transform_methods_to_keep_only_include_keys(
    instance, method_names=('get', 'query')
):
    """
    Wraps all methods that contain an `include` argument so they filter their output
    accordingly.
    """
    delegated = Delegator(instance)
    for method_name in dir(instance):
        if not method_name.startswith('_'):
            method = getattr(instance, method_name)
            if callable(method) and 'include' in signature(method).parameters:
                setattr(delegated, method_name, keep_only_include_keys(method))
    return delegated
