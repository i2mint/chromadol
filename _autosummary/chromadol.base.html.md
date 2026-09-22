# chromadol.base

Base objects for chromadol.

### Functions

| `get_collection`(collection, \*[, codec, client])   |    |
|-----------------------------------------------------|----|
| `identity`(x)                                       |    |

### Classes

| [`AppendableChromaCollection`](#chromadol.base.AppendableChromaCollection)(collection)         | ChromaCollection with `append` and `extend`, auto-generating uuid keys.   |
|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`ChromaClient`](#chromadol.base.ChromaClient)([client, decoder, get_or_create]) |                                                                           |
| [`ChromaCollection`](#chromadol.base.ChromaCollection)(collection)                   |                                                                           |
| [`ChromaDocuments`](#chromadol.base.ChromaDocuments)(collection)                    | ChromaCollection but reading and writing only the 'documents' field.      |
| [`ChromaUris`](#chromadol.base.ChromaUris)(collection)                         | ChromaCollection but reading and writing only the 'uris' field.           |

### *class* chromadol.base.AppendableChromaCollection(collection)

Bases: [`AppendableChromaCollection`](#chromadol.base.AppendableChromaCollection)

ChromaCollection with `append` and `extend`, auto-generating uuid keys.

Items are the raw `chromadb` kwargs mappings that
`ChromaCollection.__setitem__()` accepts (e.g.
`{"documents": ..., "metadatas": ...}`) – use this when you need to append
more than the single field the codec-ed stores below expose.

### *class* chromadol.base.ChromaClient(client=None, \*, decoder=<class 'chromadol.base.ChromaCollection'>, get_or_create=True, \*\*create_collection_kwargs)

Bases: [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

#### clear()

This method is here, in fact, to disable the clear method, that would
otherwise be inherited from MutableMapping.
It’s existence is too dangerous, as it would delete all collections in the
client.
If you want to actually delete all collections in the client, do so explicitly
by iterating over the client and deleting each collection, as such:

```pycon
>>> for k in chroma_client_instance:
...     del chroma_client_instance[k]
```

### *class* chromadol.base.ChromaCollection(collection)

Bases: [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

### *class* chromadol.base.ChromaDocuments(collection)

Bases: [`ChromaDocuments`](#chromadol.base.ChromaDocuments)

ChromaCollection but reading and writing only the ‘documents’ field.

`append` and `extend` take the same values `__setitem__` takes (that is,
the ‘documents’ field’s value), generating uuid keys for them. To write raw
`chromadb` kwargs instead, use `AppendableChromaCollection`.

### *class* chromadol.base.ChromaUris(collection)

Bases: [`ChromaUris`](#chromadol.base.ChromaUris)

ChromaCollection but reading and writing only the ‘uris’ field.
