"""Tests for datasets."""

from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.datasets import DatasetClient

from nova.galaxy.connection import Connection
from nova.galaxy.dataset import Dataset, DatasetCollection

# If test fails, this file may be moved or no longer exists.
REMOTE_FILE_PATH = "/HFIR/CG3/shared/Cycle509/IntermediateConfigNiQ_RC509.txt"


def test_dataset_upload(nova_instance: Connection) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        # [create dataset]
        dataset = Dataset("tests/test_files/test_text_file.txt")
        dataset.upload(store)
        # [create dataset complete]
        assert dataset.get_content() is not None


def test_dataset_set_content_upload(nova_instance: Connection) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        data = Dataset()
        # File type is optional
        # [set dataset content]
        data.set_content(content="this is some content, that I'm setting", file_type=".txt")
        # [set dataset content complete]
        data.upload(store)
        # [get content]
        content = data.get_content()
        # [get content complete]
        assert content is not None


def test_remote_file_ingest(nova_instance: Connection, galaxy_instance: GalaxyInstance) -> None:
    with nova_instance.connect() as connection:
        store = connection.get_data_store(name="nova_galaxy_testing")
        store.mark_for_cleanup()
        # [create remote dataset]
        data = Dataset(path=REMOTE_FILE_PATH, remote_file=True)
        # [create remote dataset complete]
        data.upload(store=store)
        dataset_client = DatasetClient(galaxy_instance)
        dataset_upstream = dataset_client.show_dataset(dataset_id=data.id)
        assert dataset_upstream is not None


def test_dataset_collection_upload(nova_instance: Connection) -> None:
    # TODO: Dataset collection uploading needs to be implemented
    # [create dataset collection]
    my_collection = DatasetCollection("path/to/my/collection")
    # [create dataset collection complete]
    assert my_collection is not None
