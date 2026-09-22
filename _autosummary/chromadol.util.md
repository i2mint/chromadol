# chromadol.util

Utils for chromadol.

### Functions

| [`add_if_missing`](#chromadol.util.add_if_missing)(collection, ids[, ...])           | Add to collection if not already there.                                                                                                |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| [`argument_value`](#chromadol.util.argument_value)(argname, func, args, kwargs)      | Extract the argument value from a function call, or the default if not given.                                                          |
| [`identity`](#chromadol.util.identity)(x)                                      | The identity function.                                                                                                                 |
| `ids_not_in_collection`(collection, ids)                                                          |                                                                                                                                        |
| `indices_of_id_not_in_collection`(collection, ids)                                                |                                                                                                                                        |
| [`keep_only_include_keys`](#chromadol.util.keep_only_include_keys)(method)                   | Return wrapped method that only subdicts it's outputs to only `include` keys.                                                          |
| [`map_arguments`](#chromadol.util.map_arguments)(func, args, kwargs)                | Get a `{argname: argval, ...}` dict from the args and kwargs of a function call.                                                       |
| [`mapped_list`](#chromadol.util.mapped_list)(func[, iterable, max_workers])       | Like builtin map, but returns a list, and if iterable is None, returns a partial function that can directly be applied to an iterable. |
| [`subdict`](#chromadol.util.subdict)(d, keys)                                 | return a subdict with only the given keys                                                                                              |
| [`transform_methods_to_keep_only_include_keys`](#chromadol.util.transform_methods_to_keep_only_include_keys)(...) | Wraps all methods that contain an `include` argument so they filter their output accordingly.                                          |

### Classes

| [`Delegator`](#chromadol.util.Delegator)(wrapped_obj)   | Delegates all attributes to the wrapped object   |
|---------------------------------------------------------------------------|--------------------------------------------------|

### *class* chromadol.util.Delegator(wrapped_obj)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Delegates all attributes to the wrapped object

### chromadol.util.add_if_missing(collection, ids, embeddings=None, metadatas=None, documents=None, images=None, uris=None)

Add to collection if not already there.

### chromadol.util.argument_value(argname, func, args, kwargs)

Extract the argument value from a function call, or the default if not given.

Note that this

```pycon
>>> func = lambda x, y, z=42: None
>>> argument_value('z', func, [1, 2], {})  # z not given, so use default
42
>>> argument_value('z', func, [1, 2], {'z': 4})  # z given, so use that
4
>>> argument_value('z', func, [1, 2, 3], {})  # y given as positional, so use that
3
```

### chromadol.util.identity(x)

The identity function. Returns what it is given.

* **Return type:**
  [`TypeVar`](https://docs.python.org/3/library/typing.html#typing.TypeVar)(`T`)

### chromadol.util.keep_only_include_keys(method)

Return wrapped method that only subdicts it’s outputs to only `include` keys.

### chromadol.util.map_arguments(func, args, kwargs)

Get a `{argname: argval, ...}` dict from the args and kwargs of a function call.

```pycon
>>> func = lambda x, y, z=42: None
>>> map_arguments(func, [1], {'y': 2})  # x as positional, y as keyword, z not given
{'x': 1, 'y': 2, 'z': 42}
>>> map_arguments(func, [1, 2], {'z': 4})  # z given, so use that
{'x': 1, 'y': 2, 'z': 4}
>>> map_arguments(func, [1, 2, 3], {})  # y given as positional, so use that
{'x': 1, 'y': 2, 'z': 3}
```

### chromadol.util.mapped_list(func, iterable=None, , max_workers=1)

Like builtin map, but returns a list,
and if iterable is None, returns a partial function that can directly be applied
to an iterable.
This is useful, for instance, for making a data loader from any single-uri loader.

### Example

```pycon
>>> mapped_list(lambda x: x**2, [1,2,3])
[1, 4, 9]
>>> squares = mapped_list(lambda x: x**2)  # iterable=None -> partial
>>> squares([1,2,3])
[1, 4, 9]
```

### chromadol.util.subdict(d, keys)

return a subdict with only the given keys

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

```pycon
>>> subdict(dict(a=1, b=2, c=3), ['a', 'c'])
{'a': 1, 'c': 3}
```

### chromadol.util.transform_methods_to_keep_only_include_keys(instance, method_names=('get', 'query'))

Wraps all methods that contain an `include` argument so they filter their output
accordingly.
