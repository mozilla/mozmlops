# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import io
import logging
import sys

from pathlib import Path

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class ClarifyingException(Exception):
    def __init__(self, message):            
        self.message = message
    
class ArtifactStore:
    """
    This module provides functions for interacting with Google Cloud Storage.

    An instance of this class needs: 

    - The GCS Project name
    - The GCS Bucket name

    to which that instance will upload, and from which that instance will fetch.
    """
    def __init__(self, project_name: str, bucket_name: str):
        self.gcs_project_name = project_name
        self.gcs_bucket_name = bucket_name
    

    def _get_storage_path(self, flow_name: str, run_id: str, file_name: str) -> str:
        """
        PRIVATE FUNCTION

        Assembles the paths to be uploaded to GCS. 
        """
        return f"{flow_name}/{run_id}/{file_name}"

    def store(self, data: bytes, storage_path: str) -> str:
        """
        Places a blob of data, represented in bytes, 
        at a specific filepath within the GCS project and bucket specified
        when the ArtifactStore was initialized. 
        """
        from google.cloud import storage

        client = storage.Client(project=self.gcs_project_name)
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
            except Exception as e:
                if "" in e.message:
                    raise ClarifyingException("The object you tried to upload is already in the GCS bucket. Currently, the .store() function's implementation dictates this behavior.")

        return log_line

    def fetch(self, remote_path: str, local_path: str) -> str:
        """
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

    def delete(self, remote_path: str) -> str: 
        """
        Deletes a file
        at a specific remote_path within the GCS project and bucket specified.
        """
        from google.cloud import storage

        client = storage.Client(project=self.gcs_project_name)
        bucket = client.get_bucket(self.gcs_bucket_name)

        blob = bucket.blob(remote_path)

        blob.delete()

    def store_flow_data(self, data: bytes, filename: str) -> str:
        """
        Uses this class's public `store` function
        To store continuous checkpoints during model training
        orchestrated by a Metaflow flow.
        """
        from metaflow import current

        deployment_path = self._get_storage_path(
            current.flow_name, current.run_id, filename
        )

        self.store(data, deployment_path)

        return deployment_path

    def fetch_flow_data(self, flow_name: str, run_id: str, file_name: str) -> str:
        """
        Uses this class's public `fetch` function
        To fetch artifacts stored on GCS
        from a prior run of a Metaflow flow.
        """

        from google.cloud import storage

        path = self._get_storage_path(
            flow_name=flow_name, run_id=run_id, file_name=file_name
        )

        self.fetch(remote_path=path, local_path=path)

        return path
