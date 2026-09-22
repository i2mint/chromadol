"""Base objects for chromadol."""

from __future__ import annotations

from typing import Union, Optional
from collections.abc import MutableMapping, Callable
from dol.appendable import appendable, mk_item2kv_for
from dol import ValueCodecs

from chromadb import Client, PersistentClient, GetResult

dflt_create_collection_kwargs = dict()


def identity(x):
    return x


# def _resolve_codec(codec, kind):
#     if codec is None:
#         return identity
#     elif isinstance(codec, str):
#         field = codec
#         codec = ValueCodecs.single_nested_value(field)
#         if kind == 'encoder':
#             return codec.encoder
#         elif kind == 'decoder':
#             return codec.decoder
#         else:
#             raise ValueError(f'kind must be "encoder" or "decoder", not {kind}')

result_fields = set(GetResult.__annotations__)


# @appendable(item2kv=item2kv)
class ChromaCollection(MutableMapping):
    def __init__(self, collection):
        """
        Initializes the store with a chromadb Collection instance.

        :param collection: An instance of chromadb.Collection.
        """
        self.collection = collection

    @property
    def _ids(self):
        collection_elements = self.collection.get()
        return collection_elements["ids"]

    def __iter__(self):
        return iter(self._ids)

    #: The ``include`` that reads pass to ``collection.get``. ``None`` keeps
    #: chromadb's default (documents and metadatas); a single-field store whose
    #: field is not in that default (e.g. ``uris``) names it here.
    get_include: tuple[str, ...] | None = None

    def __getitem__(self, k: str) -> GetResult:
        if self.get_include is None:
            return self.collection.get(k)
        return self.collection.get(k, include=list(self.get_include))

    def __len__(self):
        return self.collection.count()

    def __contains__(self, k):
        try:
            self.collection.get(k)
            return True
        except KeyError:
            return False

    def __setitem__(self, k: str, v: dict | str):
        return self.collection.upsert(k, **v)

    def __delitem__(self, k: str):
        self.collection.delete(k)


from dol import ValueCodecs

# def int_string(x):
#     return str(int(x))


# item2kv = mk_item2kv_for.utc_key(factor=1e9, time_postproc=int_string)
uuid_key = mk_item2kv_for.uuid_key()


def get_collection(
    collection,
    *,
    codec: Callable | str = identity,
    client: str | Client | None = None,
) -> ChromaCollection:
    if isinstance(collection, str):
        clientdol = ChromaClient(client)
        c = clientdol[collection]
    else:
        c = ChromaCollection(collection)

    if isinstance(codec, str):
        field = codec
        assert field in result_fields, f"codec must be a field name in {result_fields}"
        codec = ValueCodecs.single_nested_value(field)
    else:
        assert callable(codec), "codec must be a callable or a field name"

    return codec(c)


@appendable(item2kv=uuid_key)
class AppendableChromaCollection(ChromaCollection):
    """ChromaCollection with ``append`` and ``extend``, auto-generating uuid keys.

    Items are the raw ``chromadb`` kwargs mappings that
    :meth:`ChromaCollection.__setitem__` accepts (e.g.
    ``{"documents": ..., "metadatas": ...}``) -- use this when you need to append
    more than the single field the codec-ed stores below expose.
    """


# NOTE: `appendable` must be applied OUTSIDE any value codec. Applied inside,
# dol's class-wrapping re-installs `append`/`extend` as delegated attributes bound
# to the un-codec'd leaf store, so appended values bypass the codec and reach
# `ChromaCollection.__setitem__` raw. See https://github.com/i2mint/chromadol/issues/2


@appendable(item2kv=uuid_key)
@ValueCodecs.single_nested_value("documents")
class ChromaDocuments(ChromaCollection):
    """ChromaCollection but reading and writing only the 'documents' field.

    ``append`` and ``extend`` take the same values ``__setitem__`` takes (that is,
    the 'documents' field's value), generating uuid keys for them. To write raw
    ``chromadb`` kwargs instead, use ``AppendableChromaCollection``.
    """


def _nones_to_none(values):
    """``None`` if every item is ``None`` (chromadb's "field not given")."""
    if values is None or all(x is None for x in values):
        return None
    return values


@appendable(item2kv=uuid_key)
@ValueCodecs.single_nested_value("uris")
class ChromaUris(ChromaCollection):
    """ChromaCollection but reading and writing only the 'uris' field.

    Writing uris needs a collection created with a ``data_loader`` (see
    ``chromadol.data_loaders``): the record is embedded from the data it loads.
    ``chromadb`` only does that in ``add`` (``upsert`` and ``update`` embed only
    documents or images), so a new key is added and an existing key is replaced
    (delete, then add, keeping its metadata), and restored if the add fails.
    """

    get_include = ("uris",)

    def __setitem__(self, k, v: dict):
        ids = [k] if isinstance(k, str) else list(k)
        old = self.collection.get(
            ids, include=["embeddings", "metadatas", "documents", "uris"]
        )
        if not old["ids"]:
            return self.collection.add(ids, **v)
        if "metadatas" not in v:  # keep metadata, as ``upsert`` would
            old_metas = dict(zip(old["ids"], old["metadatas"]))
            metas = _nones_to_none([old_metas.get(i) or None for i in ids])
            if metas is not None:
                v = {**v, "metadatas": metas}
        self.collection.delete(old["ids"])
        try:
            return self.collection.add(ids, **v)
        except Exception:
            self.collection.add(
                ids=old["ids"],
                embeddings=old["embeddings"],
                # chromadb reads a record without metadata back as ``{}`` but
                # refuses ``{}`` on write
                metadatas=_nones_to_none([m or None for m in old["metadatas"]]),
                documents=_nones_to_none(old["documents"]),
                uris=old["uris"],
            )
            raise


@ValueCodecs.single_nested_value("metadatas")
class ChromaMetadatas(ChromaCollection):
    """ChromaCollection but reading and writing only the 'metadatas' field.

    Mainly a read view: ``chromadb`` refuses an ``upsert`` that carries neither
    documents nor images, so writing metadata alone raises (that is also why this
    one has no ``append``). Write metadata with the documents, through
    ``ChromaCollection`` or ``AppendableChromaCollection``.
    """


class ChromaClient(MutableMapping):
    def __init__(
        self,
        client=None,
        *,
        decoder=ChromaCollection,
        get_or_create=True,
        **create_collection_kwargs,
    ):
        """
        Initializes the reader with a chromadb Client instance.

        :param client: An instance of chromadb.Client.
        """
        if client is None:
            client = Client()
        elif isinstance(client, str):
            client = PersistentClient(client)
        self.client = client
        self._create_collection_kwargs_for_getitem = dict(
            create_collection_kwargs, get_or_create=get_or_create
        )
        self._create_collection_kwargs_for_setitem = create_collection_kwargs
        self._decoder = decoder or identity

    def __iter__(self):
        """
        Iterates over the names of collections in the chromadb Client.
        """
        return (obj.name for obj in self.client.list_collections())

    def __getitem__(self, k: str):
        """
        Retrieves a collection by its name. Creates the collection if it doesn't exist.

        :param k: The name of the collection to retrieve.
        :return: The collection object.
        """
        return self._decoder(
            self.client.create_collection(
                k, **self._create_collection_kwargs_for_getitem
            )
        )

    def __setitem__(self, k: str, v: dict):
        """
        Creates or updates a collection.

        :param k: The name of the collection.
        :param v: a dict that will be used to populate the collection via .add_documents(**v)
        """
        # Implementation depends on how collections are created or updated in chromadb
        # Example:
        collection = self.client.create_collection(
            name=k, **self._create_collection_kwargs_for_setitem
        )
        if v:
            collection.add_documents(**v)

    def __delitem__(self, k: str):
        """
        Deletes a collection.

        :param k: The name of the collection to delete.
        """
        self.client.delete_collection(k)

    def __len__(self):
        """
        Returns the number of collections in the client.
        """
        return len(self.client.list_collections())

    def __contains__(self, k):
        """
        Returns True if the client has a collection with the given name.
        """
        existing_names = set(self)
        return k in existing_names

    def clear(self):
        """
        This method is here, in fact, to disable the clear method, that would
        otherwise be inherited from MutableMapping.
        It's existence is too dangerous, as it would delete all collections in the
        client.
        If you want to actually delete all collections in the client, do so explicitly
        by iterating over the client and deleting each collection, as such:

        >>> for k in chroma_client_instance:  # doctest: +SKIP
        ...     del chroma_client_instance[k]

        """
        raise NotImplementedError("Disabled for safety reasons.")
