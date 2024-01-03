"""Test base.py"""


from chromadol.base import ChromaClient


def test_simple():
    """A simple test of the ChromaClient and ChromaCollection classes."""

    
    import tempfile, os 
    with tempfile.TemporaryDirectory() as temp_dir:
        tempdir = os.path.join(temp_dir, "chromadol_test")
        os.makedirs(tempdir)
    client = ChromaClient(tempdir)

    # removing all contents of client to be able to run a test on a clean slate
    for k in client:
        del client[k]
    assert list(client) == []
    collection = client['chromadol_test']
    # note that just accessing the collection creates it (by default)
    assert list(client) == ['chromadol_test']
    assert list(collection) == []
    assert len(collection) == 0

    # chromadb is designed to operate on multiple documents at once, so
    # specifying it's keys and contents (and any extras) list this:
    collection[['piece', 'of']] = {
        'documents': ['contents for piece', 'contents for of'],
        'metadatas': [{'author': 'me'}, {'author': 'you'}],
    }

    # Now we have two documents in the collection:

    assert len(collection) == 2

    # Note, though, that the order of the documents is not guaranteed.

    assert sorted(collection) == ['of', 'piece']

    assert collection['piece'] == {'ids': ['piece'],
    'embeddings': None,
    'metadatas': [{'author': 'me'}],
    'documents': ['contents for piece'],
    'uris': None,
    'data': None}

    assert collection['of'] == {'ids': ['of'],
    'embeddings': None,
    'metadatas': [{'author': 'you'}],
    'documents': ['contents for of'],
    'uris': None,
    'data': None}

    # You can also read multiple documents at once.
    # But note that the order of the documents is not guaranteed.
    assert collection[['piece', 'of']] == collection[['of', 'piece']]

    # But you can read or write one document at a time too.
    collection['cake'] = {
        "documents": "contents for cake",
    }
    assert list(collection) == ['piece', 'of', 'cake']
    assert collection['cake'] == {
        'ids': ['cake'],
        'embeddings': None,
        'metadatas': [None],
        'documents': ['contents for cake'],
        'uris': None,
        'data': None,
    }

    # In fact, see that if you only want to specify the "documents" part of the information,
    collection['cake'] = 'a different cake'
    assert collection['cake'] == {
        'ids': ['cake'],
        'embeddings': None,
        'metadatas': [None],
        'documents': ['a different cake'],
        'uris': None,
        'data': None,
    }

    # The `collection` instance is not only dict-like, but also list-like in the 
    # sense that it has an `.append` and an `.extend` method.

    assert len(collection) == 3
    collection.extend(['two documents', 'specified without keys'])
    assert len(collection) == 5

