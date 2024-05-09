from datetime import datetime
from google.cloud import storage

from mozmlops.cloud_storage_api_client import CloudStorageAPIClient

import pytest

class MockGoogleCloudStorageClient():
    def __init__(self, **kwargs):
        self.initializer_args = kwargs
        self.call_list = [f"__init__ with {kwargs}"]

    def get_bucket(self, attr):
        return MockGoogleCloudBucket()

class MockGoogleCloudBucket():
    def blob(self, storage_path):
        return MockBlob()

class MockBlob():
    def upload_from_file(self, bytes, if_generation_match):
        return 'fake value to test that we call blob.upload_from_file'

def get_mock_storage_client(**kwargs):
    return MockGoogleCloudStorageClient(**kwargs)

def test_store__calls_gcloud(monkeypatch):
    monkeypatch.setattr(storage, 'Client', get_mock_storage_client)

    storage_client = CloudStorageAPIClient(project_name="mozdata", bucket_name="mozdata-tmp")

    string_to_store = "Ada Lovelace"
    filename_to_store_it_at = f"first_computer_programmer.txt"
    encoded_string = string_to_store.encode(encoding='utf-8')

    # When we use .store() to call for her name to be stored on GCS, the command calls google cloud the way we expect:

    bucket, blob, upload_value, call_list = storage_client.store(data=encoded_string, storage_path=filename_to_store_it_at, testing=True)
    assert isinstance(bucket, MockGoogleCloudBucket)
    assert isinstance(blob, MockBlob)
    assert upload_value == 'fake value to test that we call blob.upload_from_file'
    assert call_list == filename_to_store_it_at, "The model was not stored as we expect."
