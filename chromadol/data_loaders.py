"""Data loaders for ChromaDB."""
import multiprocessing
from typing import Optional, Sequence, List, Union
from operator import attrgetter
from chromadb.api.types import URI, DataLoader
from concurrent.futures import ThreadPoolExecutor


# --------------------------- Examples of loaders ---------------------------

FileContents = Union[str, bytes]  # a type for the contents of a file


def load_text(filepath: str) -> str:
    with open(filepath, "r") as f:
        return f.read()


def load_bytes(filepath: str) -> bytes:
    with open(filepath, "rb") as f:
        return f.read()


def url_to_contents(
    url: str, content_extractor=attrgetter('text'), *, params=None, **kwargs
) -> FileContents:
    import requests

    response = requests.get(url, params=params, **kwargs)
    response.raise_for_status()
    return content_extractor(response)


def pdf_file_text(
    filepath: str, *, page_break_delim='---------------------------'
) -> str:
    from pypdf import PdfReader  # pip install pypdf

    return page_break_delim.join(
        page.extract_text() for page in PdfReader(filepath).pages
    )


# --------------------------- FileLoader ---------------------------


class FileLoader(DataLoader[List[Optional[FileContents]]]):
    """A DataLoader that loads a list of text files from a list of URIs.

    By default, it loads text files from local files, given URIs that are full file paths.
    You can specify a prefix thought (usually used to specify a root directory),
    or a suffix (usually used to specify a file extension).

    Further, you can specify a different `loader`, e.g. to load files from a remote URL,
    or to load binary files, or to load text from pdf files, or from S3, or a database, etc.

    Example:

    >>> rootdir = chromadb.__path__[0] + '/'
    >>> file_loader_1 = FileLoader(prefix=rootdir)
    >>> file_contents_1 = file_loader_1(['__init__.py', 'types.py'])
    >>> len(file_contents_1)
    2
    >>> 'Embeddings' in file_contents_1[0]  # i.e. __init__.py contains the word 'Embeddings'
    >>> 'from typing import' in file_contents_1[1]  # i.e. types.py contains the phrase 'from typing import'

    """

    def __init__(
        self,
        loader=load_text,
        *,
        prefix: str = "",
        suffix: str = "",
        max_workers: int = multiprocessing.cpu_count(),
    ) -> None:
        """
        Args:
            loader: A function that takes a (single) URI and returns its contents
            prefix: A string to prepend to the URI
            suffix: A string to append to the URI
            max_workers: The maximum number of threads to use when loading the URIs
        """
        self._loader = loader
        self._prefix = prefix
        self._suffix = suffix
        self._max_workers = max_workers

    def _load_file(self, uri: Optional[URI]) -> Optional[FileContents]:
        if uri is None:
            return None
        return self._loader(f"{self._prefix}{uri}{self._suffix}")

    def __call__(self, uris: Sequence[Optional[URI]]) -> List[Optional[FileContents]]:
        if isinstance(uris, str):
            # To avoid a common mistake, we cast a string to a list of containing it
            uris = [uris]
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            return list(executor.map(self._load_file, uris))


# add a few loaders as attributes, for convenience
FileLoader.load_text = load_text
FileLoader.load_bytes = load_bytes
FileLoader.url_to_contents = url_to_contents
FileLoader.pdf_file_text = pdf_file_text


def test_file_loader():
    # Here, we'll use the dfault loader, which loads text from local files
    # We'll use the rootdir of the chromadb package as our root directory
    import chromadb

    rootdir = chromadb.__path__[0] + '/'
    file_loader_1 = FileLoader(prefix=rootdir)

    file_contents_1 = file_loader_1(['__init__.py', 'types.py'])
    assert len(file_contents_1) == 2

    # Note: The following two asserts seem faily robust, but still, they assume something
    # about the contents of __init__.py, and types.py, which could change in the future.
    assert 'Embeddings' in file_contents_1[0]
    assert 'from typing import' in file_contents_1[1]

    # See that we could also decide that keys should assume the `.py` extension implicitly:
    file_loader_2 = FileLoader(prefix=rootdir, suffix='.py')

    file_contents_2 = file_loader_2(['__init__', 'types'])
    assert sorted(file_contents_1) == sorted(file_contents_2)

    # Now lets use a different loader: One that returns contents from a remote URL
    file_loader_3 = FileLoader(loader=FileLoader.url_to_contents)
    url = 'https://github.com/chroma-core/chroma/issues/1606'
    contents = file_loader_3(url)[0]
    'vectorizer' in contents  # this issue mentions the term "vectorizer"
