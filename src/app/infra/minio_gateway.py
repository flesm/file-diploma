import time

from minio import Minio
from minio.error import S3Error


class MinioGateway:
    def __init__(
        self,
        endpoint: str,
        public_endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool,
    ):
        self.bucket_name = bucket_name
        public_endpoint_value = public_endpoint.replace("http://", "").replace(
            "https://", ""
        ).rstrip("/")
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region="us-east-1",
        )
        self._public_client = Minio(
            public_endpoint_value,
            access_key=access_key,
            secret_key=secret_key,
            secure=public_endpoint.startswith("https://"),
            region="us-east-1",
        )

    def ensure_bucket(self) -> None:
        last_error = None
        for _ in range(20):
            try:
                if not self._client.bucket_exists(self.bucket_name):
                    self._client.make_bucket(self.bucket_name)
                return
            except Exception as error:  # noqa: BLE001
                last_error = error
                time.sleep(1)

        if last_error:
            raise last_error

    def presign_upload(self, object_key: str, content_type: str) -> str:
        return self._public_client.presigned_put_object(
            self.bucket_name,
            object_key,
        )

    def presign_download(self, object_key: str) -> str:
        return self._public_client.presigned_get_object(
            self.bucket_name,
            object_key,
        )

    def ensure_object_exists(self, object_key: str) -> None:
        try:
            self._client.stat_object(self.bucket_name, object_key)
        except S3Error as error:
            raise ValueError("Object was not uploaded") from error
