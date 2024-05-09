import io
from datetime import datetime
from google.cloud import storage

from mozmlops.cloud_storage_api_client import CloudStorageAPIClient

import pytest

import google.cloud.storage  # type: ignore[import]

from cloud_storage_mocker import BlobMetadata, Mount
from cloud_storage_mocker import patch as gcs_patch

import pathlib
def test_store__stores_file_on_gcs(tmp_path: pathlib.Path) -> None:
    # Mounts directories. Empty list is allowed if no actual access is required.
    with gcs_patch(
        [
            Mount("testbucket", tmp_path / "src", readable=True, writable=True),
        ],
    ):
        storage_client = CloudStorageAPIClient(project_name="testproject", bucket_name="testbucket")

        string_to_store = "Ada Lovelace"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename_to_store_it_at = f"first_computer_programmer_{timestamp}.txt"
        encoded_string = string_to_store.encode(encoding='utf-8')

        filepath = storage_client.store(data=encoded_string, storage_path=filename_to_store_it_at)
        assert filepath == filename_to_store_it_at

        mock_client = google.cloud.storage.Client()
        blob = mock_client.bucket("testbucket").blob(filename_to_store_it_at)
        assert blob.download_as_text() == string_to_store

def test_fetch__gets_file_off_gcs(tmp_path: pathlib.Path) -> None:
    # Mounts directories. Empty list is allowed if no actual access is required.
    with gcs_patch(
        [
            Mount("testbucket", tmp_path / "src", readable=True, writable=True),
        ],
    ):
        storage_client = CloudStorageAPIClient(project_name="testproject", bucket_name="testbucket")

        string_to_store = "Ada Lovelace"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename_to_store_it_at = f"first_computer_programmer_{timestamp}.txt"
        encoded_string = string_to_store.encode(encoding='utf-8')


        mock_client = google.cloud.storage.Client()
        blob = mock_client.bucket("testbucket").blob(filename_to_store_it_at)
        with io.BytesIO(encoded_string) as data:
            blob.upload_from_file(data)

        storage_client.fetch(remote_path=filename_to_store_it_at, local_path=tmp_path / filename_to_store_it_at)
        assert (tmp_path / filename_to_store_it_at).read_text() == string_to_store



