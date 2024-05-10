# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import io
import logging
import sys

from pathlib import Path

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class CloudStorageAPIClient:
    """
    This module provides functions for interacting with Google Cloud Storage.

    Arguments:

    - project_name (str): The GCS Project name
    - bucket_name (str): The GCS Bucket name

    to which that instance will upload, and from which that instance will fetch.
    """

    def __init__(self, project_name: str, bucket_name: str):
        self.gcs_project_name = project_name
        self.gcs_bucket_name = bucket_name

    def store(self, data: bytes, storage_path: str) -> str:
        """
        Arguments:
        data (bytes): The data to be stored in the cloud.
        storage_path (str): The filepath where the data will be stored.

        Places a blob of data, represented in bytes,
        at a specific filepath within the GCS project and bucket specified
        when the CloudStorageAPIClient was initialized.
        """
        from google.cloud import storage
        from google.cloud.exceptions import GoogleCloudError

        client = storage.Client(project=self.gcs_project_name)

        # Raises an exception if the bucket name cannot be found
        bucket = client.get_bucket(self.gcs_bucket_name)

        blob = bucket.blob(storage_path)

        with io.BytesIO(data) as f:
            # TODO: Catch exceptions and report back.

            # Google recommends setting `if_generation_match=0` if the
            # object is expected to be new. We don't expect collisions,
            # so setting this to 0 seems good.
            try:
                blob.upload_from_file(f, if_generation_match=0)
                log_line = f"The model is stored at {storage_path}"
                logging.info(log_line)
            except GoogleCloudError as e:
                if e.code == 412:
                    raise Exception(
                        "The object you tried to upload is already in the GCS bucket. Currently, the .store() function's implementation dictates this behavior."
                    ).with_traceback(e.__traceback__)
                raise e

        return storage_path

    def fetch(self, remote_path: str, local_path: str) -> str:
        """
        Arguments:
        remote_path (str): The filepath on GCS from which to fetch the data.
        storage_path (str): The local filepath in which to store the data.

        Fetches a file
        at a specific remote_path within the GCS project and bucket specified
        and stores it at a location specified by local_path.
        """
        from google.cloud import storage

        client = storage.Client(project=self.gcs_project_name)
        bucket = client.get_bucket(self.gcs_bucket_name)

        blob = bucket.blob(remote_path)

        # Create any directory that's needed.
        p = Path(local_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        blob.download_to_filename(local_path)

    def __delete(self, remote_path: str) -> str:
        """
        For tests only.

        Arguments:
        remote_path (str): The filepath on GCS from which to delete the data.

        Deletes a file
        at a specific remote_path within the GCS project and bucket specified.
        """
        from google.cloud import storage

        client = storage.Client(project=self.gcs_project_name)
        bucket = client.get_bucket(self.gcs_bucket_name)

        blob = bucket.blob(remote_path)

        blob.delete()
