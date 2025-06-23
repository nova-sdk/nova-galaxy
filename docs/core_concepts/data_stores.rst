.. _data_stores:

Data Stores
-------------------------

A `Datastore` or `Data Store` in nova-galaxy represents a Galaxy history. It serves as a container for organizing your data and tool outputs within Galaxy.

.. code-block:: python

    from nova.galaxy import Nova

    galaxy_url = "your_galaxy_url"
    galaxy_key = "your_galaxy_api_key"
    connection = Connection(galaxy_url, galaxy_key)

    with connection.connect() as conn:
        data_store = conn.create_data_store("My Data Store")

By default data stores are persisted, meaning that their jobs and outputs will be available to retrieve even after the connection is closed.
Datastores (or data stores) also keep their namespace even after the application is exited. Meaning, if you name your data store "Data1", then
if you create a new data store in the future named "Data1" then Nova Galaxy will automatically connect the new instance to the old one, assuming
it has not been deleted.

In order to delete and cleanup your data stores (ie delete all outputs/resources associated with the data store), there are a few methods.

First you can mark a data store for cleanup automatically when you close your nova connection.

.. code-block:: python

    with connection.connect() as conn:
        data_store = conn.create_data_store("My Data Store")
        data_store.mark_for_cleanup()
        # when the 'with' block exits, the data store will be cleaned up.

This will also work when the connection class is used without the 'with' syntax.

.. code-block:: python

    active_connection = connection.connect()
    data_store = conn.create_data_store("My Data Store")
    data_store.mark_for_cleanup()
    active_connection.close()
    # when close() is called, the data store will be cleaned up.


You can also manually clean a data store by invoking the cleanup class method:

.. code-block:: python

    active_connection = connection.connect()
    data_store = active_connection.create_data_store("My Data Store")
    # Do work
    data_store.cleanup()
    data_store = active_connection.create_data_store("My Data Store")
    # In order to use this data store again, you will have to call create_data_store again. This will be an empty store since the previous was cleaned up.

If at any point, you want to persist a store that has been marked for cleanup, you can call the persist class method:

.. code-block:: python

    active_connection = connection.connect()
    data_store = active_connection.create_data_store("My Data Store")
    # Run your first tool
    data_store.cleanup()
    data_store = active_connection.create_data_store("My Data Store")
    # Run your second tool
    data_store.persist()
    active_connection.close()
    # All data in the store from the second tool will be persisted, whereas the first tool's outputs will be gone.
