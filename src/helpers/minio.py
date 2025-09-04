from minio import Minio
from minio.error import S3Error
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from loggers.logapp import logger
from configs import settings



# config MinIO
MINIO_ENDPOINT = settings.MINIO_ENDPOINT
ACCESS_KEY = settings.ACCESS_KEY
SECRET_KEY = settings.SECRET_KEY
BUCKET_NAME = settings.BUCKET_NAME
SECURE = False
# initial client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=SECURE
)
