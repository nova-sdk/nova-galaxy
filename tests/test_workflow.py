"""Integration tests for Workflow functionality."""

import os
import time

import pytest

from nova.common.job import WorkState
from nova.galaxy.connection import Connection
from nova.galaxy.data_store import Datastore
from nova.galaxy.parameters import Parameters
from nova.galaxy.workflow import Workflow

GALAXY_URL = os.environ.get("NOVA_GALAXY_TEST_GALAXY_URL", "https://calvera-test.ornl.gov")
GALAXY_API_KEY = os.environ.get("NOVA_GALAXY_TEST_GALAXY_KEY", "")


PLACEHOLDER_WORKFLOW_ID = "test_workflow_id_for_nova_galaxy_placeholder"
TEST_HISTORY_NAME_WF = "nova_galaxy_workflow_test_history"


@pytest.fixture(scope="module")
def nova_galaxy_connection() -> Connection:
    """Provides a Connection instance for the tests."""
    if not GALAXY_API_KEY:
        pytest.skip("NOVA_GALAXY_TEST_GALAXY_KEY is not set. Skipping integration tests.")
    conn = Connection(galaxy_url=GALAXY_URL, api_key=GALAXY_API_KEY)
    return conn

@pytest.fixture
def test_datastore(nova_galaxy_connection: Connection) -> Datastore:
    """Creates a new history for testing and yields the Datastore."""
    ds = nova_galaxy_connection.create_data_store(name=TEST_HISTORY_NAME_WF)
    yield ds
    try:
        if not ds.history_id:
            histories = nova_galaxy_connection.galaxy_instance.histories.get_histories(name=TEST_HISTORY_NAME_WF)
            if histories:
                ds.history_id = histories[0]['id']
        
        if ds.history_id:
            nova_galaxy_connection.galaxy_instance.histories.delete_history(ds.history_id, purge=True)
            print(f"Cleaned up history: {TEST_HISTORY_NAME_WF} (ID: {ds.history_id})")
    except Exception as e:
        print(f"Error during history cleanup: {e}")


@pytest.mark.integration
def test_workflow_lifecycle_with_placeholder_id(
    nova_galaxy_connection: Connection, test_datastore: Datastore
):
    """
    Tests the Workflow class lifecycle methods when using a placeholder workflow ID.
    This test expects failures when trying to run the workflow, as the ID is a placeholder.
    """
    workflow = Workflow(id=PLACEHOLDER_WORKFLOW_ID)
    params = Parameters()

    assert workflow.id == PLACEHOLDER_WORKFLOW_ID
    assert workflow.get_status() == WorkState.NOT_STARTED
    assert workflow.get_invocation_id() is None

    with pytest.raises(Exception) as excinfo_run_wait:
        workflow.run(data_store=test_datastore, params=params, wait=True)
    
    print(f"Exception from run(wait=True): {excinfo_run_wait.value}")

    assert workflow.get_status() == WorkState.ERROR, \
        f"Expected ERROR state after failed run, got {workflow.get_status()}"
    
    full_status_after_fail_wait = workflow.get_full_status()
    assert full_status_after_fail_wait is not None
    assert full_status_after_fail_wait.state == WorkState.ERROR
    assert full_status_after_fail_wait.details is not None and full_status_after_fail_wait.details != ""

    workflow = Workflow(id=PLACEHOLDER_WORKFLOW_ID)

    outputs_no_wait = workflow.run(data_store=test_datastore, params=params, wait=False)
    assert outputs_no_wait is None

    time.sleep(2)

    status_no_wait = workflow.get_status()
    invocation_id_no_wait = workflow.get_invocation_id()
    full_status_no_wait = workflow.get_full_status()

    print(f"Status after run(wait=False): {status_no_wait}")
    print(f"Invocation ID after run(wait=False): {invocation_id_no_wait}")
    print(f"Full status details: {full_status_no_wait.details if full_status_no_wait else 'N/A'}")

    assert status_no_wait in [WorkState.ERROR, WorkState.QUEUED], \
        f"Expected ERROR or QUEUED state after run(wait=False), got {status_no_wait}"

    if status_no_wait == WorkState.ERROR:
        assert full_status_no_wait is not None
        assert full_status_no_wait.state == WorkState.ERROR
        assert full_status_no_wait.details is not None and full_status_no_wait.details != ""
    
    results = workflow.get_results()
    assert results is None, f"Expected no results for a failed/incomplete workflow, got {results}"

    cancel_result = workflow.cancel()
    print(f"Cancel result: {cancel_result}")
    if invocation_id_no_wait:
        pass
    else:
        assert not cancel_result, "Cancel should return False if no invocation ID was set"


    step_jobs = workflow.get_step_jobs()
    assert isinstance(step_jobs, list)
    assert len(step_jobs) == 0, "Expected no step jobs for a placeholder/failed workflow"

    final_status = workflow.get_status()
    assert final_status in [WorkState.ERROR, WorkState.CANCELED, WorkState.QUEUED], \
         f"Unexpected final state: {final_status}"

@pytest.mark.integration
def test_workflow_initial_state():
    """Tests the initial state of a Workflow object before any run."""
    workflow = Workflow(id="another_placeholder_id")
    assert workflow.id == "another_placeholder_id"
    assert workflow.get_status() == WorkState.NOT_STARTED
    assert workflow.get_invocation_id() is None
    assert workflow.get_results() is None
    assert workflow.get_full_status() is None
    assert not workflow.cancel()
    assert workflow.get_step_jobs() == []