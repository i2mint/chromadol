"""Base objects for chromadol."""

from typing import MutableMapping, Union
from functools import cached_property
from dol.appendable import appendable, mk_item2kv_for

from chromadb import Client, PersistentClient, GetResult

dflt_create_collection_kwargs = dict()


class ChromaClient(MutableMapping):
    def __init__(self, client=None, *, get_or_create=True, **create_collection_kwargs):
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
        return ChromaCollection(
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




def int_string(x):
    return str(int(x))


item2kv = mk_item2kv_for.utc_key(factor=1e9, time_postproc=int_string)


@appendable(item2kv=item2kv)
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
        return collection_elements['ids']

    def __iter__(self):
        return iter(self._ids)

    def __getitem__(self, k: str) -> GetResult:
        return self.collection.get(k)

    def __len__(self):
        return self.collection.count()

    def __contains__(self, k):
        try:
            self.collection.get(k)
            return True
        except KeyError:
            return False

    def __setitem__(self, k: str, v: Union[dict, str]):
        if isinstance(v, str):
            v = {'documents': [v]}
        self.collection.upsert(k, **v)

    def __delitem__(self, k: str):
        self.collection.delete(k)
