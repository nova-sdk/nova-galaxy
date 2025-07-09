.. _data_stores:

Data Stores
-------------------------

A `Datastore` or `Data Store` in nova-galaxy represents a Galaxy history. It serves as a container for organizing your data and tool outputs within Galaxy.

You will need to create your connection as is standard with the galaxy_url and galaxy_key values set.

.. literalinclude:: ../../tests/conftest.py
    :start-after: setup nova connection
    :end-before: setup nova connection complete
    :dedent:

.. literalinclude:: ../../tests/test_data_store.py
    :start-after: create new datastore
    :end-before: create new datastore complete
    :dedent:

By default data stores are persisted, meaning that their jobs and outputs will be available to retrieve even after the connection is closed.
Datastores (or data stores) also keep their namespace even after the application is exited. Meaning, if you name your data store "Data1", then
if you create a new data store in the future named "Data1" then Nova Galaxy will automatically connect the new instance to the old one, assuming
it has not been deleted.

In order to delete and cleanup your data stores (ie delete all outputs/resources associated with the data store), there are a few methods.

First you can mark a data store for cleanup automatically when you close your nova connection.

.. literalinclude:: ../../tests/test_data_store.py
    :start-after: create new datastore
    :end-before: mark for cleanup complete
    :dedent:

When the 'with' block exits, the data store will be cleaned up. This will also work when the connection class is used without the 'with' syntax.

.. literalinclude:: ../../tests/test_data_store.py
    :start-after: manual connection start
    :end-before: manual connection complete
    :dedent:

When the `connection.close()` method is called, the data store will be cleaned up. You can also manually clean a data store by invoking the cleanup class method: `cleanup()`.


In order to use the data store again after it's been clean up, you will have to call create_data_store again. If at any point, you want to persist a store that has been marked for cleanup, you can call the `persist()` class method.
