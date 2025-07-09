.. _tool_runner:

Tool Runner
--------------

The `ToolRunner` is a helper class to run Galaxy tools using Blinker signals. This allows connect to connect
Galaxy with GUI in a decoupled way.

.. literalinclude:: ../../tests/test_tool_runner.py
    :start-after: tool runner example start
    :end-before: tool runner example start complete
    :dedent:

The ToolRunner needs a Tool class which it will manage. This class should inherit from the `BasicTool` and define
functions specific to the tool. For example:

.. literalinclude:: ../../tests/test_tool_runner.py
    :start-after: BasicTool example
    :end-before: BasicTool example complete
    :dedent:
