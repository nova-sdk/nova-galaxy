"""Tool Runner classes."""

import asyncio
import threading
from concurrent.futures import CancelledError
from copy import copy
from typing import Any, Callable, Optional

from blinker import signal

from nova.common.job import ToolOutputs, WorkState
from nova.common.signals import Signal, ToolCommand, get_signal_id
from nova.galaxy import Connection, Tool
from nova.galaxy.interfaces import BasicTool
from nova.galaxy.job import JobStatus

StoreFactoryFunction = Callable[[], str]


def job_stopped(state: WorkState) -> bool:
    return state in [
        WorkState.FINISHED,
        WorkState.CANCELED,
        WorkState.ERROR,
        WorkState.DELETED,
    ]


class ToolRunner:
    """Class that manages running tools.

    This class is responsible for managing the execution of tools in Galaxy.

    Parameters
    ----------
    id : str
        Unique identifier for the tool runner instance. Should be the same in all GUI components from nov
        a-trame libraray so that events could be passed between the Tool Runner and components
    tool : BasicTool
        An instance of the tool to be executed.
    store_factory : StoreFactoryFunction
        A factory function that returns a name of a store the tool should run with
    galaxy_url : str
        The URL of the Galaxy server to interact with.
    galaxy_api_key : str
        API key used for authentication with the Galaxy server.
    """

    def __init__(
        self, id: str, tool: BasicTool, store_factory: StoreFactoryFunction, galaxy_url: str, galaxy_api_key: str
    ) -> None:
        self.galaxy_url = galaxy_url
        self.galaxy_api_key = galaxy_api_key

        self.sender_id = f"ToolRunner_{id}"
        self.store_factory = store_factory
        self.tool = tool
        self.monitoring_task: Optional[asyncio.Task] = None
        self.output_monitoring_task: Optional[asyncio.Task] = None
        self.run_thread: Optional[threading.Thread] = None
        self.nova_tool: Optional[Tool] = None
        self.current_status: JobStatus = JobStatus()
        self.current_outputs: ToolOutputs = ToolOutputs()
        self.progress_signal = signal(get_signal_id(id, Signal.PROGRESS))
        self.error_message_signal = signal(get_signal_id(id, Signal.ERROR_MESSAGE))
        self.execution_signal = signal(get_signal_id(id, Signal.TOOL_COMMAND))
        self.outputs_signal = signal(get_signal_id(id, Signal.OUTPUTS))

        self.error: str = ""
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        self.execution_signal.connect(self._process_command, weak=False)

    async def _process_command(self, sender: Any, command: str) -> Any:
        match command:
            case ToolCommand.START:
                self._start_tool()
            case ToolCommand.STOP:
                self._stop_tool()
            case ToolCommand.CANCEL:
                self._cancel_tool()
            case ToolCommand.GET_RESULTS:
                res = await self._get_results()
                return {"sender": sender, "command": command, "results": res}

    async def _output_monitor_run(self) -> None:
        while True:
            try:
                if self.error or self.nova_tool:
                    if self.nova_tool:
                        tool_status = self.nova_tool.get_full_status()
                        tool_state = tool_status.state
                        self._update_outputs(tool_status)
                    else:
                        tool_state = WorkState.ERROR
                        self.current_outputs.stderr = self.error
                    await self.outputs_signal.send_async(self.sender_id, outputs=self.current_outputs)
                    if job_stopped(tool_state):
                        break
            except Exception as e:
                print(f"Exception during output monitoring: {e}")
            await asyncio.sleep(1)

    def _update_outputs(self, tool_status: JobStatus) -> None:
        if not self.nova_tool:
            return
        tool_state = tool_status.state
        try:
            stdout = self.nova_tool.get_stdout(len(self.current_outputs.stdout), 100000) or ""
            stderr = self.nova_tool.get_stderr(len(self.current_outputs.stderr), 100000) or ""
        except Exception:
            stdout = ""
            stderr = ""
        if tool_state in [WorkState.RUNNING, WorkState.STOPPING]:
            self.current_outputs.stdout += stdout
            self.current_outputs.stderr += stderr
        else:
            self.current_outputs.stdout = stdout
            self.current_outputs.stderr = stderr

        if tool_state == WorkState.ERROR:
            if tool_status.details:
                self.current_outputs.stderr = f"{tool_status.details['message']}\n{self.current_outputs.stderr}"

    async def _monitor_run(self) -> None:
        while True:
            try:
                if self.nova_tool or self.error:
                    status = self._get_job_status()
                    if self.current_status.state != status.state or self.current_status.details != status.details:
                        self.current_status = status
                        await self._send_status_change_signal()
                        if job_stopped(self.current_status.state):
                            break
            except Exception as e:
                print(f"Exception during run monitoring: {e}")

            await asyncio.sleep(0.5)

    async def _send_status_change_signal(self) -> None:
        if self.current_status.state == WorkState.ERROR:
            error_message = self.current_status.details.get("message", "")
            await self.error_message_signal.send_async(self.sender_id, error_message=error_message)
        await self.progress_signal.send_async(
            self.sender_id, state=self.current_status.state, details=self.current_status.details
        )

    def _get_job_status(self) -> JobStatus:
        if self.nova_tool:
            status = copy(self.nova_tool.get_full_status())
            if status.state == WorkState.ERROR:
                status.details = {"message": "Error running NDIP tool. Please see tool outputs for more information."}
        else:
            status = JobStatus()
            status.state = WorkState.ERROR
            status.details = {"message": self.error}
        return status

    def _run_in_background(self) -> None:
        try:
            try:
                self.tool.validate_for_run()
            except ValueError as e:
                self.error = str(e)
                return
            nova_connection = Connection(self.galaxy_url, self.galaxy_api_key).connect()
            store = nova_connection.get_data_store(self.store_factory())
            self.tool.set_store(store)
            self.nova_tool, nova_tool_params = self.tool.prepare_tool()
            self.nova_tool.run(data_store=store, params=nova_tool_params, wait=False)
        except Exception as e:
            self.error = str(e)

    def _wait_async_task_finishes(self, task: Optional[asyncio.Task[Any]]) -> None:
        if not task:
            return

        async def wait_for_cancel() -> None:
            try:
                await task
            except Exception:
                pass

        if not self.loop:
            raise Exception("Event loop is not set")

        future = asyncio.run_coroutine_threadsafe(wait_for_cancel(), self.loop)
        try:
            future.result()
        except CancelledError:
            pass

    def _start_tool(self) -> None:
        self.current_status.state = WorkState.NOT_STARTED
        self.nova_tool = None
        self.error = ""
        self.current_outputs = ToolOutputs()
        self.loop = asyncio.get_event_loop()
        self.run_thread = threading.Thread(target=self._run_in_background, daemon=True)
        self.run_thread.start()
        self.monitoring_task = asyncio.create_task(self._monitor_run())
        self.output_monitoring_task = asyncio.create_task(self._output_monitor_run())

    def _cancel_in_background(self) -> None:
        if not self.nova_tool:
            raise Exception("Job should be started first")
        self.nova_tool.cancel()
        if self.run_thread:
            self.run_thread.join()
        self._wait_async_task_finishes(self.monitoring_task)
        self._wait_async_task_finishes(self.output_monitoring_task)

    async def _get_results(self) -> Optional[bytes]:
        if not self.nova_tool:
            return None
        try:
            res = self.tool.get_results(self.nova_tool)
        except Exception as e:
            await self.error_message_signal.send_async(self.sender_id, error_message=f"cannot download results: {e}")
            res = None
        return res

    def _cancel_tool(self) -> None:
        cancel_thread = threading.Thread(target=self._cancel_in_background, daemon=True)
        cancel_thread.start()

    def _stop_in_background(self) -> None:
        if not self.nova_tool:
            raise Exception("Job should be started first")
        self.nova_tool.stop()
        if self.run_thread:
            self.run_thread.join()
        self._wait_async_task_finishes(self.monitoring_task)
        self._wait_async_task_finishes(self.output_monitoring_task)

    def _stop_tool(self) -> None:
        stop_thread = threading.Thread(target=self._stop_in_background, daemon=True)
        stop_thread.start()
