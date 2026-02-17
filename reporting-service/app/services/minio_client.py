from minio import Minio
from app.core.config import settings
import io
import logging
from datetime import timedelta

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

    def upload_bytes(self, object_name: str, data: bytes, content_type: str = "application/octet-stream"):
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                
            stream = io.BytesIO(data)
            self.client.put_object(
                self.bucket, 
                object_name, 
                stream, 
                length=len(data),
                content_type=content_type
            )
            return True
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    def generate_presigned_url(self, object_name: str):
        try:
            return self.client.get_presigned_url(
                "GET",
                self.bucket,
                object_name,
                expires=timedelta(hours=2)
            )
        except Exception as e:
            logger.error(f"Presigned URL generation failed: {e}")
            return None

minio_service = MinioClient()
