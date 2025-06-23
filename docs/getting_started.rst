.. _getting_started:

Getting Started
===============

To begin using nova-galaxy, you need to initialize a `Nova` instance with your Galaxy server's URL and API key. Then, establish a connection using a context manager.

.. code-block:: python

   from nova.galaxy import Nova

   # Initialize Nova with your Galaxy server URL and API key
   galaxy_url = "your_galaxy_url"
   galaxy_key = "your_galaxy_api_key"
   nova = Connection(galaxy_url, galaxy_key)

   # Connect to Galaxy and perform operations within the 'with' block
   with nova.connect() as conn:
       # Create a data store (history)
       data_store = conn.create_data_store("My Data Store")

       # Now you can upload data, run tools, etc.
       # ...

.. note::

   Ensure that your Galaxy server is accessible and that you have a valid API key.
