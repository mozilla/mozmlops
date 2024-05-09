import io
import pathlib
from datetime import datetime

import google.cloud.storage  # type: ignore[import]
from cloud_storage_mocker import Mount
from cloud_storage_mocker import patch as gcs_patch
from mozmlops.cloud_storage_api_client import CloudStorageAPIClient


def test_store__stores_file_on_gcs(tmp_path: pathlib.Path) -> None:
    """
    This is a unit test that checks whether we called the GCS API
    according to the expectations of this GCS mocking library:

    https://github.com/odashi/cloud-storage-mocker

    The library does not support mocks for all GCS operations,
    and it is not maintained by the team that builds the GCS API.

    If this test fails and it's unclear why,
    run the integration tests to check our integration behavior for real
    to see if something is wrong:

    pytest -m integration
    """

    # Given the following mocked bucket
    with gcs_patch(
        [
            Mount("testbucket", tmp_path / "src", readable=True, writable=True),
        ],
    ):
        # When our API Client stores data in a file on GCS:
        storage_client = CloudStorageAPIClient(project_name="testproject", bucket_name="testbucket")

        string_to_store = "Ada Lovelace"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename_to_store_it_at = f"first_computer_programmer_{timestamp}.txt"
        encoded_string = string_to_store.encode(encoding='utf-8')

        filepath = storage_client.store(data=encoded_string, storage_path=filename_to_store_it_at)
        assert filepath == filename_to_store_it_at

        # Then we can do the steps to download the file from mock GCS:
        mock_client = google.cloud.storage.Client()
        blob = mock_client.bucket("testbucket").blob(filename_to_store_it_at)
        assert blob.download_as_text() == string_to_store

def test_fetch__gets_file_off_gcs(tmp_path: pathlib.Path) -> None:
    """
    This is a unit test that checks whether we called the GCS API
    according to the expectations of this GCS mocking library:

    https://github.com/odashi/cloud-storage-mocker

    The library does not support mocks for all GCS operations,
    and it is not maintained by the team that builds the GCS API.

    If this test fails and it's unclear why,
    run the integration tests to check our integration behavior for real
    to see if something is wrong:

    pytest -m integration
    """

    # Given the following mocked bucket
    with gcs_patch(
        [
            Mount("testbucket", tmp_path / "src", readable=True, writable=True),
        ],
    ):
        # When we do the steps to upload a file to mock GCS:
        string_to_store = "Ada Lovelace"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename_to_store_it_at = f"first_computer_programmer_{timestamp}.txt"
        encoded_string = string_to_store.encode(encoding='utf-8')

        mock_client = google.cloud.storage.Client()
        blob = mock_client.bucket("testbucket").blob(filename_to_store_it_at)
        with io.BytesIO(encoded_string) as data:
            blob.upload_from_file(data)

        # Then Our API client is able to fetch them:
        storage_client = CloudStorageAPIClient(project_name="testproject", bucket_name="testbucket")
        storage_client.fetch(remote_path=filename_to_store_it_at, local_path=tmp_path / filename_to_store_it_at)
        assert (tmp_path / filename_to_store_it_at).read_text() == string_to_store



