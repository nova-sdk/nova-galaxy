"""The NOVA class is responsible for managing interactions with a Galaxy server instance."""

from typing import Any, List
from urllib.parse import urlparse

from bioblend import galaxy
from deprecated import deprecated
from requests import head

from .data_store import Datastore
from .tool import stop_all_tools_in_store

_global_connections: List = []


def global_cleanup(*args: Any, **kwargs: Any) -> None:
    """Stop all tools in all data stores."""
    global _global_connections
    for conn in _global_connections.copy():
        conn.close(force_stop=True)
    _global_connections = []


def global_get_running_tools(*args: Any, **kwargs: Any) -> List:
    """Get all running tools in all data stores."""
    global _global_connections
    tools: List = []
    for conn in _global_connections:
        for store in conn.datastores:
            tools += store.recover_tools()
    return tools


class GalaxyConnectionError(Exception):
    """Exception raised for errors in the connection.

    Attributes
    ----------
        message (str): Explanation of the error.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ConnectionHelper:
    """Manages datastore for current connection.

    Should not be instantiated manually. Use Connection.connect() instead. Any stores created using the connection will
    be persisted after connection is closed, unless Datastore.mark_for_cleanup() is called for that store.
    """

    def __init__(self, galaxy_instance: galaxy.GalaxyInstance, galaxy_url: str):
        self.galaxy_instance = galaxy_instance
        self.galaxy_url = galaxy_url
        self.datastores: List[Datastore] = []

    def __enter__(self) -> Any:
        """Enter method for use with "with" keyword."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit method for use with "with" keyword."""
        self.close()

    @deprecated(version="0.8.0", reason="Should use `get_data_store() instead.")
    def create_data_store(self, name: str) -> Datastore:
        """DEPRECATED. Creates a datastore with the given name or returns an existing data store with that name.

        Parameters
        ----------
        name: str
            Name of the data store.
        """
        return self.get_data_store(name=name, create=True)

    def get_data_store(self, name: str, create: bool = True) -> Datastore:
        """Fetches a datastore with the given name.

        Parameters
        ----------
        name: str
            Name of the data store.
        create: bool
            If true, creates a data store if one does not exist with the specified name.

        Returns
        -------
        Datastore
            Returns the specified or newly created data store.
        """
        histories = self.galaxy_instance.histories.get_histories(name=name)
        if len(histories) > 0:
            store = Datastore(name, self, histories[0]["id"])
            self.datastores.append(store)
            return store
        if create:
            history_id = self.galaxy_instance.histories.create_history(name=name)["id"]
            store = Datastore(name, self, history_id)
            self.datastores.append(store)
            return store
        else:
            raise Exception("Data store does not exist and auto creation is set to false.")

    def remove_data_store(self, store: Datastore) -> None:
        """Permanently deletes the data store with the given name.

        Parameters
        ----------
        store: Datastore
            The data store to remove from this connection.
        """
        if not store.persist_store:
            store.cleanup()
        self.datastores.remove(store)

    def close(self, force_stop: bool = False) -> None:
        """Closes the connection and stops all jobs in non-persisted data stores.

        Parameters
        ----------
        force_stop: bool
            Force data stores to stop currently running jobs even persisted stores. Will not delete persisted stores.

        """
        global _global_connections
        # Remove all data stores after execution
        for store in self.datastores:
            if not store.persist_store or force_stop:
                stop_all_tools_in_store(store)
                self.remove_data_store(store)
        _global_connections.remove(self)


class Connection:
    """
    Class to manage a connection to the NDIP platform.

    Attributes
    ----------
        galaxy_url (str): URL of the Galaxy instance.
        galaxy_api_key (str): API key for the Galaxy instance.
    """

    def __init__(
        self,
        galaxy_url: str,
        galaxy_key: str,
    ) -> None:
        """
        Initializes the Connection instance with the provided URL and API key.

        Args:
            galaxy_url str: URL of the Galaxy instance.
            galaxy_key str: API key for the Galaxy instance.
        """
        # Check for redirects on the URL and follow them to the final Galaxy URL.
        response = head(galaxy_url, allow_redirects=True)
        resolved_url = response.url
        parsed_url = urlparse(resolved_url)
        new_galaxy_url = f"{parsed_url.scheme}://{parsed_url.hostname}"

        self.galaxy_url = new_galaxy_url
        self.galaxy_api_key = galaxy_key
        self.galaxy_instance: galaxy.GalaxyInstance

    def _init_galaxy_instance(self) -> None:
        if not self.galaxy_url or not self.galaxy_api_key:
            raise ValueError("Galaxy URL and API key must be provided.")
        if not isinstance(self.galaxy_url, str):
            raise ValueError("Galaxy URL must be a string")
        self.galaxy_instance = galaxy.GalaxyInstance(url=self.galaxy_url, key=self.galaxy_api_key)
        self.galaxy_instance.config.get_version()

    def connect(self) -> ConnectionHelper:
        """
        Connects to the Galaxy instance using the provided URL and API key.

        Raises a ValueError if the URL or API key is not provided.

        Raises
        ------
            ValueError: If the Galaxy URL or API key is not provided.
        """
        global _global_connections
        self._init_galaxy_instance()
        conn = ConnectionHelper(self.galaxy_instance, self.galaxy_url)
        _global_connections.append(conn)
        return conn
