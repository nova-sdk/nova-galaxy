.. _tools:

Tools
--------------

The `Tool` class represents a Galaxy tool. You can run tools, manage their inputs, and retrieve their outputs using nova-galaxy.

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: basic run tool example
    :end-before: basic run tool example complete
    :dedent:


By default tools will run synchronously. In order to run a tool in an "async" manner, set the wait argument to False.

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: async run example
    :end-before: async run example complete
    :dedent:

Any code after will be executed immediately. Outputs will be None in this case.

You can get the status of the tool in the form of a WorkState (from nova-common library) enum value:

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: get status example
    :end-before: get status example complete
    :dedent:


If a tool has already been run, and you want to get the results/outputs again:

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: get results example
    :end-before: get results example complete
    :dedent:

If you have run a tool asynchronously, and at a later point, you want to wait for the tool, you can use the `wait_for_results()` method:

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: async run example
    :end-before: get results example complete
    :dedent:

If you want to stop a tool from running, but keep any existing outputs from the Tool, use the `stop()` method.
If you want to cancel a tool from running and throw away any output from it, use the `cancel()` method.

You can get any current stdout and stderr from a Tool with the flexibility of choosing starting position and how many characters you want:

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: get stdout example
    :end-before: get stdout example complete
    :dedent:

These methods work regardless of whether the job is running or has been completed.

Advanced users may find they need to access the underlying job id for a tool, which they can do so with `get_uid()`.
Tools can also be assigned to already running or completed jobs by using `assign_id()`
