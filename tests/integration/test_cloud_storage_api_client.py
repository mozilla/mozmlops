import os
import pytest

from datetime import datetime

from mozmlops.cloud_storage_api_client import CloudStorageAPIClient

def test_store_fetch_delete__nominal():
    """
    Test the integration to store a file, fetch a file, and delete a file. 
    This test takes several seconds to run. Exclude integration tests except before release with the command:
    `pytest --ignore=tests/integration`

    If this test fails, one of the integrations is broken. 
    Each has its own assertions and error messages, designed to help pinpoint the failure.
    You can also visit the bucket on GCS to find the file:

    https://console.cloud.google.com/storage/browser/mozdata-tmp

    These functions are tested together as a top-level integration test because: 
    
    1. .store() and .fetch() are inverse operations, and then .delete() cleans up after .store()
    2. Testing these functions separately requires independently recreating the integrations,
    3. Which duplicates the logic while failing to actually isolate the integration behaviors.
    """
    # Given an artifact store and a file containing Ada Lovelace's name:

    storage_client = CloudStorageAPIClient(project_name="mozdata", bucket_name="mozdata-tmp")

    string_to_store = "Ada Lovelace"
    identifier = os.getlogin() if os.getlogin() else "anonymous"
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename_to_store_it_at = f"first_computer_programmer_{identifier}_{timestamp}.txt"
    encoded_string = string_to_store.encode(encoding='utf-8')

    # When we use .store() to call for her name to be stored on GCS, the command succeeds: 

    log_line = storage_client.store(data=encoded_string, storage_path=filename_to_store_it_at)
    assert log_line == f"The model is stored at {filename_to_store_it_at}", "The model was not stored as we expect."

    # And when we use .fetch() to call for the file to be fetched from GCS, we can retrieve her name:

    try:
        storage_client.fetch(remote_path=filename_to_store_it_at, local_path=filename_to_store_it_at)

        with open(filename_to_store_it_at, "rb") as file:
            encoded_stored_string = file.read()
            decoded_stored_string = encoded_stored_string.decode(encoding='utf-8')
            assert decoded_stored_string == string_to_store, "The model was not fetched as we expect."

    # And when we use .delete() to call for the file to be deleted, provided it's possible that our file _uploaded_, we can delete it: 
    # (Lives in a finally block so the file is cleaned up even if fetching fails)
    finally: 
        storage_client._CloudStorageAPIClient__delete(filename_to_store_it_at)

        try:
            # This line assumes fetch is working (which we believe we're testing for above)
            storage_client.fetch(remote_path=filename_to_store_it_at, local_path=filename_to_store_it_at)
            
            pytest.fail("The model was not deleted as we expect; it's still on the GCS file system.")
        except Exception as e:
            assert "No such object" in e.message

        finally:
            # Removes local file, in the event that fetch succeeded
            os.remove(filename_to_store_it_at)

def test_store__existing_filename__throws_clear_exception():
    """
    Tests that, if we try to store a file in GCS when there's already a file of that name, we get an exception that clearly explains what happened.

    I added this test because this happened to me while writing another test, and I found the GCS error message cryptic.
    """
    # Given an artifact store and a file containing Grace Hopper's name:

    storage_client = CloudStorageAPIClient(project_name="mozdata", bucket_name="mozdata-tmp")

    string_to_store = "Grace Hopper"
    identifier = os.getlogin() if os.getlogin() else "anonymous"
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename_to_store_it_at = f"coined_the_term_bug_{identifier}_{timestamp}.txt"
    encoded_string = string_to_store.encode(encoding='utf-8')

    # After we call .store() for that object and location once: 

    log_line = storage_client.store(data=encoded_string, storage_path=filename_to_store_it_at)
    assert log_line == f"The model is stored at {filename_to_store_it_at}"

    # When we do it again: 

    try:
        storage_client.store(data=encoded_string, storage_path=filename_to_store_it_at)
        pytest.fail("Trying to store a file at an existing filename in GCS has historically raised an exception, and just now it didn't.")
    
    # We get an exception indicating that we have already stored this object at this location.
    
    except Exception as e:
        assert "The object you tried to upload is already in the GCS bucket." in str(e), "Uploading existing file no longer produces the exception we expect."
