"""Test that ``append``/``extend`` go through the value codec.

``ChromaDocuments`` & friends stack ``appendable`` on top of a ``dol`` value
codec. The stacking order matters: when ``appendable`` sits *inside* the codec,
``dol``'s class-wrapping re-installs ``append``/``extend`` as delegated
attributes bound to the (un-codec'd) leaf store, so appended values bypass the
codec entirely. See https://github.com/i2mint/chromadol/issues/2
"""

import chromadb
import pytest

from chromadol.base import (
    AppendableChromaCollection,
    ChromaCollection,
    ChromaDocuments,
    ChromaUris,
)

# The appendable stores, i.e. those whose value codec keeps a single field.
appendable_stores = [ChromaDocuments, ChromaUris]


class _RecordingCollection:
    """Minimal stand-in for a ``chromadb`` Collection, recording ``upsert`` calls."""

    def __init__(self):
        self.upserts = []

    def upsert(self, ids, **kwargs):
        self.upserts.append((ids, kwargs))

    def get(self, ids=None):
        return {"ids": [ids for ids, _ in self.upserts]}

    def count(self):
        return len(self.upserts)

    def delete(self, ids):
        pass


def _documents_store(tmp_path, name):
    """A ``ChromaDocuments`` over a fresh, empty, on-disk collection."""
    client = chromadb.PersistentClient(str(tmp_path / name))
    return ChromaDocuments(client.create_collection(name, get_or_create=True))


@pytest.mark.parametrize("store_cls", appendable_stores, ids=lambda c: c.__name__)
def test_append_writes_what_setitem_writes(store_cls):
    """``append`` must speak the same value language as ``__setitem__``.

    Uses a recording stand-in rather than a real collection so the invariant is
    checked for every appendable store, independently of which ``chromadb``
    field its codec happens to target.
    """
    collection = _RecordingCollection()
    store = store_cls(collection)

    store["a_key"] = "a value"
    store.append("a value")

    (_, via_setitem), (_, via_append) = collection.upserts
    assert via_append == via_setitem


def test_append_goes_through_value_codec(tmp_path):
    docs = _documents_store(tmp_path, "appendtest")
    docs["k1"] = "via setitem"
    assert docs["k1"] == ["via setitem"]

    docs.append("via append")

    assert len(docs) == 2
    (appended_key,) = (k for k in docs if k != "k1")
    assert docs[appended_key] == ["via append"]


def test_extend_goes_through_value_codec(tmp_path):
    docs = _documents_store(tmp_path, "extendtest")

    docs.extend(["first", "second"])

    assert len(docs) == 2
    assert sorted(docs[k][0] for k in docs) == ["first", "second"]


def test_appendable_chroma_collection_appends_raw_chromadb_kwargs(tmp_path):
    """The escape hatch: auto-keyed appends of raw ``chromadb`` kwargs."""
    client = chromadb.PersistentClient(str(tmp_path / "raw"))
    raw = AppendableChromaCollection(
        client.create_collection("raw", get_or_create=True)
    )

    raw.append({"documents": "raw document", "metadatas": {"author": "me"}})

    assert issubclass(AppendableChromaCollection, ChromaCollection)
    assert len(raw) == 1
    (key,) = raw
    record = raw[key]
    assert record["documents"] == ["raw document"]
    assert record["metadatas"] == [{"author": "me"}]
