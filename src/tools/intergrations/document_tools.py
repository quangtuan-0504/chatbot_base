import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from helpers.mongodb.get_mongodb import MongoDBConnections
from tools.rag.indexing_milvus import IndexingMilvusOri
from src.utils.timezone_utils import get_gmt7_datetime_for_db
from configs import settings
from loggers.logapp import logger
from typing import List, Dict, Any, Optional
from data_models.document_dataclass import FilesQueryRequest
from src.helpers.minio import minio_client
from bson import ObjectId
from minio.deleteobjects import DeleteObject


class DocumentTool:
    def __init__(self, mongodb: MongoDBConnections = None):
        # Initialize MongoDB connection
        self.mongodb = mongodb
        self.documents_collection = self.mongodb.DOCUMENTS

        # Create indexes for better performance
        self.documents_collection.create_index([("user_id", 1), ("collection_id", 1)])

    def create_file(
            self, 
            original_file_name: str,
            minio_stored_file_name: str, 
            file_path: str,
            user_id: str, 
            collection_id: str, 
            file_type: str,
            description: str
        ) -> Dict[str, Any]:
        """
        Create a new file record in the database
        """
        current_time = get_gmt7_datetime_for_db()        
        file_record = {
            'file_name': original_file_name,
            'minio_stored_file_name': minio_stored_file_name,
            'file_path': file_path,
            'user_id': user_id,
            'collection_id': collection_id,
            'file_type': file_type,
            'description': description,
            'status': 'pending',
            'created_at': current_time,
            'updated_at': current_time,
            'process_attempts': 0
        }

        result = self.documents_collection.insert_one(file_record)

        # Get the MongoDB _id and use it as file_id in the return value
        file_record['file_id'] = str(result.inserted_id)
        return file_record

    def get_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a file record by its ID
        """
        # Try to convert user_id to ObjectId if it's a valid MongoDB _id
        object_id = ObjectId(file_id)
        file_record = self.documents_collection.find_one({'_id': object_id})
        file_record['file_id'] = str(file_record['_id'])
        del file_record['_id']
        return file_record

    def get_files_of_collection(self, 
        query: FilesQueryRequest
    ) -> List[Dict[str, Any]]:
        """
        Get files matching the search criteria
        """

        # Xây dựng query filter
        filters = {"collection_id": query.collection_id}

        # Thêm các filter tùy chọn
        if query.file_name:
            filters["file_name"] = {"$regex": query.file_name, "$options": "i"}
        if query.file_types:
            filters["file_type"] = {"$in": query.file_types}

        if query.status:
            filters["status"] = {"$in": query.status}

        # Filter theo khoảng thời gian updated_at
        if query.created_after or query.created_before:# Current annotation is Optional[datetime] if a <=> if a!=None , thêm str vào annotation để if a <=> if a!=None and a!=""
            filters["updated_at"] = {}
            if query.created_after:
                filters["updated_at"]["$gte"] = query.created_after
            if query.created_before:
                filters["updated_at"]["$lte"] = query.created_before

        # Truy vấn MongoDB
        cursor = self.documents_collection.find(filters).sort('updated_at', -1)  
        files = list(cursor)
        # LOGGER.debug(str(files))
        # Add the _id as file_id in each record
        for file in files:
            file['file_id'] = str(file['_id'])
            del file['_id']
        return files

    def update_file_status(self, user_id: str, status: str) -> Optional[Dict[str, Any]]:
        """
        Update the status of a file
        """
        try:
            # Try to convert user_id to ObjectId if it's a valid MongoDB _id
            object_id = ObjectId(user_id)
            file_record = self.documents_collection.find_one({'_id': object_id})
            query_field = '_id'
        except:
            # If conversion fails, look for a record with this user_id
            file_record = self.documents_collection.find_one({'user_id': user_id})
            query_field = 'user_id'

        if not file_record:
            raise ValueError(f"File with ID {user_id} not found")

        update_query = {query_field: object_id if query_field == '_id' else user_id}

        self.documents_collection.update_one(
            update_query,
            {
                '$set': {
                    'status': status,
                    'updated_at': get_gmt7_datetime_for_db()
                }
            }
        )

        return self.get_file(user_id)
    def remove_file(self, file_id: str, collection_id: str, indexing_milvus: IndexingMilvusOri) -> Optional[Dict[str, Any]]:
        """
        Remove a file and its record
        """
        try:
            # Try to convert file_id to ObjectId
            object_id = ObjectId(file_id)
            file_record = self.documents_collection.find_one({'_id': object_id})
        except:
            # If conversion fails, assume file_id is not an ObjectId
            file_record = self.documents_collection.find_one({'file_id': file_id})

        if not file_record:
            raise ValueError(f"File with ID {file_id} not found")

        # Delete file from disk
        file_path = file_record.get('file_path')
        if file_path:
            try:
                # Check bugket is exist
                if not minio_client.bucket_exists(settings.BUCKET_NAME):
                    raise ValueError(f"Bucket {settings.BUCKET_NAME} không tồn tại")
                # Delete file in minIO
                minio_client.remove_object(
                    bucket_name=settings.BUCKET_NAME,
                    object_name=file_path
                )
                # Delete images of file in minIO
                FOLDER_SAVE_IMG = settings.DOCUMENT_IMAGES
                path_to_folder_save_img_of_file = os.path.join(
                    FOLDER_SAVE_IMG,
                    collection_id,
                    file_id
                )

                # Đảm bảo folder_path kết thúc bằng '/' để tìm tất cả object trong thư mục
                if not path_to_folder_save_img_of_file.endswith('/'):
                    path_to_folder_save_img_of_file += '/'
                # Lấy danh sách tất cả object trong thư mục
                objects = minio_client.list_objects(
                    bucket_name=settings.BUCKET_NAME,
                    prefix=path_to_folder_save_img_of_file,
                    recursive=True
                )
                # Tạo danh sách các DeleteObject để xóa
                delete_objects = [DeleteObject(obj.object_name) for obj in objects]
                errors = minio_client.remove_objects(
                    bucket_name=settings.BUCKET_NAME,
                    delete_object_list=delete_objects,
                    bypass_governance_mode=True
                )
                error_count = 0
                for error in errors:
                    logger.error(f"Lỗi khi xóa {error.object_name}: {error.message}")
                    error_count += 1

                if error_count == 0:
                    logger.info(f"Đã xóa {len(delete_objects)} file khỏi bucket {settings.BUCKET_NAME}")
                else:
                    logger.error(f"Có {error_count} lỗi, xóa được {len(delete_objects) - error_count} file")

            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {str(e)}")

        # Delete file from Milvus
        collection_id = file_record.get("collection_id")
        # Remove prefix if present
        if collection_id.startswith(settings.PREFIX_COLLECTION_NAME):
            collection_id = collection_id[len(settings.PREFIX_COLLECTION_NAME):]
        indexing_milvus.delete_file(
            collection_name=settings.PREFIX_COLLECTION_NAME+collection_id,
            file_id=file_id
        )

        # Delete record from mongoDB
        if '_id' in file_record:
            self.documents_collection.delete_one({'_id': file_record['_id']})
        else:
            self.documents_collection.delete_one({'file_id': file_id})

        # Add file_id to returned record
        file_record['file_id'] = str(file_record.get('_id', ''))
        return file_record
    def download_file(self,
        file_path: str
    ):
        res = minio_client.get_object(
            bucket_name=settings.BUCKET_NAME,
            object_name=file_path
        )
        return res
 
    def get_processing_result(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the processing result for a file
        """
        try:
            # Try to convert file_id to ObjectId
            object_id = ObjectId(file_id)
            file_record = self.documents_collection.find_one({'_id': object_id})
        except:
            # If conversion fails, assume file_id is not an ObjectId
            file_record = self.documents_collection.find_one({'file_id': file_id})

        if not file_record:
            raise ValueError(f"File with ID {file_id} not found")

        if file_record.get('status') != 'completed':
            return None

        # Return processing result data
        return {
            'file_id': str(file_record.get('_id', '')),
            'status': file_record['status'],
            'result': file_record.get('result', {}),
            'processing_started': file_record.get('processing_started'),
            'processing_completed': file_record.get('processing_completed')
        }