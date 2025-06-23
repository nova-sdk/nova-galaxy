.. _dataset_collections:

Example 3: Handling Dataset Collections
---------------------------------------

This example illustrates how to work with dataset collections (note that uploading collections is not yet implemented).

.. code-block:: python

   from nova.galaxy import Nova, DatasetCollection

   galaxy_url = "your_galaxy_url"
   galaxy_key = "your_galaxy_api_key"
   nova = Connection(galaxy_url, galaxy_key)

   with nova.connect() as conn:
       data_store = conn.create_data_store("Collection Example")

       # Assume the collection is already uploaded and you have its ID
       my_collection = DatasetCollection("My Collection")
       my_collection.id = "your_collection_id" # Replace with your collection id
       my_collection.store = data_store

       # Download the collection
       my_collection.download("path/to/output/directory")

       # Get info of each element of the collection
       content = my_collection.get_content()
       print(content)
