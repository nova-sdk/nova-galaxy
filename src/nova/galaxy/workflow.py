"""Contains classes to run workflows in Galaxy via Connection."""

from threading import Lock, Thread
from typing import TYPE_CHECKING, Dict, List, Optional, Union

if TYPE_CHECKING:
    from .data_store import Datastore

from bioblend import TimeoutException

from nova.common.job import WorkState

from .dataset import AbstractData, Dataset, DatasetCollection
from .outputs import Outputs
from .parameters import Parameters, WorkflowParameters
from .tool import Tool


class AbstractWorkflow:
    """Abstraction for a runnable object in Galaxy such as a tool or workflow."""

    def __init__(self, id: str):
        self.id = id

    def get_outputs(self) -> List[AbstractData]:
        return []

    def get_inputs(self) -> List[Parameters]:
        return []

    def run(self, data_store: "Datastore", params: WorkflowParameters, wait: bool) -> Union[Outputs, None]:
        return None


class InvocationStatus:
    """Internal structure to hold workflow invocation status info."""

    def __init__(self) -> None:
        self.lock = Lock()
        self._state = WorkState.NOT_STARTED
        self._details = ""

    @property
    def state(self) -> WorkState:
        with self.lock:
            return self._state

    @state.setter
    def state(self, value: WorkState) -> None:
        with self.lock:
            self._state = value

    @property
    def details(self) -> str:
        with self.lock:
            return self._details

    @details.setter
    def details(self, value: str) -> None:
        with self.lock:
            self._details = value


class Invocation:
    """Internal class managing Galaxy workflow invocation. Should not be used by end users."""

    def __init__(self, workflow_id: str, data_store: "Datastore") -> None:
        self.workflow_id = workflow_id
        self.store = data_store
        self.galaxy_instance = self.store.nova_connection.galaxy_instance
        self.status = InvocationStatus()
        self.invocation_id: Optional[str] = None
        self.outputs_data: Optional[Dict] = None

    def _map_galaxy_state_to_workstate(self, galaxy_state: str) -> WorkState:
        """Maps Galaxy states (both invocation and job states) to internal WorkState enum."""
        state_map = {
            # Common states
            "new": WorkState.QUEUED,
            "queued": WorkState.QUEUED,
            "running": WorkState.RUNNING,
            "ok": WorkState.FINISHED,
            "error": WorkState.ERROR,
            "paused": WorkState.QUEUED,
            "canceled": WorkState.CANCELED,
            # Invocation-specific states
            "scheduled": WorkState.QUEUED,
            "failed": WorkState.ERROR,
            # Job-specific states
            "upload": WorkState.UPLOADING_DATA,
            "waiting": WorkState.QUEUED,
            "deleted": WorkState.DELETED,
            "stopped": WorkState.CANCELED,
        }
        return state_map.get(galaxy_state, WorkState.ERROR)

    def _extract_error_details_from_invocation(self, invocation_details: Dict) -> str:
        """Parses invocation details to extract a detailed error message."""
        error_list = [f"Invocation failed. Overall State: {invocation_details.get('state', 'Unknown')}."]
        if "steps" in invocation_details and isinstance(invocation_details["steps"], list):
            for step in invocation_details["steps"]:
                step_galaxy_state = step.get("state")
                if self._map_galaxy_state_to_workstate(step_galaxy_state) == WorkState.ERROR:
                    step_label = step.get("workflow_step_label", f"Step ID {step.get('id', 'Unknown')}")
                    error_list.append(f"  - Step '{step_label}' failed with state: {step_galaxy_state}.")
                    # TODO: Future enhancement: Extract more specific error messages from step['messages']
        return "\n".join(error_list)

    def _run_and_wait(self, params: Optional[WorkflowParameters]) -> None:
        """Submits workflow invocation and waits for completion."""
        try:
            self.submit(params)
            if self.invocation_id:
                self.wait_for_results()
                invocation_details = self.galaxy_instance.invocations.show_invocation(self.invocation_id)
                self.status.state = self._map_galaxy_state_to_workstate(invocation_details["state"])
                if self.status.state == WorkState.ERROR:
                    self.status.details = self._extract_error_details_from_invocation(invocation_details)
                elif self.status.state == WorkState.FINISHED:
                    self.outputs_data = invocation_details
            else:
                self.status.state = WorkState.ERROR
                self.status.details = "Workflow submission failed prior to obtaining invocation ID."

        except Exception as e:
            self.status.state = WorkState.ERROR
            self.status.details = f"Error during workflow execution or waiting: {str(e)}"

    def run(self, params: Optional[WorkflowParameters], wait: bool) -> Optional[Outputs]:
        """Runs the workflow invocation."""
        if self.status.state in [WorkState.NOT_STARTED, WorkState.FINISHED, WorkState.ERROR, WorkState.CANCELED]:
            self.status = InvocationStatus()
            self.invocation_id = None
            self.outputs_data = None
            thread = Thread(target=self._run_and_wait, args=(params,))
            thread.start()
            if wait:
                thread.join()
                if self.status.state == WorkState.ERROR:
                    raise Exception(f"Workflow invocation failed: {self.status.details}")
                return self.get_results()
            return None
        else:
            raise Exception(
                f"Workflow {self.workflow_id} (invocation: {self.invocation_id}) is already running or in an"
                f"intermediate state ({self.status.state}). Cannot start a new run."
            )

    def submit(self, params: Optional[WorkflowParameters]) -> None:
        """Handles input preparation and submits the workflow invocation using explicit bioblend approach."""
        try:
            if params:
                bioblend_inputs = params.get_bioblend_inputs()
                bioblend_params = params.get_bioblend_params()
            else:
                bioblend_inputs = {}
                bioblend_params = {}

            self.status.state = WorkState.QUEUED
            invocation_info = self.galaxy_instance.workflows.invoke_workflow(
                workflow_id=self.workflow_id,
                inputs=bioblend_inputs,
                params=bioblend_params,
                history_id=self.store.history_id,
                parameters_normalized=False,
            )
            self.invocation_id = invocation_info["id"]
            self.status.state = self._map_galaxy_state_to_workstate(invocation_info["state"])
        except Exception as e:
            self.status.state = WorkState.ERROR
            self.status.details = f"Failed to prepare or submit workflow invocation: {str(e)}"
            self.invocation_id = None

    def wait_for_results(self, max_tries: int | None = None) -> None:
        """Waits for the workflow invocation to complete."""
        if not self.invocation_id:
            raise Exception("Cannot wait for results, invocation ID is not set.")

        # galaxy doesn't always return when a job fails. Periodically checking the jobs to see if we should return.
        attempt_counter = 0
        while True:
            try:
                if max_tries is None or attempt_counter < max_tries:
                    self.galaxy_instance.invocations.wait_for_invocation(self.invocation_id, maxwait=5)
                break
            except TimeoutException:
                # check if any steps failed. If they have we return. Otherwise we just wait some more.
                attempt_counter += 1
                for step in self.get_step_jobs(running_only=False):
                    if step._job is not None:
                        if step.get_status() is WorkState.ERROR:
                            return

        # galaxy returns once all steps are scheduled instead of complete. Need to wait for each job to complete
        for step in self.get_step_jobs():
            if step._job is not None:
                step._job.wait_for_results()
                if step.get_status() is not WorkState.FINISHED:
                    return

    def get_state(self) -> InvocationStatus:
        """Returns the current state of the workflow invocation."""
        if not self.invocation_id or self.status.state in [WorkState.FINISHED, WorkState.ERROR, WorkState.CANCELED]:
            return self.status

        try:
            invocation_details = self.galaxy_instance.invocations.show_invocation(self.invocation_id)
            self.status.state = self._map_galaxy_state_to_workstate(invocation_details["state"])
            # Galaxy doesn't update workflow state to finished but leaves them at scheduled. Checking each job.
            if self.status.state is WorkState.QUEUED:
                jobs_finished = True
                for step in self.get_step_jobs():
                    if step.get_status() is not WorkState.FINISHED:
                        jobs_finished = False
                if jobs_finished:
                    self.status.state = WorkState.FINISHED

            if self.status.state == WorkState.ERROR and not self.status.details:  # Check details
                self.status.details = self._extract_error_details_from_invocation(invocation_details)
            if self.status.state == WorkState.FINISHED:
                self.outputs_data = invocation_details

        except Exception as e:
            print(f"Warning: Could not fetch invocation state for {self.invocation_id}: {e}")

        return self.status

    def get_results(self) -> Optional[Outputs]:
        """Returns the results (outputs) from a completed workflow invocation."""
        current_status = self.get_state()

        if current_status.state != WorkState.FINISHED:
            print(f"Cannot get results. Invocation state is {current_status.state} (ID: {self.invocation_id}).")
            return None

        if not self.outputs_data:
            try:
                assert isinstance(self.invocation_id, str)
                self.outputs_data = self.galaxy_instance.invocations.show_invocation(self.invocation_id)
            except Exception as e:
                raise Exception(f"Failed to fetch invocation details for results processing: {e}") from e

        outputs = Outputs()
        try:
            if "outputs" in self.outputs_data:
                for output_name, dataset_info in self.outputs_data["outputs"].items():
                    if dataset_info and "id" in dataset_info and "src" in dataset_info and dataset_info["src"] == "hda":
                        d = Dataset(output_name)
                        d.id = dataset_info["id"]
                        d.store = self.store
                        outputs.add_output(d)

            if "output_collections" in self.outputs_data:
                for output_name, collection_info in self.outputs_data["output_collections"].items():
                    if (
                        collection_info
                        and "id" in collection_info
                        and "src" in collection_info
                        and collection_info["src"] == "hdca"
                    ):
                        dc = DatasetCollection(output_name)
                        dc.id = collection_info["id"]
                        dc.store = self.store
                        outputs.add_output(dc)

            return outputs

        except Exception as e:
            raise Exception(f"Error processing invocation results: {e}") from e

    def cancel(self) -> bool:
        """Cancels the workflow invocation."""
        if not self.invocation_id or self.status.state in [WorkState.FINISHED, WorkState.ERROR, WorkState.CANCELED]:
            return False

        try:
            success = self.galaxy_instance.invocations.cancel_invocation(self.invocation_id)
            if success:
                self.status.state = WorkState.CANCELED
                self.status.details = "Invocation canceled by user."
            return True
        except Exception as e:
            print(f"Error cancelling invocation {self.invocation_id}: {e}")
            return False

    def get_invocation_id(self) -> Optional[str]:
        """Returns the Galaxy invocation ID."""
        return self.invocation_id

    def get_step_jobs(self, running_only: bool = True) -> List[Tool]:
        """Returns nova-galaxy Job instances for each step in the workflow invocation."""
        if not self.invocation_id:
            return []

        try:
            jobs_summary = self.galaxy_instance.invocations.get_invocation_step_jobs_summary(self.invocation_id)
            step_jobs = []
            tools = self.store.recover_tools(filter_running=running_only)

            for job_info in jobs_summary:
                if job_info.get("id"):
                    for tool in tools:
                        if job_info.get("id") == tool.get_uid():
                            step_jobs.append(tool)

            return step_jobs
        except Exception as e:
            print(f"Warning: Could not fetch invocation step jobs for {self.invocation_id}: {e}")
            return []

    def get_step_name(self, step_number: int) -> str:
        if not self.invocation_id:
            return ""

        try:
            steps = self.galaxy_instance.invocations.show_invocation(self.invocation_id).get("steps")
            if steps is None:
                return ""

            if step_number >= len(steps):
                return ""

            return steps[step_number]["workflow_step_label"]

        except Exception as e:
            print(f"Warning: Could not fetch invocation step jobs for {self.invocation_id}: {e}")
            return ""


class Workflow(AbstractWorkflow):
    """Represents a Galaxy workflow that can be invoked (run).

    It's recommended to create a new Workflow object for each invocation
    to prevent state conflicts if run multiple times.
    """

    def __init__(self, id: str):
        """Initializes a Workflow object.

        Parameters
        ----------
        id : str
            The Galaxy workflow ID (obtainable via `galaxy_instance.workflows.get_workflows()`).
        """
        super().__init__(id)
        self._invocation: Optional[Invocation] = None

    def run(
        self, data_store: "Datastore", params: Optional[WorkflowParameters] = None, wait: bool = True
    ) -> Optional[Outputs]:
        """Invokes (runs) this workflow in the specified data store.

        By default, runs in a blocking manner (waits for completion). Set `wait=False`
        for non-blocking execution.

        Parameters
        ----------
        data_store : Datastore
            The data store (history) where the workflow will be invoked.
        params : Optional[Parameters]
            The input parameters and datasets for the workflow. The structure of these
            parameters needs to align with how the workflow expects inputs (e.g., keyed
            by step labels or IDs). See `Invocation.submit` for details.
        wait : bool, optional
            If True (default), wait for the workflow invocation to complete before returning.
            If False, start the invocation and return None immediately.

        Returns
        -------
        Optional[Outputs]
            If `wait` is True and the invocation completes successfully, returns an
            `Outputs` object containing the workflow results.
            If `wait` is False or the invocation fails, returns None.

        Raises
        ------
        Exception
            If the workflow is already running or if an error occurs during execution
            when `wait` is True.
        """
        self._invocation = Invocation(workflow_id=self.id, data_store=data_store)
        return self._invocation.run(params=params, wait=wait)

    def get_status(self) -> WorkState:
        """Returns the current status of the last workflow invocation.

        Returns
        -------
        WorkState
            The current state (e.g., QUEUED, RUNNING, FINISHED, ERROR).
            Returns NOT_STARTED if `run` has not been called yet.
        """
        if self._invocation:
            return self._invocation.get_state().state
        else:
            return WorkState.NOT_STARTED

    def get_full_status(self) -> Optional[InvocationStatus]:
        """Returns the full status object of the last workflow invocation.

        Returns
        -------
        Optional[InvocationStatus]
            The InvocationStatus object containing state and details.
            Returns None if `run` has not been called yet.
        """
        if self._invocation:
            return self._invocation.get_state()
        return None

    def get_results(self) -> Optional[Outputs]:
        """Returns the results from the last completed workflow invocation.

        Should only be called after the workflow has finished successfully
        (i.e., `get_status()` returns FINISHED).

        Returns
        -------
        Optional[Outputs]
            An `Outputs` object containing the workflow results if finished,
            otherwise None.

        Raises
        ------
        Exception
            If called before the invocation is finished, or if there was an
            error fetching or processing results.
        """
        if self._invocation:
            return self._invocation.get_results()
        return None

    def cancel(self) -> bool:
        """Cancels the currently running workflow invocation.

        Returns
        -------
        bool
            True if cancellation was successfully requested, False otherwise.
        """
        if self._invocation:
            return self._invocation.cancel()
        return False

    def stop(self) -> bool:
        """Stops (cancels) the currently running workflow invocation.

        Alias for cancel().
        """
        return self.cancel()

    def get_invocation_id(self) -> Optional[str]:
        """Gets the Galaxy invocation ID for the last run.

        Returns
        -------
        Optional[str]
            The invocation ID if `run()` has been called, otherwise None.
        """
        if self._invocation:
            return self._invocation.get_invocation_id()
        return None

    def get_step_jobs(self, running_only: bool = True) -> List[Tool]:
        """Gets nova-galaxy Job instances for each step in the workflow.

        Returns the individual jobs that make up the workflow steps,
        allowing access to step-level status, outputs, and console logs.

        Parameters
        ----------
        running_only : Optional[bool]
            A boolean that determines whether or not to return only jobs which
           are currently running.

        Returns
        -------
        List[Job]
            List of Job instances representing workflow steps.
            Returns empty list if workflow hasn't been run yet.

        Examples
        --------
        >>> workflow = Workflow("workflow_id")
        >>> workflow.run(data_store, params, wait=False)
        >>> jobs = workflow.get_step_jobs()
        >>> for job in jobs:
        ...     print(f"Step {job.tool}: {job.status.state}")
        ...     if job.status.state == WorkState.RUNNING:
        ...         console = job.get_console_output(0, 1000)
        ...         print(console.get('stdout', ''))
        """
        if self._invocation:
            return self._invocation.get_step_jobs(running_only)
        return []

    def get_step_name(self, step_number: int) -> str:
        """Gets the name of the step in the workflow.

        Returns the string of the name of the step associated with the number.

        Returns
        -------
        str
            Name of the step as declared in Galaxy. Empty if step doesn't exist.
        """
        if self._invocation:
            return self._invocation.get_step_name(step_number)
        return ""

    def get_active_step(self) -> Optional[Tool]:
        """Gets the currently active (running) step in the workflow invocation.

        This method iterates through all jobs associated with the workflow steps
        and returns the first one found to be in the 'RUNNING' state.

        Returns
        -------
        Optional["Job"]
            The Job instance representing the currently running step.
            Returns None if no step is currently running, if the workflow
            hasn't been run yet, or if step jobs cannot be retrieved.
        """
        if not self._invocation:
            return None

        step_jobs = self._invocation.get_step_jobs()
        for job in step_jobs:
            if job.get_status().state == WorkState.RUNNING:
                return job
        return None

    def wait_for_results(self) -> None:
        """Waits on the workflow to complete.

        This method will wait for a running work to complete
        """
        if not self._invocation:
            return
        return self._invocation.wait_for_results()
