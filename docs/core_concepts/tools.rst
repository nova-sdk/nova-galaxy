.. _tools:

Tools
--------------

The `Tool` class represents a Galaxy tool. You can run tools, manage their inputs, and retrieve their outputs using nova-galaxy.

.. code-block:: python

   from nova.galaxy import Connection, Tool, Parameters, Dataset

   # Get a tool instance
   my_tool = Tool("tool_id")

   connection = Connection("galaxy_url", "galaxy_key")
   active_connection = connection.connect()
   data_store = active_connection.create_data_store("cool store")
   inputs = Parameters()
   # Run the tool
   outputs = my_tool.run(data_store, inputs)

By default tools will run synchronously. In order to run a tool in an "async" manner, set the wait argument to False.

.. code-block:: python

    outputs = my_tool.run(data_store=data_store, params=inputs, wait=False)
    # any code after will be executed immediately. Outputs will be None in this case.

You can get the status of the tool in the form of a WorkState (from nova-common library) enum value:

.. code-block:: python

    status = my_tool.get_status()
    print(status) # could print "running", "queued", "error", etc
    full status = my_tool.get_full_status()
    print(full_status) # Gives you details on error states, etc

If a tool has already been run, and you want to get the results/outputs again:

.. code-block:: python

    outputs = my_tool.get_results()

If you have run a tool asynchronously, and at a later point, you want to wait for the tool, you can use the `wait_for_results` method:

.. code-block:: python

    my_tool.run(data_store=data_store, params=inputs, wait=False)

    # do some stuff

    my_tool.wait_for_results()
    # Any code after will be executed after tool has finished running

If you want to stop a tool from running, but keep any existing outputs from the Tool, use the `stop` method.

.. code-block:: python

    my_tool.run(data_store=data_store, params=inputs, wait=False)
    my_tool.stop()
    outputs = my_tool.get_results()

If you want to cancel a tool from running and throw away any output from it, use the `cancel` method:

.. code-block:: python

    my_tool.run(data_store=data_store, params=inputs, wait=False)
    my_tool.cancel()

You can get any current stdout and stderr from a Tool:

.. code-block:: python

    stdout = my_tool.get_stdout() # Get current stdout
    stderr = my_tool.get_stderr(position=10, length = 300) # Gets 300 characters of stderr, starting from the tenth index.
    # Both stdout and stderr amount and starting position can be specified.

These methods work regardless of whether the job is running or has been completed.

Advanced users may find they need to access the underlying job id for a tool, which they can do so with `get_uid`

.. code-block:: python

    upstream_id = my_tool.get_uid() # Galaxy job ID

Tools can also be assigned to already running or completed jobs by using `assign_id`

.. code-block:: python

    second_tool = Tool("tool_id")
    second_tool.assign_id(upstream_id)
    # second_tool now can access status, outputs, stdout, stderr, etc from first tool
