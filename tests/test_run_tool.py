"""Tests for tools."""

import time

from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.datasets import DatasetClient
from nova.common.job import WorkState

from nova.galaxy.connection import Connection
from nova.galaxy.dataset import Dataset
from nova.galaxy.parameters import Parameters
from nova.galaxy.tool import Tool

TEST_TOOL_ID = "neutrons_remote_command"
TEST_INT_TOOL_ID = "interactive_tool_jupyter_notebook"
# If test fails, these files may be moved or no longer exists.
REMOTE_FILE_PATH = "/HFIR/CG3/shared/Cycle509/IntermediateConfigNiQ_RC509.txt"
REMOTE_FILE_PATH_2 = "/HFIR/CG3/shared/Cycle509/Long6AConfigURBj_RC509.txt"


def test_run_tool(nova_instance: Connection) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        test_tool = Tool(TEST_TOOL_ID)
        # [outputs example]
        outputs = test_tool.run(data_store=store, params=Parameters())
        assert outputs is not None
        data = outputs.get_dataset("output1")
        # [outputs example complete]
        assert "hostname:" in data.get_content().decode("utf-8")


def test_run_tool_interactive(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        # [run interactive tool]
        notebook = Dataset(path="tests/test_files/test_jupyter_notebook.ipynb")
        test_tool = Tool(TEST_INT_TOOL_ID)
        params = Parameters()
        params.add_input("mode|mode_select", "previous")
        params.add_input("ipynb", notebook)
        params.add_input("run_it", True)
        link = test_tool.run_interactive(data_store=store, params=params, check_url=False)
        # [run interactive tool complete]
        assert link is not None
        # [interactive tool get link]
        assert test_tool.get_url() is not None
        # [interactive tool get link complete]
        entry_points = galaxy_instance.make_get_request(
            f"{store.nova_connection.galaxy_url}/api/entry_points?running=true"
        )
        for ep in entry_points.json():
            if ep.get("target", None):
                if link == f"{store.nova_connection.galaxy_url}{ep['target']}":
                    galaxy_instance.jobs.wait_for_job(job_id=ep["job_id"])
                    outputs = galaxy_instance.jobs.get_outputs(ep["job_id"])
                    test_output = None
                    for out in outputs:
                        if out.get("name", None) == "output_single":
                            test_output = out["dataset"]["id"]
                    assert test_output is not None
                    dataset_client = DatasetClient(store.nova_connection.galaxy_instance)
                    test_text = dataset_client.download_dataset(
                        test_output, use_default_filename=False, file_path=None
                    ).decode("utf-8")
                    assert test_text == "this is a test"
                    return
        raise Exception("Did not find interactive tool while testing.")


def test_status(nova_instance: Connection) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        # store.mark_for_cleanup()
        test_tool = Tool(TEST_INT_TOOL_ID)
        params = Parameters()
        state = test_tool.get_status()
        assert state == WorkState.NOT_STARTED
        test_tool.run_interactive(data_store=store, params=params, check_url=False)
        time.sleep(4)
        state = test_tool.get_status()
        assert state == WorkState.RUNNING
        test_tool.stop()
        state = test_tool.get_status()
        assert state == WorkState.STOPPING
        test_tool.wait_for_results()
        state = test_tool.get_status()
        assert state == WorkState.FINISHED


def test_full_status(nova_instance: Connection) -> None:
    # [basic run tool example]
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        test_tool = Tool(TEST_TOOL_ID)
        params = Parameters()
        params.add_input("command_mode|command", "fail")
        test_tool.run(data_store=store, params=params)
        # [basic run tool example complete]
        # [get status example]
        assert test_tool.get_status() == WorkState.ERROR
        assert test_tool.get_full_status().details != ""
        # [get status example complete]
        assert test_tool.get_stderr() != ""


def test_cancel_tool(nova_instance: Connection) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        test_tool = Tool(TEST_INT_TOOL_ID)
        params = Parameters()
        test_tool.run_interactive(data_store=store, params=params, check_url=False)
        test_tool.cancel()
        state = test_tool.get_status()
        assert state == WorkState.CANCELING


def test_cancel_tool_while_uploading(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        notebook = Dataset(path="tests/test_files/test_jupyter_notebook.ipynb")
        notebook2 = Dataset(path="tests/test_files/test_jupyter_notebook.ipynb")
        test_tool = Tool(TEST_INT_TOOL_ID)
        params = Parameters()
        params.add_input("mode|mode_select", "previous")
        params.add_input("ipynb", notebook)
        # Tool doesn't have this parameter, but since we're canceling in the upload stage, should still be fine to test.
        params.add_input("extra_notebook", notebook2)
        params.add_input("run_it", True)
        test_tool.run(data_store=store, params=params, wait=False)
        time.sleep(2)
        state = test_tool.get_status()
        assert state == WorkState.UPLOADING_DATA
        test_tool.cancel()
        state = test_tool.get_status()
        assert state == WorkState.CANCELING
        test_tool.wait_for_results()
        state = test_tool.get_status()
        assert state == WorkState.CANCELED
        history_id = galaxy_instance.histories.get_histories(name="nova_galaxy_testing")[0]["id"]
        history_details = galaxy_instance.histories.get_status(history_id=history_id)
        assert history_details["percent_complete"] == 0


def test_get_tool_stdout(nova_instance: Connection) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        test_tool = Tool(TEST_INT_TOOL_ID)
        params = Parameters()
        test_tool.run_interactive(data_store=store, params=params, check_url=False)
        state = test_tool.get_status()
        assert state == WorkState.RUNNING
        time.sleep(10)  # Tool takes a moment to produce stdout
        # [get stdout example]
        stdout = test_tool.get_stdout()
        stdout_substring = test_tool.get_stdout(5, 50)
        # [get stdout example complete]
        assert stdout is not None
        assert stdout_substring is not None
        assert stdout_substring in stdout
        test_tool.cancel()


def test_run_tool_independent_data_store(nova_instance: Connection) -> None:
    connection = nova_instance.connect()
    store = connection.get_data_store(name="nova_galaxy_testing")
    store.mark_for_cleanup()
    test_tool = Tool(TEST_TOOL_ID)
    outputs = test_tool.run(data_store=store, params=Parameters())
    assert outputs is not None
    connection.close()


def test_wait_for_results(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    connection = nova_instance.connect()
    store = connection.get_data_store(name="nova_galaxy_testing")
    store.mark_for_cleanup()
    test_tool = Tool(TEST_TOOL_ID)
    # [async run example]
    outputs = test_tool.run(data_store=store, params=Parameters(), wait=False)
    # [async run example complete]
    assert outputs is None
    assert test_tool.get_uid() is not None
    test_tool.wait_for_results()
    # [get results example]
    results = test_tool.get_results()
    # [get results example complete]
    assert results is not None
    connection.close()


def test_existing_dataset_as_parameter(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    # [existing dataset input]
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        test_tool = Tool(TEST_TOOL_ID)
        test_data = Dataset(path="tests/test_files/test_text_file.txt", force_upload=False)
        test_data.upload(store=store)
        # [existing dataset input complete]
        params = Parameters()
        params.add_input("test", test_data)
        # doesn't matter here if tool fails
        test_tool.run(data_store=store, params=params)
        history_content = galaxy_instance.histories.show_history(history_id=store.history_id, contents=True)
        # should only be 2 elements here (tool and the dataset passed as param), since dataset was manually uploaded
        assert len(history_content) == 2


def test_remote_dataset_as_parameter(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        test_tool = Tool(TEST_TOOL_ID)
        test_data = Dataset(path=REMOTE_FILE_PATH, remote_file=True)
        test_data_2 = Dataset(path=REMOTE_FILE_PATH_2, remote_file=True)
        params = Parameters()
        params.add_input("test", test_data)
        params.add_input("test2", test_data_2)
        test_tool.run(data_store=store, params=params)
        history_content = galaxy_instance.histories.show_history(history_id=store.history_id, contents=True)
        for item in history_content:
            assert item["state"] == "ok"
