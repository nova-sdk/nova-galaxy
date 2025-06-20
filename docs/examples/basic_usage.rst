.. _basic_usage:

Example 1: Uploading a Dataset and Running a Tool
--------------------------------------------------

This example demonstrates how to upload a dataset to Galaxy and run a tool using nova-galaxy.

.. code-block:: python

   from nova.galaxy import Connection, Dataset, Tool, Parameters

   galaxy_url = "your_galaxy_url"
   galaxy_key = "your_galaxy_api_key"
   nova = Connection(galaxy_url, galaxy_key)

   with nova.connect() as conn:
       # Create a data store
       data_store = conn.create_data_store("Example Data Store")

       # Create a dataset from a local file
       my_dataset = Dataset("path/to/your/file.txt", name="My Dataset")

       # Upload the dataset to Galaxy
       my_dataset.upload(data_store)

       # Define tool parameters
       params = Parameters()
       params.add_input("input", my_dataset)
       params.add_input("some_parameter", 10)

       # Get the tool
       my_tool = Tool("add_value") # Replace with the actual tool ID

       # Run the tool
       outputs = my_tool.run(data_store, params)

       # Get an output dataset
       output_dataset = outputs.get_dataset("out_file1")

       # Download the output dataset
       output_dataset.download("path/to/output/directory")

       # Get the content of the output dataset
       content = output_dataset.get_content()
       print(content)
       # Because data stores persist by default, this content will still be saved after the with block is exited.


Example 2: Manually managing a Connection
--------------------------------------------------
.. code-block:: python

    from nova.galaxy import Connection, Dataset, Tool, Parameters

        galaxy_url = "your_galaxy_url"
        galaxy_key = "your_galaxy_api_key"
        nova = Connection(galaxy_url, galaxy_key)

        # Open the connection
        conn = nova.connect()

        # Create a data store
        data_store = conn.create_data_store("Example Data Store")

        # Create a dataset from a local file
        my_dataset = Dataset("path/to/your/file.txt")

        # Define tool parameters
        params = Parameters()
        params.add_input("input", my_dataset)

        # Get the tool
        my_tool = Tool("some_tool_id") # Replace with the actual tool ID

        # Run the tool asynchronously
        my_tool.run(data_store, params, wait=False)

        # Get Tool Status
        print(my_tool.get_status())

        # Wait for tool to finish
        my_tool.wait_for_results()

        # Get the results from the tool
        results = my_tool.get_results()
        output_coll = results.get_collection("my_output_collection")

        # Download the output collection to a local path
        output_coll.download("/local/path/where/I/want/to/download/")

        # Clean data store (remove all files and outputs) after connection is closed
        data_store.mark_for_cleanup()

        # Manually close connection
        conn.close()
        # Results have been removed from upstream since data store was cleaned up.
