import io
import logging
import sys

from pathlib import Path

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class ArtifactStore:
    def __init__(self, project_name: str, bucket_name: str):
        self.gcs_project_name = project_name
        self.gcs_bucket_name = bucket_name

    def _get_storage_path(self, flow_name: str, run_id: str, file_name: str) -> str:
        return f"{flow_name}/{run_id}/{file_name}"

    def store(self, data: bytes, storage_path: str) -> str:
        from google.cloud import storage

        client = storage.Client(project=self.gcs_project_name)
        bucket = client.get_bucket(self.gcs_bucket_name)

        blob = bucket.blob(storage_path)

        with io.BytesIO(data) as f:
            # TODO: Catch exceptions and report back.

            # Google recommends setting `if_generation_match=0` if the
            # object is expected to be new. We don't expect collisions,
            # so setting this to 0 seems good.
            blob.upload_from_file(f, if_generation_match=0)
            logging.info(f"The model is stored at {storage_path}")

    def fetch(self, remote_path: str, local_path: str) -> str:
        from google.cloud import storage

        client = storage.Client(project=self.gcs_project_name)
        bucket = client.get_bucket(self.gcs_bucket_name)

        blob = bucket.blob(remote_path)

        # Create any directory that's needed.
        p = Path(local_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        blob.download_to_filename(local_path)

    def store_flow_data(self, data: bytes, filename: str) -> str:
        from metaflow import current

        deployment_path = self._get_storage_path(
            current.flow_name, current.run_id, filename
        )

        self.store(data, deployment_path)

        return deployment_path

    def fetch_flow_data(self, flow_name: str, run_id: str, file_name: str) -> str:
        from google.cloud import storage

        path = self._get_storage_path(
            flow_name=flow_name, run_id=run_id, file_name=file_name
        )

        self.fetch(remote_path=path, local_path=path)

        return path
