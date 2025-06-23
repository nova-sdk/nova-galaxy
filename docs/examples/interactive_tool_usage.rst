.. _interactive_tool_usage:

Example 4: Using an Interactive Tool
-------------------------------------

This example demonstrates how to run an interactive tool and retrieve its URL.

.. code-block:: python

   from nova.galaxy import Nova, Dataset, Tool, Parameters

   galaxy_url = "your_galaxy_url"
   galaxy_key = "your_galaxy_api_key"
   nova = Connection(galaxy_url, galaxy_key)

   with nova.connect() as conn:
       data_store = conn.create_data_store("Interactive Tool Example")
       data_store.mark_for_cleanup()
       # Create and upload a dataset if needed
       # my_dataset = Dataset("path/to/your/file.txt")
       # my_dataset.upload(data_store)

       # Define parameters
       params = Parameters()
       # params.add_input("input", my_dataset)

       # Get the interactive tool
       interactive_tool = Tool("interactive_tool_id") # Replace with your interactive tool ID

       # Run the tool interactively
       try:
           url = interactive_tool.run_interactive(data_store, params)
           print(f"Access the interactive tool at: {url}")
       except Exception as e:
           print(f"Error running interactive tool: {e}")

       # Fetch the url again
       url = interactive_tool.get_url()
