#test_minio.py
from minio import Minio
from minio.error import S3Error
import os
import logging
from minio.deleteobjects import DeleteObject


# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cấu hình MinIO
MINIO_ENDPOINT = "10.18.27.59:9000"
ACCESS_KEY = "U2K9iOhAOEIARj0d"
SECRET_KEY = "xaD6SYqCmJ3uUu247lbmR1bB0Q8LC5wj"
BUCKET_NAME = "tuan"
SECURE = False

# Khởi tạo client
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
            logger.info(f"Bucket '{BUCKET_NAME}' created.")
        else:
            logger.info(f"Bucket '{BUCKET_NAME}' exists.")
    except S3Error as err:
        logger.error(f"Error creating bucket: {err}")

def upload_file(local_file_path, object_name=None):
    """
    Tải file lên MinIO.
    - local_file_path: Đường dẫn file cục bộ (VD: 'docs/sample.docx')
    - object_name: Đường dẫn file trên MinIO (VD: 'pdfs/sample.pdf'). Nếu None, giữ nguyên tên file gốc.
    """
    try:
        # Nếu không chỉ định object_name, dùng tên file gốc
        if object_name is None:
            object_name = os.path.basename(local_file_path)

        # Kiểm tra file tồn tại
        if not os.path.exists(local_file_path):
            logger.error(f"File {local_file_path} does not exist.")
            return False
        # Tải file lên bucket
        minio_client.fput_object(
            bucket_name=BUCKET_NAME, 
            object_name=object_name, 
            file_path=local_file_path
        )
        logger.info(f"Uploaded '{local_file_path}' to '{BUCKET_NAME}/{object_name}'.")
        return True
    except S3Error as err:
        logger.error(f"Error uploading file: {err}")
        return False

def download_file(object_name, local_file_path):
    """
    Tải file từ MinIO về máy.
    - object_name: Đường dẫn file trên MinIO (VD: 'documents/sample.pdf')
    - local_file_path: Đường dẫn lưu file cục bộ (VD: 'downloads/sample_1.pdf')
    """
    try:
        # Tạo thư mục đích nếu chưa tồn tại
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

        # Tải file từ bucket
        minio_client.fget_object(
            bucket_name=BUCKET_NAME,
            object_name= object_name,
            file_path= local_file_path
        )
        logger.info(f"Downloaded '{object_name}' to '{local_file_path}'.")
        return True
    except S3Error as err:
        logger.error(f"Error downloading file: {err}")
        return False

# def extract_text(file_path):
#     try:
#         suffix = Path(file_path).suffix.lower()
#         if suffix == ".docx":
#             doc = docx.Document(file_path)
#             return " ".join([para.text for para in doc.paragraphs])
#         elif suffix == ".pdf":
#             with open(file_path, "rb") as f:
#                 pdf = PyPDF2.PdfReader(f)
#                 return " ".join([pdf.pages[i].extract_text() for i in range(len(pdf.pages))])
#         return ""
#     except Exception as e:
#         logger.error(f"Error extracting text from {file_path}: {e}")
#         return ""

# def upload_and_index(local_file_path, object_name=None):
#     if upload_file(local_file_path, object_name):
#         text = extract_text(local_file_path)
#         if text:
#             logger.info(f"Extracted text: {text[:100]}...")
#             # TODO: Tích hợp với Milvus nếu cần
#         else:
#             logger.warning("No text extracted.")
#     else:
#         logger.error("Upload failed.")
def get_list_file():
    objects = minio_client.list_objects(bucket_name=BUCKET_NAME, prefix="chatbot_resources/images/68009fdb1f23a65929a13249/68009fef1f23a65929a1324a/", recursive=True)
    # print(objects)
    # for obj in objects: # Duyệt 1 lần rồi lần sau duyệt lại sẽ rỗng
    #     print(obj.object_name)
    delete_objects = [DeleteObject(obj.object_name) for obj in objects]
    print(delete_objects)
    errors = minio_client.remove_objects(bucket_name=BUCKET_NAME,delete_object_list=delete_objects, bypass_governance_mode=True)
    print(f"Đã xóa file list image của  khỏi bucket {BUCKET_NAME}")
    error_count = 0
    for error in errors:
        print(f"Lỗi khi xóa {error.object_name}: {error.message}")
        error_count += 1

    if error_count == 0:
        print(f"Đã xóa {len(delete_objects)} file khỏi bucket {BUCKET_NAME}")
    else:
        print(f"Có {error_count} lỗi, xóa được {len(delete_objects) - error_count} file")
def main():

    check_minio_connection()
    ensure_bucket_exists()
    # Up load file

    
    # Ví dụ: Tải lên một file
    # upload_file("test_code/file_test/estimate_resources_sys_chatbot.docx", "collecion1/estimate_resources_sys_chatbot.docx")
    # Tải file đơn
    # upload_and_index("sample.docx", "documents/sample.docx")
    # # Tải thư mục
    # upload_directory("docs", "documents/2025/")
    # Tải file về
    # download_file("collecion1/estimate_resources_sys_chatbot.docx", "test_code/download_file_test/estimate_resources_sys_chatbot.docx")

    get_list_file()

if __name__ == "__main__":
    main()