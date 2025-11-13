.. _workflows:

Workflows
=========

The ``nova-galaxy`` library provides a ``Workflow`` class to interact with and run Galaxy workflows. This allows you to programmatically execute complex bioinformatic pipelines defined in Galaxy.

Key Concepts
------------

*   **Workflow ID**: Each workflow in Galaxy has a unique ID. You'll need this ID to instantiate a ``Workflow`` object. You can typically find this ID through the Galaxy UI or API (e.g., using ``galaxy_instance.workflows.get_workflows()``).
*   **Datastore**: Workflows are run within a specific Galaxy history, which is represented by a :ref:`Datastore <datastores>` object in ``nova-galaxy``.
*   **Parameters**: Workflows often require input datasets and various parameters to control their execution. These are provided via a :ref:`Parameters <parameters>` object.
*   **Invocation**: Each run of a workflow is called an "invocation". The library manages the state and results of these invocations.
*   **Outputs**: Upon successful completion, a workflow produces output datasets, which can be accessed via an :ref:`Outputs <outputs>` object.

Using the ``Workflow`` Class
----------------------------

The primary class for interacting with workflows is ``nova.galaxy.workflow.Workflow``.

Initializing a Workflow
~~~~~~~~~~~~~~~~~~~~~~~

To start, you need the ID of the Galaxy workflow you want to run.

.. code-block:: python

    from nova.galaxy.workflow import Workflow

    # Replace 'your_workflow_id' with the actual ID from Galaxy
    workflow_id = "your_workflow_id"
    my_workflow = Workflow(id=workflow_id)

Running a Workflow
~~~~~~~~~~~~~~~~~~

To run the workflow, you use the ``run()`` method. This method requires a ``Datastore`` (representing the Galaxy history) and optionally a ``WorkflowParameters`` object for inputs and step-specific parameters.

.. code-block:: python

    from nova.galaxy.data_store import Datastore
    from nova.galaxy.parameters import WorkflowParameters
    from nova.galaxy.dataset import Dataset, DatasetCollection

    # Assume 'galaxy_connection' is an established Connection object
    # Assume 'history_id' is the ID of the target Galaxy history
    data_store = Datastore(galaxy_connection, history_id=history_id)

    # Prepare workflow parameters
    workflow_params = WorkflowParameters()

    # Example 1: Providing a dataset as a workflow-level input
    # '0' is the input ID of the workflow (as defined in Galaxy)
    # 'your_input_dataset_id' is the Galaxy ID of an existing dataset in the history.
    input_dataset = Dataset(id="your_input_dataset_id")
    workflow_params.add_workflow_input("0", input_dataset)

    # Example 2: Providing a dataset collection as a workflow-level input
    # '1' is another input ID of the workflow
    input_collection = DatasetCollection(id="your_input_collection_id")
    workflow_params.add_workflow_input("1", input_collection)

    # Example 3: Setting a parameter for a specific step within the workflow
    # '2' is the ID of the workflow step (as defined in Galaxy)
    # 'some_tool_param' is the parameter path within that step
    workflow_params.add_step_param("2", "some_tool_param", "some_value")

    # Example 4: Setting a list of datasets for a parameter in a step
    list_of_datasets = [Dataset(id="ds_id_1"), Dataset(id="ds_id_2")]
    workflow_params.add_step_param("3", "multiple_inputs", list_of_datasets)

    # Run the workflow and wait for completion (default behavior)
    try:
        outputs = my_workflow.run(data_store=data_store, params=workflow_params, wait=True)
        if outputs:
            print("Workflow completed successfully!")
    except Exception as e:
        print(f"Workflow execution failed: {e}")

Non-Blocking Execution
^^^^^^^^^^^^^^^^^^^^^^

If you don't want to wait for the workflow to complete, set ``wait=False``.

.. code-block:: python

    my_workflow.run(data_store=data_store, params=params, wait=False)
    print(f"Workflow started with invocation ID: {my_workflow.get_invocation_id()}")
    # You'll need to check the status periodically

Checking Workflow Status
~~~~~~~~~~~~~~~~~~~~~~~~

You can check the status of the last workflow invocation using ``get_status()`` or ``get_full_status()``.

.. code-block:: python

    from nova.common.job import WorkState

    status = my_workflow.get_status()
    print(f"Current workflow status: {status}")

    if status == WorkState.RUNNING:
        print("Workflow is still running.")
    elif status == WorkState.FINISHED:
        print("Workflow finished successfully.")
    elif status == WorkState.ERROR:
        full_status = my_workflow.get_full_status()
        print(f"Workflow failed. Details: {full_status.details if full_status else 'N/A'}")

The ``get_status()`` method returns a ``WorkState`` enum member (e.g., ``WorkState.QUEUED``, ``WorkState.RUNNING``, ``WorkState.FINISHED``, ``WorkState.ERROR``).

The ``get_full_status()`` method returns an ``InvocationStatus`` object which contains both the ``state`` and a ``details`` string (useful for error messages).

Getting Workflow Results
~~~~~~~~~~~~~~~~~~~~~~~~

Once a workflow has completed successfully (``get_status() == WorkState.FINISHED``), you can retrieve its outputs using ``get_results()``.

.. code-block:: python

    if my_workflow.get_status() == WorkState.FINISHED:
        outputs = my_workflow.get_results()
        if outputs:
            for output_name, dataset_or_collection in outputs.items():
                print(f"Output '{output_name}': ID {dataset_or_collection.id}")
        else:
            print("No outputs found, or an issue retrieving them.")

The ``get_results()`` method returns an ``Outputs`` object, which is a dictionary-like structure mapping output names (as defined in the workflow) to ``Dataset`` or ``DatasetCollection`` objects.

Cancelling a Workflow
~~~~~~~~~~~~~~~~~~~~~

If a workflow is running, you can attempt to cancel it using ``cancel()`` or its alias ``stop()``.

.. code-block:: python

    if my_workflow.get_status() == WorkState.RUNNING:
        was_cancelled = my_workflow.cancel()
        if was_cancelled:
            print("Workflow cancellation requested.")
        else:
            print("Failed to request workflow cancellation.")

Getting Invocation ID
~~~~~~~~~~~~~~~~~~~~~

Each workflow run (invocation) has a unique ID in Galaxy. You can retrieve this ID:

.. code-block:: python

    invocation_id = my_workflow.get_invocation_id()
    if invocation_id:
        print(f"Galaxy Invocation ID: {invocation_id}")

Accessing Step-Level Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~

Workflows are composed of individual tool executions. You can access these as ``Tool`` objects using ``get_step_jobs()``. This is useful for monitoring progress at a finer grain or retrieving logs from specific steps.

.. code-block:: python

    from nova.galaxy.tool import Tool

    step_tools: List[Tool] = my_workflow.get_step_jobs()
    for tool in step_tools:
        print(f"Step Tool ID: {tool.id}, Status: {tool.get_status()}")
        if tool.get_status() == WorkState.ERROR:
            full_tool_status = tool.get_full_status()
            print(f"  Tool Error Details: {full_tool_status.details if full_tool_status else 'N/A'}")


Important Notes
---------------

*   **Workflow Definition**: The structure of your ``WorkflowParameters`` object (workflow input IDs, step IDs, and parameter paths) must match how the workflow is defined in Galaxy. Use the Galaxy UI or API to inspect your workflow's inputs and step details.
*   **Dataset IDs**: When providing ``Dataset`` or ``DatasetCollection`` objects as inputs, they must already exist in the Galaxy history and have their ``id`` attribute populated.
*   **Error Handling**: Always wrap ``run()`` calls (especially with ``wait=True``) in try-except blocks to handle potential exceptions during workflow execution. Check ``get_full_status().details`` for more information on errors.
*   **State Management**: The ``Workflow`` object primarily manages the state of its *last* invocation. If you need to manage multiple concurrent runs of the same workflow definition, instantiate a new ``Workflow`` object for each run.

This guide provides an overview of using the ``Workflow`` class. For more detailed information on specific classes like ``Datastore``, ``Parameters``, ``Dataset``, and ``Outputs``, please refer to their respective documentation pages.
