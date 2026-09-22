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
    ChromaMetadatas,
    ChromaUris,
)

# The appendable stores, i.e. those whose value codec keeps a single field.
appendable_stores = [ChromaDocuments, ChromaUris]


class _RecordingCollection:
    """Minimal stand-in for a ``chromadb`` Collection, recording writes.

    ``upsert`` and ``add`` are both recorded in ``upserts`` (``ChromaUris`` has
    to ``add``, because only ``add`` embeds uris in ``chromadb``).
    """

    def __init__(self):
        self.upserts = []

    def upsert(self, ids, **kwargs):
        self.upserts.append((ids, kwargs))

    add = upsert

    def get(self, ids=None, include=None):
        wanted = None if ids is None else ([ids] if isinstance(ids, str) else ids)
        written = [
            i
            for recorded, _ in self.upserts
            for i in ([recorded] if isinstance(recorded, str) else recorded)
        ]
        return {"ids": [i for i in written if wanted is None or i in wanted]}

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


@pytest.mark.parametrize(
    "store_cls, field",
    [
        (ChromaDocuments, "documents"),
        (ChromaUris, "uris"),
        (ChromaMetadatas, "metadatas"),
    ],
    ids=lambda x: getattr(x, "__name__", x),
)
def test_single_field_stores_write_their_own_chromadb_field(store_cls, field):
    """Each single-field store must write the ``chromadb`` kwarg it is named for.

    ``ChromaUris`` used to be silently redefined by a second class (field
    ``"metadata"``, not even a ``chromadb`` kwarg), so every write raised
    ``TypeError: upsert() got an unexpected keyword argument 'metadata'``.
    """
    collection = _RecordingCollection()
    store_cls(collection)["a_key"] = "a value"
    ((_ids, kwargs),) = collection.upserts
    assert list(kwargs) == [field]


def test_chroma_metadatas_reads_the_metadatas_field(tmp_path):
    client = chromadb.PersistentClient(str(tmp_path / "metas"))
    collection = client.create_collection("metas", get_or_create=True)
    ChromaCollection(collection)["k"] = {
        "documents": "doc",
        "metadatas": {"author": "me"},
    }
    assert ChromaMetadatas(collection)["k"] == [{"author": "me"}]


def _uris_store(tmp_path, name):
    """A ``ChromaUris`` over a collection that loads uris as text files."""
    from chromadol.data_loaders import FileLoader

    client = chromadb.PersistentClient(str(tmp_path / name))
    collection = client.create_collection(name, data_loader=FileLoader())
    return ChromaUris(collection), collection


def test_chroma_uris_round_trips_against_real_chromadb(tmp_path):
    """Write, read, overwrite and append uris on a real ``chromadb`` collection.

    ``upsert`` refuses a record with only uris ("Exactly one of documents,
    images must be provided"), and a default ``get`` leaves ``uris`` out, so a
    store that upserts and reads with the default include can neither write nor
    read. A recording fake cannot see either problem.
    """
    for name in ("a", "b", "c"):
        (tmp_path / f"{name}.txt").write_text(f"contents of {name}")
    uris, collection = _uris_store(tmp_path, "uristest")
    a, b, c = (str(tmp_path / f"{n}.txt") for n in "abc")

    uris["k"] = a
    assert uris["k"] == [a]
    uris["k"] = c  # overwrite a key that has no metadata
    assert uris["k"] == [c]

    collection.update(ids="k", metadatas={"author": "me"})
    uris["k"] = b  # overwrite an existing key
    assert uris["k"] == [b]
    assert collection.get("k")["metadatas"] == [{"author": "me"}]
    assert len(uris) == 1

    uris.append(c)
    assert len(uris) == 2
    assert sorted(uris[key][0] for key in uris) == [b, c]


def test_chroma_uris_overwrite_that_fails_keeps_the_old_record(tmp_path):
    (tmp_path / "a.txt").write_text("contents of a")
    uris, collection = _uris_store(tmp_path, "uriskeep")
    a = str(tmp_path / "a.txt")
    uris["k"] = a

    with pytest.raises(Exception):
        uris["k"] = str(tmp_path / "missing.txt")  # the data loader can't load it

    assert uris["k"] == [a]
