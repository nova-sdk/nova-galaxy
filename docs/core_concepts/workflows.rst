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

To run the workflow, you use the ``run()`` method. This method requires a ``Datastore`` (representing the Galaxy history) and optionally a ``Parameters`` object for inputs.

.. code-block:: python

    from nova.galaxy.data_store import Datastore
    from nova.galaxy.parameters import Parameters
    from nova.galaxy.dataset import Dataset # Assuming you have an input dataset

    # Assume 'galaxy_connection' is an established Connection object
    # Assume 'history_id' is the ID of the target Galaxy history
    data_store = Datastore(galaxy_connection, history_id=history_id)

    # Prepare parameters (if any)
    params = Parameters()
    # Example: Adding an input dataset. 'input_dataset_label' is the label
    # of the workflow input as defined in Galaxy.
    # 'input_ds_id' is the Galaxy ID of an existing dataset in the history.
    input_dataset = Dataset(name="My Input Data", id="input_ds_id")
    input_dataset.store = data_store # Associate dataset with the datastore
    params.add_input("input_dataset_label", input_dataset)

    # Example: Setting a tool parameter within the workflow.
    # 'workflow_step_label' is the label of the step in Galaxy.
    # 'parameter_name' is the name of the parameter for that tool.
    params.add_parameter("workflow_step_label", {"parameter_name": "parameter_value"})


    # Run the workflow and wait for completion (default behavior)
    try:
        outputs = my_workflow.run(data_store=data_store, params=params, wait=True)
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

Accessing Step-Level Jobs
~~~~~~~~~~~~~~~~~~~~~~~~~

Workflows are composed of individual tool executions (jobs). You can access these as ``Job`` objects using ``get_step_jobs()``. This is useful for monitoring progress at a finer grain or retrieving logs from specific steps.

.. code-block:: python

    from nova.galaxy.job import Job

    step_jobs: List[Job] = my_workflow.get_step_jobs()
    for job in step_jobs:
        print(f"Step Tool ID: {job.tool_id}, Status: {job.get_status()}")
        if job.get_status() == WorkState.ERROR:
            full_job_status = job.get_full_status()
            print(f"  Job Error Details: {full_job_status.details if full_job_status else 'N/A'}")


Important Notes
---------------

*   **Workflow Definition**: The structure of your ``Parameters`` object (input labels, step labels for parameters) must match how the workflow is defined in Galaxy. Use the Galaxy UI or API to inspect your workflow's inputs and step details.
*   **Dataset IDs**: When providing ``Dataset`` or ``DatasetCollection`` objects as inputs, they must already exist in the Galaxy history and have their ``id`` attribute populated.
*   **Error Handling**: Always wrap ``run()`` calls (especially with ``wait=True``) in try-except blocks to handle potential exceptions during workflow execution. Check ``get_full_status().details`` for more information on errors.
*   **State Management**: The ``Workflow`` object primarily manages the state of its *last* invocation. If you need to manage multiple concurrent runs of the same workflow definition, instantiate a new ``Workflow`` object for each run.

This guide provides an overview of using the ``Workflow`` class. For more detailed information on specific classes like ``Datastore``, ``Parameters``, ``Dataset``, and ``Outputs``, please refer to their respective documentation pages.