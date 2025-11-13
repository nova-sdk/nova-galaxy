"""Integration tests for Workflow functionality."""

import os

from nova.common.job import WorkState

from nova.galaxy.connection import Connection
from nova.galaxy.parameters import WorkflowParameters
from nova.galaxy.workflow import Workflow

GALAXY_URL = os.environ.get("NOVA_GALAXY_TEST_GALAXY_URL", "https://calvera-test.ornl.gov")
GALAXY_API_KEY = os.environ.get("NOVA_GALAXY_TEST_GALAXY_KEY", "")


TEST_HISTORY_NAME_WF = "nova_galaxy_workflow_test_history"


def test_workflow_lifecycle_with_placeholder_id(nova_instance: Connection) -> None:
    """
    Tests the Workflow class lifecycle methods when using a placeholder workflow ID.

    This test expects failures when trying to run the workflow, as the ID is a placeholder.
    """
    with nova_instance.connect() as connection:
        ds = connection.get_data_store(name=TEST_HISTORY_NAME_WF)
        workflow = Workflow(id="placeholder_id")

        outputs = workflow.run(data_store=ds, wait=False)
        assert outputs is None

        status = workflow.get_status()
        invocation_id = workflow.get_invocation_id()
        full_status = workflow.get_full_status()

        print(f"Status after run(wait=True): {status}")
        print(f"Invocation ID after run(wait=True): {invocation_id}")
        print(f"Full status details: {full_status.details if full_status else 'N/A'}")

        assert status in [
            WorkState.ERROR,
            WorkState.QUEUED,
        ], f"Expected ERROR or QUEUED state after run(wait=False), got {status}"

        if status == WorkState.ERROR:
            assert full_status is not None
            assert full_status.state == WorkState.ERROR
            assert full_status.details is not None and full_status.details != ""

        results = workflow.get_results()
        assert results is None, f"Expected no results for a failed/incomplete workflow, got {results}"

        cancel_result = workflow.cancel()
        print(f"Cancel result: {cancel_result}")
        if invocation_id:
            pass
        else:
            assert not cancel_result, "Cancel should return False if no invocation ID was set"

        step_jobs = workflow.get_step_jobs()
        assert isinstance(step_jobs, list)
        assert len(step_jobs) == 0, "Expected no step jobs for a placeholder/failed workflow"

        final_status = workflow.get_status()
        assert final_status in [
            WorkState.ERROR,
            WorkState.CANCELED,
            WorkState.QUEUED,
        ], f"Unexpected final state: {final_status}"


def test_simple_test_workflow_with_dataset(nova_instance: Connection) -> None:
    """Tests running the 'simple_test_workflow_with_dataset' workflow with specific inputs and parameters."""
    with nova_instance.connect() as connection:
        ds = connection.get_data_store(name=TEST_HISTORY_NAME_WF)
        workflows = connection.galaxy_instance.workflows.get_workflows(
            name="simple_test_workflow_with_dataset", published=True
        )

        assert len(workflows) > 0, (
            "'simple_test_workflow_with_dataset' not found. Please ensure it's published in Galaxy."
        )

        workflow_id = workflows[0]["id"]
        params = WorkflowParameters()

        # Set workflow input 0 to True
        params.add_workflow_input("0", True)

        # Set parameter for step 1
        params.add_step_param("1", "params|ingest_mode", "file")
        params.add_step_param("1", "params|filepath", "/SNS/TOPAZ/IPTS-17211/0/22594/NeXus/TOPAZ_22594_event.nxs")

        workflow = Workflow(id=workflow_id)

        workflow.run(data_store=ds, params=params, wait=True)

        # Assertions for successful completion
        assert workflow.get_status() == WorkState.FINISHED, (
            f"Workflow did not finish successfully. Current status: {workflow.get_status()}"
        )


def test_workflow_initial_state() -> None:
    """Tests the initial state of a Workflow object before any run."""
    workflow = Workflow(id="another_placeholder_id")
    assert workflow.id == "another_placeholder_id"
    assert workflow.get_status() == WorkState.NOT_STARTED
    assert workflow.get_invocation_id() is None
    assert workflow.get_results() is None
    assert workflow.get_full_status() is None
    assert not workflow.cancel()
    assert workflow.get_step_jobs() == []
