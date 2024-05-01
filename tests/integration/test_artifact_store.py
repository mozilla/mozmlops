import os

from datetime import datetime

from mozmlops.artifact_store import ArtifactStore

def test_store_fetch_delete__nominal():
    """
    Test the integration to store a file, fetch a file, and delete a file. 
    This test takes several seconds to run. Exclude integration tests except before release with the command:
    `pytest --ignore=tests/integration`

    If this test fails, one of the integrations is broken. 
    Each has its own assertions, which should help pinpoint the failure.
    You can also visit the bucket on GCS to find the file:

    https://console.cloud.google.com/storage/browser/mozdata-tmp

    These functions are tested together as a top-level integration test because: 
    
    1. .store() and .fetch() are inverse operations, and then .delete() cleans up after .store()
    2. What we're testng here, largely, is that Google Cloud API is doing what we expect. We're doing this on the assumption that there's a mozdata-tmp bucket in a mozdata project. If this test fails, the API and the bucket assumpton are the prime suspects.
    3. Testing these functions separately requires independently recreating the integrations implemented in the functions themselves,
    4. And doing #3 depends on the functionality inventoried in #2, so is no less brittle than calling the functions themselves, and produces logic duplication.
    6. Finally, both fetching and deleting a file requres the file to be there, which we accomplish by calling .store(). Putting them in the same test guarantees .store() being called to test before .fetch() or .delete().
    """
    # Given an artifact store and a file containing Ada Lovelace's name:

    artifact_store = ArtifactStore(project_name="mozdata", bucket_name="mozdata-tmp")

    string_to_store = "Ada Lovelace"
    identifier = os.getlogin() if os.getlogin() else "anonymous"
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename_to_store_it_at = f"first_computer_programmer_{identifier}_{timestamp}.txt"
    encoded_string = string_to_store.encode(encoding='utf-8')

    # When we use .store() to call for her name to be stored on GCS, the command succeeds: 

    log_line = artifact_store.store(data=encoded_string, storage_path=filename_to_store_it_at)
    assert log_line == f"The model is stored at {filename_to_store_it_at}"

    # And when we use .fetch() to call for the file to be fetched from GCS, we can retrieve her name:

    try:
        artifact_store.fetch(remote_path=filename_to_store_it_at, local_path=filename_to_store_it_at)

        with open(filename_to_store_it_at, "rb") as file:
            encoded_stored_string = file.read()
            decoded_stored_string = encoded_stored_string.decode(encoding='utf-8')
            assert decoded_stored_string == string_to_store

    # And when we use .delete() to call for the file to be deleted, provided it's possible that our file _uploaded_, we can delete it: 
    # (Lives in a finally block so the file is cleaned up even if fetching fails)
    finally: 
        # No assertion here because .delete() should throw its own exception if the file cannot be deleted.
        artifact_store.delete(filename_to_store_it_at)

        # Removes local file, in the event that fetch succeeded
        os.remove(filename_to_store_it_at)