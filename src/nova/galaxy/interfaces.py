"""Abstract interfaces and type definitions."""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from nova.galaxy.data_store import Datastore
from nova.galaxy.parameters import Parameters
from nova.galaxy.tool import Tool


class BasicTool(ABC):
    """Base tool class.

    Provides methods required for tool runner to handle the tool execution.
    """

    def __init__(self) -> None:
        self.store: Datastore

    def set_store(self, store: Datastore) -> None:
        """Set datastore for the tool."""
        self.store = store

    @abstractmethod
    def prepare_tool(self) -> Tuple[Tool, Optional[Parameters]]:
        """Prepare tool to run."""
        raise Exception("Please implement in a concrete class")

    @abstractmethod
    def get_results(self, tool: Tool) -> bytes:
        """Get tool results as bytes."""
        raise Exception("Please implement in a concrete class")

    def validate_for_run(self) -> None:
        """Validate tool inputs."""
        return
