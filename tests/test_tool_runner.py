"""Tests for tools."""

import asyncio
import os
from typing import Any, Dict, Optional, Tuple

import blinker
import pytest
from nova.common.job import WorkState
from nova.common.signals import Signal, ToolCommand, get_signal_id

from nova.galaxy import BasicTool, Connection, Parameters, Tool, ToolRunner
from nova.galaxy.connection import global_cleanup, global_get_running_tools

GALAXY_URL = os.environ.get("NOVA_GALAXY_TEST_GALAXY_URL", "https://calvera-test.ornl.gov")
GALAXY_API_KEY = os.environ.get("NOVA_GALAXY_TEST_GALAXY_KEY", "")


# [BasicTool example]
class RemoteCommandTool(BasicTool):
    """Class that prepares RemoteCommandTool tool."""

    def __init__(self) -> None:
        super().__init__()

    def prepare_tool(self) -> Tuple[Tool, Parameters]:
        tool_params = Parameters()
        tool = Tool(id="neutrons_remote_command")
        return tool, tool_params

    def get_results(self, tool: Tool) -> bytes:
        outputs = tool.get_results()
        if not outputs:
            raise Exception("no outputs")
        data = outputs.get_dataset("output1")
        return data.get_content()


# [BasicTool example complete]


class NotebookTool(BasicTool):
    """Class that prepares RemoteCommandTool tool."""

    def __init__(self) -> None:
        super().__init__()

    def prepare_tool(self) -> Tuple[Tool, Optional[Parameters]]:
        tool_params = None
        tool = Tool(id="interactive_tool_jupyter_notebook")
        return tool, tool_params

    def get_results(self, tool: Tool) -> bytes:
        return "".encode("utf-8")


# this is not how it is usually works since different parts would be in different components. But here we put everything
# in one place to test
@pytest.mark.asyncio
async def test_tool_runner(nova_instance: Connection) -> None:
    # [tool runner example start]
    id = "test"
    ToolRunner(id, RemoteCommandTool(), lambda: "nova_galaxy_testing", GALAXY_URL, GALAXY_API_KEY)
    execution_signal = blinker.signal(get_signal_id(id, Signal.TOOL_COMMAND))
    progress_signal = blinker.signal(get_signal_id(id, Signal.PROGRESS))
    await execution_signal.send_async(id, command=ToolCommand.START)
    # [tool runner example start complete]

    # setup state change callback and update results
    results: Dict[str, Any] = {"res": None}

    async def update_state(_sender: Any, state: WorkState, details: str) -> None:
        if state == WorkState.FINISHED:
            responses = await execution_signal.send_async("test", command=ToolCommand.GET_RESULTS)
            results["res"] = responses[0][1]["results"]
        elif state == WorkState.ERROR:
            results["res"] = b"error"

    progress_signal.connect(update_state, weak=False)

    # waiting for results to be updated
    for _ in range(60):
        if results["res"] is not None:
            break
        await asyncio.sleep(1)

    # to delete Galaxy history
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()

    assert results["res"] is not None
    assert "hostname:" in results["res"].decode("utf-8")


@pytest.mark.asyncio
async def test_global_cleanup(nova_instance: Connection) -> None:
    id = "test"
    ToolRunner(id, NotebookTool(), lambda: "nova_galaxy_testing", GALAXY_URL, GALAXY_API_KEY)
    execution_signal = blinker.signal(get_signal_id(id, Signal.TOOL_COMMAND))
    await execution_signal.send_async(id, command=ToolCommand.START)
    await asyncio.sleep(5)
    kill_on_exit_signal = blinker.signal(Signal.EXIT_SIGNAL)
    assert len(global_get_running_tools()) > 0
    kill_on_exit_signal.send()
    await asyncio.sleep(5)
    assert len(global_get_running_tools()) == 0

    # to delete Galaxy history
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()


@pytest.mark.asyncio
async def test_global_get_jobs(nova_instance: Connection) -> None:
    id = "test"
    ToolRunner(id, NotebookTool(), lambda: "nova_galaxy_testing", GALAXY_URL, GALAXY_API_KEY)
    execution_signal = blinker.signal(get_signal_id(id, Signal.TOOL_COMMAND))
    await execution_signal.send_async(id, command=ToolCommand.START)
    await asyncio.sleep(5)
    get_jobs_signal = blinker.signal(Signal.GET_ALL_TOOLS)
    response = get_jobs_signal.send()
    assert len(response[0][1]) > 0  # response is a list of tuples with two elements: the function, and the return value
    global_cleanup()

    # to delete Galaxy history
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
