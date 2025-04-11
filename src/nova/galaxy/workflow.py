"""Contains classes to run workflows in Galaxy via Connection."""

import time
from threading import Thread
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from bioblend import galaxy

if TYPE_CHECKING:
    from .data_store import Datastore
    from .dataset import AbstractData

from .dataset import AbstractData, Dataset, DatasetCollection, upload_datasets
from .outputs import Outputs
from .parameters import Parameters
from .tool import AbstractWork
from .util import WorkState


class InvocationStatus:
    """Internal structure to hold workflow invocation status info."""

    def __init__(self) -> None:
        self.state = WorkState.NOT_STARTED
        self.details = ""
        self.error_msg = ""


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
        """Maps Galaxy invocation states to internal WorkState enum."""
        state_map = {
            "new": WorkState.QUEUED,
            "scheduled": WorkState.QUEUED,
            "running": WorkState.RUNNING,
            "ok": WorkState.FINISHED,
            "paused": WorkState.PAUSED,
            "failed": WorkState.ERROR,
            "error": WorkState.ERROR,
            "cancelled": WorkState.CANCELLED,
        }
        return state_map.get(galaxy_state, WorkState.ERROR)

    def _run_and_wait(self, params: Optional[Parameters]) -> None:
        """Submits workflow invocation and waits for completion."""
        try:
            self.submit(params)
            if self.invocation_id:
                self.wait_for_results()
                invocation_details = self.galaxy_instance.invocations.show_invocation(self.invocation_id)
                self.status.state = self._map_galaxy_state_to_workstate(invocation_details['state'])
                if self.status.state == WorkState.ERROR:
                     # TODO: Potentially parse invocation_details['steps'] for more specific error messages
                     self.status.error_msg = f"Invocation failed. State: {invocation_details['state']}"
                elif self.status.state == WorkState.FINISHED:
                     self.outputs_data = invocation_details
            else:
                 self.status.state = WorkState.ERROR
                 self.status.error_msg = "Workflow submission failed prior to obtaining invocation ID."

        except Exception as e:
            self.status.state = WorkState.ERROR
            self.status.error_msg = f"Error during workflow execution or waiting: {str(e)}"


    def run(self, params: Optional[Parameters], wait: bool) -> Optional[Outputs]:
        """Runs the workflow invocation."""
        if self.status.state in [WorkState.NOT_STARTED, WorkState.FINISHED, WorkState.ERROR, WorkState.CANCELLED]:
            self.status = InvocationStatus()
            self.invocation_id = None
            self.outputs_data = None
            thread = Thread(target=self._run_and_wait, args=(params,))
            thread.start()
            if wait:
                thread.join()
                if self.status.state == WorkState.ERROR:
                     raise Exception(f"Workflow invocation failed: {self.status.error_msg}")
                return self.get_results()
            return None
        else:
            raise Exception(f"Workflow {self.workflow_id} (invocation: {self.invocation_id}) is already running or in an intermediate state ({self.status.state}). Cannot start a new run.")


    def submit(self, params: Optional[Parameters]) -> None:
        """Handles input preparation and submits the workflow invocation."""
        self.status.state = WorkState.PREPARING_INPUTS

        bioblend_inputs = {}
        bioblend_params = {}

        try:
            workflow_details = self.galaxy_instance.workflows.show_workflow(self.workflow_id)
            label_to_input_id = {v['label']: k for k, v in workflow_details.get('inputs', {}).items() if v.get('label')}
            label_to_step_id = {step['label']: str(step['id']) for step in workflow_details.get('steps', {}).values() if step.get('label')}

            if params:
                for label, value in params.inputs.items():
                    if isinstance(value, Dataset):
                        input_id = label_to_input_id.get(label)
                        if not input_id:
                            raise ValueError(f"Workflow input label '{label}' not found in workflow '{self.workflow_id}'. Available input labels: {list(label_to_input_id.keys())}")
                        if not value.id:
                             raise ValueError(f"Input dataset '{label}' must have an ID (must exist in Galaxy history). Upload it first if necessary.")
                        bioblend_inputs[input_id] = {'src': 'hda', 'id': value.id}
                    elif isinstance(value, DatasetCollection):
                        input_id = label_to_input_id.get(label)
                        if not input_id:
                            raise ValueError(f"Workflow input label '{label}' not found in workflow '{self.workflow_id}'. Available input labels: {list(label_to_input_id.keys())}")
                        if not value.id:
                             raise ValueError(f"Input dataset collection '{label}' must have an ID (must exist in Galaxy history).")
                        bioblend_inputs[input_id] = {'src': 'hdca', 'id': value.id}
                    elif isinstance(value, dict):
                        step_id = label_to_step_id.get(label)
                        if not step_id:
                             raise ValueError(f"Workflow step label '{label}' not found in workflow '{self.workflow_id}' for setting parameters. Available step labels: {list(label_to_step_id.keys())}")
                        bioblend_params[step_id] = value
                    else:
                        print(f"Warning: Parameter '{label}' is not a Dataset, DatasetCollection, or a dictionary associated with a known step label. It will be ignored.")


            self.status.state = WorkState.QUEUED
            invocation_info = self.galaxy_instance.workflows.invoke_workflow(
                workflow_id=self.workflow_id,
                inputs=bioblend_inputs,
                params=bioblend_params,
                history_id=self.store.history_id,
                parameters_normalized=False
            )
            self.invocation_id = invocation_info['id']
            self.status.state = self._map_galaxy_state_to_workstate(invocation_info['state'])

        except Exception as e:
            self.status.state = WorkState.ERROR
            self.status.error_msg = f"Failed to prepare or submit workflow invocation: {str(e)}"
            self.invocation_id = None


    def wait_for_results(self) -> None:
        """Waits for the workflow invocation to complete."""
        if not self.invocation_id:
            raise Exception("Cannot wait for results, invocation ID is not set.")
        # TODO: Consider adding optional polling with status updates for long workflows
        self.galaxy_instance.invocations.wait_for_invocation(self.invocation_id)


    def get_state(self) -> InvocationStatus:
        """Returns the current state of the workflow invocation."""
        if not self.invocation_id or self.status.state in [WorkState.FINISHED, WorkState.ERROR, WorkState.CANCELLED]:
            return self.status

        try:
            invocation_details = self.galaxy_instance.invocations.show_invocation(self.invocation_id)
            self.status.state = self._map_galaxy_state_to_workstate(invocation_details['state'])
            if self.status.state == WorkState.ERROR and not self.status.error_msg:
                 self.status.error_msg = f"Invocation failed. State: {invocation_details['state']}"
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
                 self.outputs_data = self.galaxy_instance.invocations.show_invocation(self.invocation_id)
             except Exception as e:
                 raise Exception(f"Failed to fetch invocation details for results processing: {e}")

        outputs = Outputs()
        try:
            if 'outputs' in self.outputs_data:
                 for output_name, dataset_info in self.outputs_data['outputs'].items():
                     if dataset_info and 'id' in dataset_info and 'src' in dataset_info and dataset_info['src'] == 'hda':
                         d = Dataset(output_name)
                         d.id = dataset_info['id']
                         d.store = self.store
                         outputs.add_output(d)

            if 'output_collections' in self.outputs_data:
                 for output_name, collection_info in self.outputs_data['output_collections'].items():
                     if collection_info and 'id' in collection_info and 'src' in collection_info and collection_info['src'] == 'hdca':
                         dc = DatasetCollection(output_name)
                         dc.id = collection_info['id']
                         dc.store = self.store
                         outputs.add_output(dc)

            return outputs

        except Exception as e:
            raise Exception(f"Error processing invocation results: {e}")


    def cancel(self) -> bool:
        """Cancels the workflow invocation."""
        if not self.invocation_id or self.status.state in [WorkState.FINISHED, WorkState.ERROR, WorkState.CANCELLED]:
            return False

        try:
            success = self.galaxy_instance.invocations.cancel_invocation(self.invocation_id)
            if success:
                self.status.state = WorkState.CANCELLED
                self.status.error_msg = "Invocation cancelled by user."
            return success
        except Exception as e:
            print(f"Error cancelling invocation {self.invocation_id}: {e}")
            return False

    def get_invocation_id(self) -> Optional[str]:
        """Returns the Galaxy invocation ID."""
        return self.invocation_id


class Workflow(AbstractWork):
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

    def run(self, data_store: "Datastore", params: Optional[Parameters] = None, wait: bool = True) -> Optional[Outputs]:
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
