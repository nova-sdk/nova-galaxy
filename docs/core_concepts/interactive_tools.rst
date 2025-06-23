.. _interactive_tools:

Interactive Tools
-----------------

nova-galaxy allows running Galaxy tools in interactive mode, which is especially useful when tools generate URLs that need to be accessed during runtime.

.. code-block:: python

    from nova.galaxy import Tool, Parameters

    # Define tool parameters
    params = Parameters()

    # Get a tool instance
    my_tool = Tool("tool_id") # Replace with your tool id from Galaxy

    # Run the tool in interactive mode
    url = my_tool.run_interactive(data_store, params)
    print(f"Interactive tool URL: {url}")

By default, interactive tools are not stopped automatically once the Nova connection is closed. To override this behavior, use the DataStore mark_for_cleanup method. This will cause the tool to stop automatically, once the connection is closed (or `with` block is exited). You can manually stop these tools by using the Tool stop_all_tools_in_store method.

If you want to get the url of an interactive tool at a later point, you can use the `get_url` method:

.. code-block:: python

     my_tool.get_url()
