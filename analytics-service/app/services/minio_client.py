from minio import Minio
from app.core.config import settings
import io
import logging

logger = logging.getLogger("minio-client")

class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = "factoryops"
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            logger.error(f"Error checking MinIO bucket: {e}")

    def upload_file(self, object_name: str, file_path: str):
        self.client.fput_object(self.bucket, object_name, file_path)

    def upload_bytes(self, object_name: str, data: bytes):
        try:
            stream = io.BytesIO(data)
            self.client.put_object(
                self.bucket, 
                object_name, 
                stream, 
                length=len(data),
                content_type="application/octet-stream"
            )
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False
            
    def download_file(self, object_name: str, file_path: str):
        self.client.fget_object(self.bucket, object_name, file_path)

minio_service = MinioClient()
