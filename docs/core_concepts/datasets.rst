.. _datasets:

Datasets and Dataset Collections
--------------------------------

nova-galaxy provides abstractions for handling individual files (`Dataset`) and collections of files (`DatasetCollection`) within Galaxy.

.. literalinclude:: ../../tests/test_dataset.py
    :start-after: create dataset
    :end-before: create dataset complete
    :dedent:

.. literalinclude:: ../../tests/test_dataset.py
    :start-after: create dataset collection
    :end-before: create dataset collection complete
    :dedent:


By default Datasets will take their name from the filepath given, but they can be given unique names by passing a string into the constructor in the `name` parameter.


Datasets can be marked as a remote file if you don't want to upload them from your local machine. Remote files are files that your upstream Galaxy instance will have access to.
For example, if your upstream Galaxy instance has access to a directory named `/SNS`, you can load a file from there as a dataset:

.. literalinclude:: ../../tests/test_dataset.py
    :start-after: create remote dataset
    :end-before: create remote dataset complete
    :dedent:

Datasets can be uploaded to a store by calling the upload method.


.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: existing dataset input
    :end-before: existing dataset input complete
    :dedent:

Note, when the remote_files flag is set to true, the files are not actually "uploaded". Instead, they will be ingested into Galaxy as a link to the actual file, so file size should not slow down the system.

When running tools, any Dataset that is used as an input parameter will be automatically uploaded/ingested, unless that dataset has already been uploaded.
In order to force the dataset to be uploaded when a tool runs, even if it has been uploaded before, the dataset can be marked with `force_upload` by passing in a boolean value to that parameter in the constructor.

By default `force_upload` is actually True.

If instead of loading a file from disk or ingesting a file, you want to directly upload some text or some other serializable python value, you can set the dataset content directly:

.. literalinclude:: ../../tests/test_dataset.py
    :start-after: set dataset content
    :end-before: set dataset content complete
    :dedent:

The `file_type` argument is optional and will default to a text file.

In order to fetch the content of a dataset you can either download the dataset to a path  using `download()` or fetch the content and store it directly in memory using `get_content()` (be careful using this with large files.)


DatasetCollections currently have less functionality than individual Datasets, as most collections will come from tool outputs.
The `get_content()` method will return a list of info on each element in the collection rather than the content of each element.
The `download()` method will save the collection (with all content included) as a zip archive to the given path.
