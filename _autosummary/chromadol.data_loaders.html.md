# chromadol.data_loaders

Data loaders for ChromaDB.

### Functions

| `load_bytes`(filepath)                              |    |
|-----------------------------------------------------|----|
| `load_text`(filepath)                               |    |
| `pdf_file_text`(filepath, \*[, page_break_delim])   |    |
| `test_file_loader`()                                |    |
| `url_to_contents`(url[, content_extractor, params]) |    |

### Classes

| [`FileLoader`](#chromadol.data_loaders.FileLoader)([loader, prefix, suffix, max_workers])   | A DataLoader that loads a list of text files from a list of URIs.   |
|------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| [`MappingLoader`](#chromadol.data_loaders.MappingLoader)(mapping, \*[, key_type, ...])         |                                                                     |

### *class* chromadol.data_loaders.FileLoader(loader=<function load_text>, \*, prefix='', suffix='', max_workers=4)

Bases: `DataLoader`[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes) | [`None`](https://docs.python.org/3/builtins/constants.html#None)]]

A DataLoader that loads a list of text files from a list of URIs.

By default, it loads text files from local files, given URIs that are full file paths.
You can specify a prefix thought (usually used to specify a root directory),
or a suffix (usually used to specify a file extension).

Further, you can specify a different `loader`, e.g. to load files from a remote URL,
or to load binary files, or to load text from pdf files, or from S3, or a database, etc.

### Example

```pycon
>>> import chromadb
>>> rootdir = chromadb.__path__[0] + '/'
>>> file_loader_1 = FileLoader(prefix=rootdir)
>>> file_contents_1 = file_loader_1(['__init__.py', 'types.py'])
>>> len(file_contents_1)
2
>>> 'Embeddings' in file_contents_1[0]  # i.e. __init__.py contains the word 'Embeddings'
True
>>> 'from typing import' in file_contents_1[1]  # i.e. types.py contains the phrase 'from typing import'
True
```

### *class* chromadol.data_loaders.MappingLoader(mapping, \*, key_type=<class 'str'>, ingress=<function identity>, egress=<function identity>, max_workers=None)

Bases: `DataLoader`
