from minio import Minio
from minio.error import S3Error
import os
from src.loggers.logapp import logger
from src.configs import settings

# config MinIO
MINIO_ENDPOINT = settings.MINIO_ENDPOINT
ACCESS_KEY = settings.ACCESS_KEY_MINIO
SECRET_KEY = settings.SECRET_KEY_MINIO
SECURE = False
# initial client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=SECURE
)
