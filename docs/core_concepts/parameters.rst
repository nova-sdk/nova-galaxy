.. _parameters:

Parameters
-------------------------

The `Parameters` class is used to define the input parameters for a Galaxy tool.

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: run interactive tool
    :end-before: run interactive tool complete
    :dedent:

You can remove an existing input value with `remove_input()` or change the value with `change_input_value()`.
