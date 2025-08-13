"""Test util module"""

from chromadol.util import transform_methods_to_keep_only_include_keys


def test_transform_methods_to_keep_only_include_keys():
    from chromadb import EphemeralClient

    collection = EphemeralClient().get_or_create_collection('test_inclusion_filter')
    # Empty the collection
    if ids := collection.get()['ids']:
        collection.delete(ids)

    collection.add(ids=['apple', 'banana'], documents=['crumble', 'split'])

    assert collection.get() == {
        'ids': ['apple', 'banana'],
        'embeddings': None,
        'metadatas': [None, None],
        'documents': ['crumble', 'split'],
        'uris': None,
        'data': None,
    }

    wrapped_collection = transform_methods_to_keep_only_include_keys(collection)

    # Now see that there's only 3 fields (the default include value of Collection.get)
    assert wrapped_collection.get() == {
        'ids': ['apple', 'banana'],
        'metadatas': [None, None],
        'documents': ['crumble', 'split'],
    }

    assert wrapped_collection.get(include=['uris']) == {
        'ids': ['apple', 'banana'],
        'uris': [None, None],
    }

    # Original query method
    result = collection.query(query_texts='split', n_results=1)
    assert list(result) == [
        'ids',
        'distances',
        'metadatas',
        'embeddings',
        'documents',
        'uris',
        'data',
    ]

    filtered_result = wrapped_collection.query(
        query_texts='split', n_results=1, include=['documents', 'distances']
    )
    assert list(filtered_result) == ['ids', 'distances', 'documents']