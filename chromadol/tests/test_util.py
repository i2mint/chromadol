"""Test util module"""

from chromadol.util import transform_methods_to_keep_only_include_keys


def test_transform_methods_to_keep_only_include_keys():
    from chromadb import EphemeralClient

    collection = EphemeralClient().get_or_create_collection('test_inclusion_filter')
    # Empty the collection
    if ids := collection.get()['ids']:
        collection.delete(ids)

    collection.add(ids=['apple', 'banana'], documents=['crumble', 'split'])

    # Raw chromadb returns the full record. Newer chromadb versions add volatile
    # keys (e.g. 'included'), so check the meaningful fields rather than exact
    # equality.
    raw = collection.get()
    assert raw['ids'] == ['apple', 'banana']
    assert raw['documents'] == ['crumble', 'split']
    assert raw['metadatas'] == [None, None]
    assert {'ids', 'documents', 'metadatas', 'embeddings', 'uris', 'data'} <= set(raw)

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

    # Original query method returns all standard fields (key order and extra
    # volatile keys like 'included' vary by chromadb version).
    result = collection.query(query_texts='split', n_results=1)
    assert {
        'ids',
        'distances',
        'metadatas',
        'embeddings',
        'documents',
        'uris',
        'data',
    } <= set(result)

    filtered_result = wrapped_collection.query(
        query_texts='split', n_results=1, include=['documents', 'distances']
    )
    assert set(filtered_result) == {'ids', 'distances', 'documents'}