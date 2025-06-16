"""Internal job related classes and functions."""

import time
from datetime import datetime, timezone
from threading import Lock, Thread
from typing import TYPE_CHECKING, Any, Dict, Optional

from bioblend import galaxy
from bioblend.galaxy.datasets import DatasetClient

if TYPE_CHECKING:
    from .data_store import Datastore
from nova.common.job import WorkState

from .dataset import Dataset, DatasetCollection
from .outputs import Outputs
from .parameters import Parameters

REGISTER_NEUTRON_DATA_TOOL = "neutrons_register"


def get_job_details(state: WorkState, job: Dict[str, Any]) -> Dict[str, Any]:
    if "job_messages" not in job or not job["job_messages"]:
        return {}
    for message in job["job_messages"]:
        if "status_details" in message:
            match message["status_details"]["status_details_source"]:
                case "slurm":
                    return get_slurm_status(state, message["status_details"])
    return {}


def to_local_time(input: str) -> str:
    utc_time = datetime.fromisoformat(input).replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone()
    return local_time.strftime("%Y-%m-%d %H:%M:%S")


def get_slurm_status(state: WorkState, status: Dict[str, Any]) -> Dict[str, Any]:
    if state == WorkState.RUNNING:
        short_details = (
            f"Slurm Job Details: Id:{status['JobId']}, Job State:{status['JobState']}, Run Time:{status['RunTime']}"
        )
    else:
        short_details = (
            f"Slurm Job Details: Id:{status['JobId']}, Job State:{status['JobState']},"
            f" Last Evaluation:{to_local_time(status['LastSchedEval'])}"
        )
    return {"message": short_details, "original_dict": status}


class JobStatus:
    """Internal structure to hold job status info."""

    def __init__(self) -> None:
        self.lock = Lock()
        self._details: Dict[str, Any] = {}
        self._state = WorkState.NOT_STARTED

    @property
    def state(self) -> WorkState:
        with self.lock:
            return self._state

    @state.setter
    def state(self, value: WorkState) -> None:
        with self.lock:
            self._state = value

    @property
    def details(self) -> Dict[str, Any]:
        with self.lock:
            return self._details

    @details.setter
    def details(self, value: Dict[str, Any]) -> None:
        with self.lock:
            self._details = value


class Job:
    """Internal class managing Galaxy job execution. Should not be used by end users."""

    def __init__(self, tool_id: str, data_store: "Datastore") -> None:
        self.id = ""
        self.datasets = None
        self.collections = None
        self.tool = tool_id
        self.store = data_store
        self.galaxy_instance = self.store.nova_connection.galaxy_instance
        self.status = JobStatus()
        self.url: Optional[str] = None
        self.thread: Optional[Thread] = None

    def _run_and_wait(self, params: Optional[Parameters]) -> None:
        """Runs tools and waits for result."""
        try:
            self.submit(params)
            self.wait_for_results()
        except Exception as e:
            self.url = None
            if self.status.state in [WorkState.CANCELING, WorkState.CANCELED]:
                self.status.state = WorkState.CANCELED
                return
            self.status.state = WorkState.ERROR
            self.status.details = {"message": str(e)}
            return

        self.status.state = WorkState.FINISHED

    def run(self, params: Optional[Parameters], wait: bool) -> Optional[Outputs]:
        """Runs a job in Galaxy."""
        if self.status.state in [WorkState.NOT_STARTED, WorkState.FINISHED, WorkState.ERROR]:
            self.thread = Thread(target=self._run_and_wait, args=(params,))
            self.thread.start()
            if wait:
                self.join_job_thread()
                return self.get_results()
            return None
        else:
            raise Exception(f"Tool {self.tool} (id: {self.id}) is already running.")

    def run_interactive(
        self, params: Optional[Parameters], wait: bool, max_tries: int = 100, check_url: bool = True
    ) -> Optional[str]:
        """Runs an interactive tool in Galaxy and returns a link to the tool."""
        self.run(params, False)
        if not wait:
            return None
        successful_url = self.get_url(max_tries=max_tries, check_url=check_url)
        if successful_url:
            return successful_url
        # If successful_url is None, then there was an issue starting the interactive tool.
        status = self.cancel()
        # if status is false, the job has been in a terminal state already, indicating an error somewhere in execution.
        if status:
            raise Exception(
                "Unable to fetch the URL for interactive tool. This could be due to needing to pull the docker image. "
                "Try again with a larger 'max_tries' value."
            )
        else:
            raise Exception("Interactive tool was stopped unexpectedly.")

    def submit(self, params: Optional[Parameters]) -> None:
        """Handles uploading inputs and submitting job."""
        self.status.state = WorkState.UPLOADING_DATA
        self.url = None
        datasets_to_upload = {}

        # Set Tool Inputs
        tool_inputs = galaxy.tools.inputs.inputs()
        if params:
            for param, val in params.inputs.items():
                if isinstance(val, Dataset):
                    datasets_to_upload[param] = val
                else:
                    tool_inputs.set_param(param, val)
            ids = self.upload_datasets(datasets=datasets_to_upload)
            if ids:
                for param, val in ids.items():
                    tool_inputs.set_dataset_param(param, val)

        if self.status.state in [WorkState.STOPPING, WorkState.CANCELING]:
            self.status.state = WorkState.CANCELED
            return
        # Run tool and wait for job to finish
        self.status.state = WorkState.QUEUED
        results = self.galaxy_instance.tools.run_tool(
            history_id=self.store.history_id, tool_id=self.tool, tool_inputs=tool_inputs
        )
        self.id = results["jobs"][0]["id"]
        self.datasets = results["outputs"]
        self.collections = results["output_collections"]

    def upload_datasets(self, datasets: Dict[str, Dataset]) -> Optional[Dict[str, str]]:
        """Helper method to upload multiple datasets or collections in parallel."""
        galaxy_instance = self.store.nova_connection.galaxy_instance
        dataset_client = DatasetClient(galaxy_instance)
        dataset_ids: Dict[str, str] = {}
        datasets_to_ingress = {}
        for name, dataset in datasets.items():
            if self.status.state in [WorkState.STOPPING, WorkState.CANCELING]:
                self.cleanup_datasets(dataset_ids)
                return None

            if not dataset.force_upload:
                self._link_existing_dataset(dataset)
                if dataset.id:
                    dataset_ids[name] = dataset.id
                    continue

            if dataset.remote_file:
                datasets_to_ingress[dataset.path] = dataset
            else:
                self._upload_single_dataset(dataset)
            if dataset.id:
                dataset_ids[name] = dataset.id
        self._ingest_datasets(datasets_to_ingress)
        for dataset_output in dataset_ids.values():
            if self.status.state in [WorkState.STOPPING, WorkState.CANCELING]:
                self.cleanup_datasets(dataset_ids)
                return None
            dataset_client.wait_for_dataset(dataset_output)
        return dataset_ids

    def _link_existing_dataset(self, dataset: Dataset) -> None:
        galaxy_instance = self.store.nova_connection.galaxy_instance
        dataset_client = DatasetClient(galaxy_instance)
        existing_data = dataset_client.get_datasets(history_id=self.store.history_id, name=dataset.name)
        if len(existing_data) > 0:
            dataset.id = existing_data[0]["id"]
            dataset.store = self.store

    def _ingest_datasets(self, datasets: dict[str, Dataset]) -> None:
        dataset_client = DatasetClient(self.store.nova_connection.galaxy_instance)
        tool_inputs = galaxy.tools.inputs.inputs()
        i = 0
        for d in datasets:
            tool_inputs.set_param(f"series_{i}|input", d)
            i += 1
        results = self.galaxy_instance.tools.run_tool(
            history_id=self.store.history_id, tool_id=REGISTER_NEUTRON_DATA_TOOL, tool_inputs=tool_inputs
        )
        for output in results["outputs"]:
            dataset_client.wait_for_dataset(dataset_id=output["id"])
            # If two datasets have the same path, then shouldn't matter
            dataset = datasets.get(output["name"], None)
            if dataset:
                dataset.id = output["id"]
                dataset.store = self.store

    def _upload_single_dataset(self, dataset: Dataset) -> None:
        galaxy_instance = self.store.nova_connection.galaxy_instance
        if len(dataset.path) < 1 and dataset.get_content():
            dataset_info = galaxy_instance.tools.paste_content(
                content=str(dataset.get_content()), history_id=self.store.history_id, file_name=dataset.name
            )
        else:
            dataset_info = galaxy_instance.tools.upload_file(path=dataset.path, history_id=self.store.history_id)
        dataset.id = dataset_info["outputs"][0]["id"]
        dataset.store = self.store

    def cleanup_datasets(self, datasets: Dict[str, str]) -> None:
        galaxy_instance = self.store.nova_connection.galaxy_instance
        history_id = galaxy_instance.histories.get_histories(name=self.store.name)[0]["id"]
        for dataset_id in datasets.values():
            galaxy_instance.histories.delete_dataset(history_id=history_id, dataset_id=dataset_id, purge=True)

    def stop(self) -> bool:
        """Stops a job in Galaxy."""
        self.url = None
        self.status.state = WorkState.STOPPING
        response = self.galaxy_instance.make_put_request(
            f"{self.store.nova_connection.galaxy_url}/api/jobs/{self.id}/finish"
        )
        if response:
            return True
        else:
            self.status.details = {"message": "could not stop job"}
            return False

    def cancel(self) -> bool:
        """Cancel a job in Galaxy."""
        self.url = None
        self.status.state = WorkState.CANCELING
        try:
            return self.galaxy_instance.jobs.cancel_job(self.id)
        except Exception:
            return False

    def join_job_thread(self) -> None:
        if self.thread:
            self.thread.join()

    def wait_for_results(self, timeout: float = 1200000) -> None:
        """Wait for job to finish."""
        self.galaxy_instance.jobs.wait_for_job(self.id, maxwait=timeout, check=True)

    def get_state(self) -> JobStatus:
        """Returns current state of job."""
        if self.status.state == WorkState.QUEUED or self.status.state == WorkState.RUNNING:
            try:
                job = self.galaxy_instance.jobs.show_job(self.id, full_details=True)
                if job["state"] == "running":
                    self.status.state = WorkState.RUNNING
                elif job["state"] == "error":
                    self.status.state = WorkState.ERROR
                elif job["state"] == "deleted":
                    self.status.state = WorkState.DELETED
                self.status.details = get_job_details(self.status.state, job)
            except Exception:
                pass
        return self.status

    def get_results(self) -> Optional[Outputs]:
        """Return results from finished job."""
        if self.status.state == WorkState.FINISHED:
            outputs = Outputs()
            if self.datasets:
                for dataset in self.datasets:
                    d = Dataset(dataset["output_name"])
                    d.id = dataset["id"]
                    d.file_type = dataset.get("file_ext", "")
                    d.store = self.store
                    outputs.add_output(d)
            if self.collections:
                for collection in self.collections:
                    dc = DatasetCollection(collection["output_name"])
                    dc.id = collection["id"]
                    dc.store = self.store
                    outputs.add_output(dc)

            return outputs
        elif self.status.state == WorkState.ERROR:
            return None
        else:
            raise Exception(f"Job {self.id} has not finished running.")

    def get_url(self, max_tries: int = 100, check_url: bool = True) -> Optional[str]:
        """Get the URL or endpoint for this tool."""
        if self.url:
            return self.url
        timer = max_tries
        while timer > 0:
            try:
                entry_points = self.galaxy_instance.make_get_request(
                    f"{self.store.nova_connection.galaxy_url}/api/entry_points?job_id={self.id}"
                )
                for ep in entry_points.json():
                    if ep["job_id"] == self.id and ep.get("target", None):
                        url = f"{self.store.nova_connection.galaxy_url}{ep['target']}"
                        self.url = url
                        response = self.galaxy_instance.make_get_request(url)
                        if response.status_code == 200 or not check_url:
                            return url
            except Exception:
                continue
            finally:
                timer -= 1
                time.sleep(1)
        return None

    def get_console_output(self, start: int, length: int) -> Dict[str, str]:
        """Get all the current console output."""
        out = self.galaxy_instance.make_get_request(
            f"{self.store.nova_connection.galaxy_url}/api/jobs/"
            f"{self.id}/console_output?stdout_position={start}&stdout_length="
            f"{length}&stderr_position={start}&stderr_length={length}"
        )
        out.raise_for_status()
        return out.json()
