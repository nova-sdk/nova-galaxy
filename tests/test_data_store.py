"""Tests for data stores."""

from typing import Optional

from bioblend.galaxy import GalaxyInstance
from nova.common.job import WorkState

from nova.galaxy.connection import Connection
from nova.galaxy.tool import Tool

TEST_INT_TOOL_ID = "interactive_tool_jupyter_notebook"


def test_no_persist_store(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    # [create new datastore]
    with nova_instance.connect() as connection:
        store = connection.create_data_store(name="nova_galaxy_testing")
        # [create new datastore complete]
        store.mark_for_cleanup()
        # [mark for cleanup complete]
        history = galaxy_instance.histories.get_histories(name=store.name)
        assert len(history) > 0
    history = galaxy_instance.histories.get_histories(name=store.history_id, deleted=False)
    assert len(history) < 1


def test_persist_store(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.persist()
        history = galaxy_instance.histories.get_histories(name=store.name)
        assert len(history) > 0
    history = galaxy_instance.histories.get_histories(name=store.name, deleted=False)
    assert len(history) > 0
    # TODO: Can maybe do global cleanup
    galaxy_instance.histories.delete_history(history_id=history[0]["id"], purge=True)


def test_manual_cleanup_store(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        history = galaxy_instance.histories.get_histories(name=store.name)
        assert len(history) > 0
        store.cleanup()
    history = galaxy_instance.histories.get_histories(name=store.history_id, deleted=False)
    assert len(history) < 1


def test_manual_connection_close(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    # [manual connection start]
    connection = nova_instance.connect()
    store = connection.get_data_store(name="nova_galaxy_testing")
    store.mark_for_cleanup()
    # [manual connection complete]
    history = galaxy_instance.histories.get_histories(name=store.name)
    assert len(history) > 0
    assert connection.datastores is not None
    connection.close()
    assert len(connection.datastores) == 0
    history = galaxy_instance.histories.get_histories(name=store.history_id, deleted=False)
    assert len(history) < 1


def test_recover_tools(nova_instance: Connection) -> None:
    first_id: Optional[str] = ""
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.persist()
        test_tool = Tool(TEST_INT_TOOL_ID)
        test_tool.run_interactive(data_store=store)
        first_id = test_tool.get_uid()

    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        tools = store.recover_tools()
        assert len(tools) > 0
        assert tools[0].get_url() is not None
        assert tools[0].get_status() == WorkState.RUNNING
        assert first_id == tools[0].get_uid()
