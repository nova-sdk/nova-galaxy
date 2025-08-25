"""Parameters are input values for Galaxy tools and workflows."""

from typing import Any, Dict

from .dataset import Dataset, DatasetCollection


class Parameters:
    """Specialized map wrapper used as an input to a Galaxy tool."""

    def __init__(self) -> None:
        self.inputs: Dict[str, Any] = {}

    def add_input(self, name: str, value: Any) -> None:
        self.inputs[name] = value

    def change_input_value(self, name: str, new_value: Any) -> None:
        if self.inputs[name]:
            self.inputs[name] = new_value

    def remove_input(self, name: str) -> None:
        self.inputs.pop(name)


class WorkflowParameters:
    """Handles workflow parameters using explicit bioblend-style approach."""

    def __init__(self) -> None:
        self.workflow_inputs: Dict[str, Any] = {}
        self.step_params: Dict[str, Dict[str, Any]] = {}

    def add_workflow_input(self, input_id: str, value: Any) -> None:
        """Add a workflow-level input.

        Parameters
        ----------
        input_id : str
            The workflow input ID (e.g., "0", "1")
        value : Any
            The input value (Dataset, DatasetCollection, or simple value)
        """
        if isinstance(value, Dataset):
            if not value.id:
                raise ValueError(f"Dataset for workflow input '{input_id}' must have an ID")
            self.workflow_inputs[input_id] = {"src": "hda", "id": value.id}
        elif isinstance(value, DatasetCollection):
            if not value.id:
                raise ValueError(f"DatasetCollection for workflow input '{input_id}' must have an ID")
            self.workflow_inputs[input_id] = {"src": "hdca", "id": value.id}
        else:
            # Simple values (strings, booleans, etc.)
            self.workflow_inputs[input_id] = value

    def add_step_param(self, step_id: str, param_path: str, value: Any) -> None:
        """Add a step-level parameter.

        Parameters
        ----------
        step_id : str
            The workflow step ID (e.g., "2", "4")
        param_path : str
            The parameter path within the step (e.g., "input", "series_0|input_mode|export_folder")
        value : Any
            The parameter value
        """
        if step_id not in self.step_params:
            self.step_params[step_id] = {}

        if isinstance(value, list):
            # Handle list of datasets
            param_list = []
            for item in value:
                if isinstance(item, Dataset):
                    if not item.id:
                        raise ValueError(f"Dataset for step {step_id} parameter {param_path} must have an ID")
                    param_list.append({"src": "hda", "id": item.id})
                elif isinstance(item, DatasetCollection):
                    if not item.id:
                        raise ValueError(f"DatasetCollection for step {step_id}'parameter {param_path} must have an ID")
                    param_list.append({"src": "hdca", "id": item.id})
                else:
                    param_list.append(item)
            self.step_params[step_id][param_path] = param_list
        elif isinstance(value, Dataset):
            if not value.id:
                raise ValueError(f"Dataset for step '{step_id}' parameter '{param_path}' must have an ID")
            self.step_params[step_id][param_path] = {"src": "hda", "id": value.id}
        elif isinstance(value, DatasetCollection):
            if not value.id:
                raise ValueError(f"DatasetCollection for step '{step_id}' parameter '{param_path}' must have an ID")
            self.step_params[step_id][param_path] = {"src": "hdca", "id": value.id}
        else:
            # Simple values
            self.step_params[step_id][param_path] = value

    def get_bioblend_inputs(self) -> Dict[str, Any]:
        """Get the workflow inputs in bioblend format."""
        return self.workflow_inputs.copy()

    def get_bioblend_params(self) -> Dict[str, Dict[str, Any]]:
        """Get the step parameters in bioblend format."""
        return self.step_params.copy()
