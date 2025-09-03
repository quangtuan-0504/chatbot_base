from minio import Minio
from minio.error import S3Error
import logging
from io import BytesIO
import base64
import os

# config logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# config MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
SECURE = False
# initial client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=SECURE
)

def check_minio_connection():
    try:
        minio_client.list_buckets()
        print("MinIO connection successful.")
        return True
    except S3Error as err:
        print(f"MinIO connection failed: {err}")
        return False

def ensure_bucket_exists():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            print(f"Bucket '{BUCKET_NAME}' created.")
        else:
            print(f"Bucket '{BUCKET_NAME}' exists.")
    except S3Error as err:
        print(f"Error creating bucket: {err}")

def get_file_from_minio(object_name : str, return_type : str = "BytesIO"):
    """
    get file MinIO and return BytesIO object.
    """
    try:
        response = minio_client.get_object(
            bucket_name=BUCKET_NAME,
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
def download_file_from_minio(object_name, local_file_path):
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
            bucket_name=BUCKET_NAME,
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
 