"""Test base.py"""


from chromadol.base import ChromaClient


def _record_includes(record, expected):
    """Whether ``record`` contains all the ``expected`` key->value pairs.

    chromadb's get-record shape carries volatile keys that drift across
    versions (e.g. ``included``, and the ``embeddings`` / ``uris`` / ``data``
    null-defaults), so asserting full equality is brittle. We assert only the
    stable, meaningful subset.
    """
    return all(record.get(k) == v for k, v in expected.items())


def test_simple():
    """A simple test of the ChromaClient and ChromaCollection classes."""

    import tempfile, os

    with tempfile.TemporaryDirectory() as temp_dir:
        tempdir = os.path.join(temp_dir, 'chromadol_test')
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

    assert _record_includes(collection['piece'], {
        'ids': ['piece'],
        'metadatas': [{'author': 'me'}],
        'documents': ['contents for piece'],
    })

    assert _record_includes(collection['of'], {
        'ids': ['of'],
        'metadatas': [{'author': 'you'}],
        'documents': ['contents for of'],
    })

    # You can also read multiple documents at once.
    # But note that the order of the documents is not guaranteed.
    assert collection[['piece', 'of']] == collection[['of', 'piece']]

    # But you can read or write one document at a time too.
    collection['cake'] = {
        'documents': 'contents for cake',
    }
    assert set(collection) == {'piece', 'of', 'cake'}
    assert _record_includes(collection['cake'], {
        'ids': ['cake'],
        'metadatas': [None],
        'documents': ['contents for cake'],
    })

    # # In fact, see that if you only want to specify the "documents" part of the information,
    # collection['cake'] = 'a different cake'
    # assert collection['cake'] == {
    #     'ids': ['cake'],
    #     'embeddings': None,
    #     'metadatas': [None],
    #     'documents': ['a different cake'],
    #     'uris': None,
    #     'data': None,
    # }

    # # The `collection` instance is not only dict-like, but also list-like in the
    # # sense that it has an `.append` and an `.extend` method.

    # assert len(collection) == 3
    # collection.extend(['two documents', 'specified without keys'])
    # assert len(collection) == 5
