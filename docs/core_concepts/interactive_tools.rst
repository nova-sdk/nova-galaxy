.. _interactive_tools:

Interactive Tools
-----------------

nova-galaxy allows running Galaxy tools in interactive mode, which is especially useful when tools generate URLs that need to be accessed during runtime.

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: run interactive tool
    :end-before: run interactive tool complete
    :dedent:

By default, interactive tools are not stopped automatically once the Nova connection is closed. To override this behavior, use the DataStore mark_for_cleanup method. This will cause the tool to stop automatically, once the connection is closed (or `with` block is exited). You can manually stop these tools by using the Tool stop_all_tools_in_store method.

If you want to get the url of an interactive tool at a later point, you can use the `get_url` method:

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: interactive tool get link
    :end-before: interactive tool get link complete
    :dedent:
