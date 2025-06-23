.. _datasets:

Datasets and Dataset Collections
--------------------------------

nova-galaxy provides abstractions for handling individual files (`Dataset`) and collections of files (`DatasetCollection`) within Galaxy.

.. code-block:: python

   from nova.galaxy import Dataset, DatasetCollection

   # Create a Dataset from a local file
   my_dataset = Dataset("path/to/my/file.txt")

   # Create a DatasetCollection (implementation for upload pending)
   my_collection = DatasetCollection("path/to/my/collection")


By default Datasets will take their name from the filepath given, but they can be given unique names by passing a string into the constructor.

.. code-block:: python

    my_dataset = Dataset(path="path/to/file.txt", name="cool_dataset_name")

Datasets can be marked as a remote file if you don't want to upload them from your local machine. Remote files are files that your upstream Galaxy instance will have access to.
For example, if your upstream Galaxy instance has access to a directory named `/SNS`, you can load a file from there as a dataset:

.. code-block:: python

    my_dataset = Dataset(path="/SNS/path/to/file.txt", remote_file=True)

Datasets can be uploaded by to a store by calling the upload method.

.. code-block:: python

    connection = Connection("galaxy_url", "galaxy_key").connect()
    store = connection.create_data_store("store")
    my_dataset = Dataset("filepath/file.txt")
    my_dataset.upload(store, name="optional name")


Note, when the remote_files flag is set to true, the files are not actually "uploaded". Instead, they will be ingested into Galaxy as a link to the actual file, so file size should not slow down the system.

When running tools, any Dataset that is used as an input parameter will be automatically uploaded/ingested, unless that dataset has already been uploaded.
In order to force the dataset to be uploaded when a tool runs, even if it has been uploaded before, the dataset can be marked with force_upload:

.. code-block:: python

     my_dataset = Dataset(path="/SNS/path/to/file.txt", force_upload=True)

By default `force_upload` is actually True.

If instead of loading a file from disk or ingesting a file, you want to directly upload some text or some other serializable python value, you can set the dataset content directly:

.. code-block:: python

    my_dataset = Dataset()
    my_dataset.set_content("Some text that will be uploaded as a text file", file_type=".txt")

The `file_type` argument is optional and will default to a text file.

In order to fetch the content of a dataset you can either download the dataset to a path or fetch the content and store it directly in memory (be careful using this with large files.)

.. code-block:: python

    my_dataset.download("/path/to/local/location/where/you/want/to/download/this.txt")
    dataset_content = my_dataset.get_content() # will store content in memory


DatasetCollections currently have less functionality than individual Datasets, as most collections will come from tool outputs.
The `get_content()` method will return a list of info on each element in the collection rather than the content of each element.
The `download()` method will save the collection (with all content included) as a zip archive to the given path.
