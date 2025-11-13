.. _parameters:

Parameters
-------------------------

The `Parameters` class is used to define the input parameters for a Galaxy tool.

.. literalinclude:: ../../tests/test_run_tool.py
    :start-after: run interactive tool
    :end-before: run interactive tool complete
    :dedent:

You can remove an existing input value with `remove_input()` or change the value with `change_input_value()`.

Workflow Parameters
-------------------

The `WorkflowParameters` class is specifically designed for passing inputs and parameters to Galaxy workflows. It provides a more explicit, bioblend-style approach to define workflow-level inputs and parameters for individual steps within a workflow.

**Workflow-level Inputs (`add_workflow_input`)**

Use `add_workflow_input` to provide values for the overall workflow inputs, which are typically identified by numerical IDs (e.g., "0", "1") as defined in the workflow. These can be datasets, dataset collections, or simple values.

.. code-block:: python

    from nova.galaxy.parameters import WorkflowParameters
    from nova.galaxy.dataset import Dataset, DatasetCollection

    workflow_params = WorkflowParameters()

    # Adding a dataset as a workflow input (input ID "0")
    my_dataset = Dataset(id="your_dataset_id")
    workflow_params.add_workflow_input("0", my_dataset)

    # Adding a dataset collection as a workflow input (input ID "1")
    my_collection = DatasetCollection(id="your_collection_id")
    workflow_params.add_workflow_input("1", my_collection)

    # Adding a simple text value as a workflow input (input ID "2")
    workflow_params.add_workflow_input("2", "my_text_input")

**Step-level Parameters (`add_step_param`)**

Use `add_step_param` to set parameters for specific steps within the workflow. These are identified by the step's ID (e.g., "2", "4") and a parameter path (e.g., "input", "series_0|input_mode|export_folder").

.. code-block:: python

    from nova.galaxy.parameters import WorkflowParameters
    from nova.galaxy.dataset import Dataset

    workflow_params = WorkflowParameters()

    # Setting a parameter for step "2" with parameter path "input"
    # This could be a dataset, dataset collection, or simple value
    input_for_step_2 = Dataset(id="another_dataset_id")
    workflow_params.add_step_param("2", "input", input_for_step_2)

    # Setting a text parameter for step "3" with parameter path "some_option"
    workflow_params.add_step_param("3", "some_option", "value_for_option")

    # Setting a list of datasets for a parameter in step "4"
    list_of_datasets = [Dataset(id="ds1"), Dataset(id="ds2")]
    workflow_params.add_step_param("4", "multiple_inputs", list_of_datasets)

When running a workflow, you pass an instance of `WorkflowParameters` to the `Workflow.run()` method.
