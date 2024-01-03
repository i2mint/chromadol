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

    # chromadb is designed to operate on multiple documents at once, so
    # specifying it's keys and contents (and any extras) list this:
    collection[['piece', 'of']] = {
        'documents': ['contents for piece', 'contents for of'],
        'metadatas': [{'author': 'me'}, {'author': 'you'}],
    }
    assert list(collection) == ['piece', 'of']

    assert collection[['piece', 'of']] == {
        'ids': ['piece', 'of'],
        'embeddings': None,
        'metadatas': [{'author': 'me'}, {'author': 'you'}],
        'documents': ['contents for piece', 'contents for of'],
        'uris': None,
        'data': None,
    }

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
