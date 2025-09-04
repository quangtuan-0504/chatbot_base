from io import BytesIO
import base64
import os
from minio import Minio
from minio.error import S3Error
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from loggers.logapp import logger

def check_minio_connection(minio_client: Minio):
    try:
        minio_client.list_buckets()
        logger.info("MinIO connection successful.")
        return True
    except S3Error as err:
        logger.error(f"MinIO connection failed: {err}")
        return False

def ensure_bucket_exists(minio_client: Minio, bucket_name: str):
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' created.")
        else:
            logger.info(f"Bucket '{bucket_name}' exists.")
    except S3Error as err:
        logger.error(f"Error creating bucket: {err}")

def get_file_from_minio(minio_client: Minio, bucket_name: str ,object_name: str, return_type: str = "BytesIO"):
    """
    get file MinIO and return BytesIO object.
    """
    try:
        response = minio_client.get_object(
            bucket_name=bucket_name,
            object_name=object_name
        )
        # read data file
        file_data = response.read()
        if return_type == "BytesIO":
            # read data into BytesIO
            file_data = BytesIO(file_data)
            return file_data
        elif return_type == "base64":
            # convert to base64
            base64_encoded = base64.b64encode(file_data).decode('utf-8')
            return base64_encoded
    except S3Error as err:
        logger.error(f"Error fetching file from MinIO: {err}")
        raise
    finally:
        response.close()
        response.release_conn()
def download_file_from_minio(minio_client: Minio, bucket_name: str, object_name: str, local_file_path: str):
    """
    Download file from MinIO to local.
    - object_name: file path in MinIO (VD: 'documents/sample.pdf')
    - local_file_path: file path in local (VD: 'downloads/sample_1.pdf')
    """
    try:
        # create directory if not exists
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

        # download file from bucket
        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name= object_name,
            file_path= local_file_path # local_file_path is a relative path like xxx/file_name.pdf
            # So it knows which directory to save the file to. then it will determine the current directory, the current directory
            # is the directory where we are running the code in the terminal, here is ~/test_chatbot/chatbot.
            # such file will be saved to ~/test_chatbot/chatbot/xxx/file_name.pdf
        )
        # logger.info(f"Downloaded '{object_name}' to '{local_file_path}'.")
        return local_file_path
    except S3Error as err:
        logger.error(f"Error downloading file: {err}")
        return False
 