# chromadol

Data Object Layer for ChromaDB

To install:	```pip install chromadol```

[Documentation](https://i2mint.github.io/chromadol/)


# Example usage

To make a `ChromaClient` DOL, you can specify a `chromadb` `Client`, `PersistentClient` (etc.) 
instance, or specify a string (which will be interpreted as a path to a directory to
save the data to in a `PersistentClient` instance).

    >>> from chromadol import ChromaClient
    >>> import tempfile, os 
    >>> with tempfile.TemporaryDirectory() as temp_dir:
    ...     tempdir = os.path.join(temp_dir, "chromadol_test")
    ...     os.makedirs(tempdir)
    >>> client = ChromaClient(tempdir)

Removing all contents of client to be able to run a test on a clean slate

    >>> for k in client:
    ...     del client[k]


There's nothing yet:

    >>> list(client)
    []

Now let's "get" a collection. 

    >>> collection = client['chromadol_test']

Note that just accessing the collection creates it (by default)


    >>> list(client)
    ['chromadol_test']

Here's nothing in the collection yet:

    >>> list(collection)
    []

So let's write something.
Note that `chromadb` is designed to operate on multiple documents at once, 
so the "chromadb-natural" way of specifying it's keys and contents (and any extras) 
would be like this:

    >>> collection[['piece', 'of']] = {
    ...     'documents': ['contents for piece', 'contents for of'],
    ...     'metadatas': [{'author': 'me'}, {'author': 'you'}],
    ... }

Now we have two documents in the collection:

    >>> len(collection)
    2

Note, though, that the order of the documents is not guaranteed.

    >>> sorted(collection)
    ['of', 'piece']

    >>> assert collection['piece'] == {
    ...     'ids': ['piece'],
    ...     'embeddings': None,
    ...     'metadatas': [{'author': 'me'}],
    ...     'documents': ['contents for piece'],
    ...     'uris': None,
    ...     'data': None
    ... }

    >>> assert collection['of'] == {
    ...     'ids': ['of'],
    ...     'embeddings': None,
    ...     'metadatas': [{'author': 'you'}],
    ...     'documents': ['contents for of'],
    ...     'uris': None,
    ...     'data': None
    ... }

You can also read multiple documents at once.
But note that the order of the documents is not guaranteed.

    >>> collection[['piece', 'of']] == collection[['of', 'piece']]
    True

You can read or write one document at a time too.

    >>> collection['cake'] = {
    ...     "documents": "contents for cake",
    ... }
    >>> sorted(collection)  # sorting because order is not guaranteed
    ['cake', 'of', 'piece']
    >>> assert collection['cake'] == {
    ...     'ids': ['cake'],
    ...     'embeddings': None,
    ...     'metadatas': [None],
    ...     'documents': ['contents for cake'],
    ...     'uris': None,
    ...     'data': None,
    ... }

In fact, see that if you only want to specify the "documents" part of the information,
you can just write a string instead of a dictionary:

    >>> collection['cake'] = 'a different cake'
    >>> assert collection['cake'] == {
    ...     'ids': ['cake'],
    ...     'embeddings': None,
    ...     'metadatas': [None],
    ...     'documents': ['a different cake'],
    ...     'uris': None,
    ...     'data': None,
    ... }
