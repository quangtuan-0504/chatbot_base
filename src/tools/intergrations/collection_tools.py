import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from helpers.mongodb.get_mongodb import MongoDBConnections
from tools.rag.indexing_milvus import IndexingMilvusOriVLLM
from configs import settings
from loggers.logapp import logger
from src.helpers.minio import minio_client
from minio.deleteobjects import DeleteObject
from bson import ObjectId
from src.utils.timezone_utils import get_gmt7_datetime_for_db
 

class CollectionTool:
    def __init__(self, mongodb: MongoDBConnections = None):
        self.mongodb = mongodb

    def create_collection(self,
        indexing_milvus: IndexingMilvusOriVLLM,
        collection_name: str,
        user_id: str,
        status: str="active",
        description: str=None,
        tags: list[str]=None
    ):
        # current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        current_time = get_gmt7_datetime_for_db().isoformat()
 
        collection_data = {
            "user_id_create": user_id,
            "collection_name": collection_name,
            "status": status,
            "created_at": current_time,
            "updated_at": current_time,
            "document_count": 0,
            "total_size_bytes": 0
        }

        # Add optional fields if provided
        if description:
            collection_data["description"] = description
        if tags:
            collection_data["tags"] = tags if isinstance(tags, list) else []

        logger.debug(f"Create collection: {collection_data}")

        try:
            check_collection_exits = self.mongodb.COLLECTIONS.find_one({"collection_name": collection_name})
            # if collection doesn't exist, create it
            if not check_collection_exits:
                # Insert MongoDB record
                collection_new = self.mongodb.COLLECTIONS.insert_one(collection_data)
                collection_id = str(collection_new.inserted_id)
                logger.debug(f"Collection created: {collection_id}")
                # thêm phân quyền collection vừa tạo cho người tạo
                new_user_collection = self.mongodb.USER_COLLECTION.insert_one(
                    {
                        "user_id": user_id,
                        "collection_id": collection_id,
                        "role": "owner",
                        "assigned_at": current_time,
                        "assigned_by": user_id
                    })
                logger.debug(f"User collection created: {new_user_collection}")
                try:
                    # Create Milvus collection, collection id in mongodb is collection_name in milvus
                    stt = indexing_milvus.create_collection(collection_name=settings.PREFIX_COLLECTION_NAME + collection_id)
                    logger.debug(f"Milvus collection created: {stt}")
                    return {
                        "id": collection_id,
                        "user_id": user_id,
                        "collection_name": collection_name,
                        "status": status,
                        "created_at": current_time,
                        "updated_at": current_time,
                        "document_count": 0,
                        "total_size_bytes": 0,
                        "description": description,
                        "tags": tags if tags else []
                    }

                except Exception as milvus_error:
                    # If Milvus creation fails, clean up MongoDB record
                    logger.error(
                        f"Failed to create Milvus collection: {str(milvus_error)}")
                    try:
                        logger.info(
                            f"Removing MongoDB record {collection_id} due to Milvus collection creation failure")
                        self.mongodb.COLLECTIONS.delete_one(
                            {"_id": collection_new.inserted_id})
                        self.mongodb.USER_COLLECTION.delete_one(
                            {"_id": new_user_collection.inserted_id})
                        logger.info(
                            f"Successfully removed MongoDB record {collection_id}")
                    except Exception as mongo_error:
                        logger.error(
                            f"Failed to remove MongoDB record: {str(mongo_error)}")

                    # Re-raise the original Milvus error
                    raise milvus_error
            else:
                logger.warning(f"Collection {collection_name} already exists in MongoDB.")
                raise Exception(f"Collection {collection_name} already exists in MongoDB.")
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise

    def remove_collection(self, 
        indexing_milvus: IndexingMilvusOriVLLM,
        collection_id: str,
        user_id: str,
        role: str = "owner"
    ) -> dict:
        """
        Remove a collection and its associated Milvus collection
        if owner, delete all, delete in milvus, mongodb collection, document, user_collection , minio files
        if shared person , just remove in user_collection mongoDB
        """
        # Remove prefix if present
        if collection_id.startswith(settings.PREFIX_COLLECTION_NAME):
            collection_id = collection_id[len(settings.PREFIX_COLLECTION_NAME):]

        # Find and validate collection exists
        collection = self.mongodb.COLLECTIONS.find_one(
            {'_id': ObjectId(collection_id)})
        if not collection:
            raise ValueError("Collection not found in MongoDB")
        if role == 'owner':
            # Remove Milvus collection
            try:
                indexing_milvus.delete_collection(settings.PREFIX_COLLECTION_NAME + collection_id)
            except Exception as e:
                raise RuntimeError(f"Failed to delete Milvus collection: {str(e)}")

            # Remove metadata from MongoDB
            del_collection = self.mongodb.COLLECTIONS.delete_one(
                {'_id': ObjectId(collection_id)}
            )
            del_documents = self.mongodb.DOCUMENTS.delete_many(
                {'collection_id': collection_id}
            )
            del_user_collection = self.mongodb.USER_COLLECTION.delete_many(
                {'collection_id': collection_id}
            )
            if del_collection.deleted_count != 1: # only remove one collection
                raise RuntimeError("Failed to delete collection metadata")
            logger.info(f"num file deleted: {del_documents.deleted_count}")
            logger.info(f"num user collection deleted: {del_user_collection.deleted_count}")

            # Remove files from Minio
            # Check bucket is exist
            if not minio_client.bucket_exists(settings.BUCKET_NAME):
                logger.info(f"Bucket {settings.BUCKET_NAME} doesn't exits")
                raise ValueError("Bucket not found")

            # Remove list files of collection in minio
            FOLDER_SAVE_FILE = settings.UPLOAD_FOLDER
            path_to_folder_save_file_of_collection = os.path.join(
                FOLDER_SAVE_FILE,
                collection_id
            )
            # Đảm bảo folder_path kết thúc bằng '/' để tìm tất cả object trong thư mục
            if not path_to_folder_save_file_of_collection.endswith('/'):
                path_to_folder_save_file_of_collection += '/'

            # Lấy danh sách tất cả object trong thư mục
            objects_file = minio_client.list_objects(
                bucket_name=settings.BUCKET_NAME,
                prefix=path_to_folder_save_file_of_collection,
                recursive=True
            )
            # Tạo danh sách các DeleteObject để xóa
            delete_objects_file = [DeleteObject(obj.object_name) for obj in objects_file]
            deleted_error_objects_file = minio_client.remove_objects( # return list object deleted error
                bucket_name = settings.BUCKET_NAME,
                delete_object_list = delete_objects_file
            )
            error_delete_file_count = 0
            for error in deleted_error_objects_file:
                logger.error(f"Lỗi khi xóa {error.object_name}: {error.message}")
                error_delete_file_count += 1

            if error_delete_file_count == 0:
                logger.error(f"Đã xóa {len(delete_objects_file)} file khỏi bucket {settings.BUCKET_NAME}")
            else:
                logger.error(f"Có {error_delete_file_count} lỗi, xóa được {len(delete_objects_file) - error_delete_file_count} file")

            # Remove folder image of collection in minio
            FOLDER_SAVE_IMG = settings.DOCUMENT_IMAGES
            path_to_folder_save_img_of_collection = os.path.join(
                FOLDER_SAVE_IMG,
                collection_id
            )
            # Đảm bảo folder_path kết thúc bằng '/' để tìm tất cả object trong thư mục
            if not path_to_folder_save_img_of_collection.endswith('/'):
                path_to_folder_save_img_of_collection += '/'

            # Lấy danh sách tất cả object trong thư mục
            objects_img = minio_client.list_objects(
                bucket_name=settings.BUCKET_NAME,
                prefix=path_to_folder_save_img_of_collection,
                recursive=True
            )
            # Tạo danh sách các DeleteObject để xóa
            delete_objects_img = [DeleteObject(obj.object_name) for obj in objects_img]
            deleted_error_objects_img = minio_client.remove_objects(
                bucket_name=settings.BUCKET_NAME,
                delete_object_list=delete_objects_img
            )
            error_delete_img_count = 0
            for error in deleted_error_objects_img:
                logger.error(f"Lỗi khi xóa {error.object_name}: {error.message}")
                error_delete_img_count += 1

            if error_delete_img_count == 0:
                logger.error(f"Đã xóa {len(delete_objects_img)} img khỏi bucket {settings.BUCKET_NAME}")
            else:
                logger.error(f"Có {error_delete_img_count} lỗi, xóa được {len(delete_objects_img) - error_delete_img_count} file")

            logger.error(f"Thực hiện xóa file list image của collection khỏi bucket {settings.BUCKET_NAME}")
        elif role in ['editer', 'viewer']:
            # chỉ xóa trong bảng user collection của mongoDB
            del_user_collection = self.mongodb.USER_COLLECTION.delete_one(
                {'user_id': user_id, 'collection_id': collection_id}
            )
            logger.info(f"num user collection deleted: {del_user_collection.deleted_count}")

        return {
            "id": collection_id,
            "collection_name": collection.get('collection_name'),
            "user_id": user_id,
            "role": role,
        }
    def collection_exists(self, collection_id: str):
        """
        Check if a collection exists by its ID

        Args:
            collection_id (str): The ID of the collection to check

        Returns:
            bool: True if the collection exists, False otherwise
        """
        if collection_id.startswith(settings.PREFIX_COLLECTION_NAME):
            collection_id = collection_id[len(settings.PREFIX_COLLECTION_NAME):]

        try:
            # Convert string ID to ObjectId
            collection = self.mongodb.COLLECTIONS.find_one(
                {'_id': ObjectId(collection_id)})
            return collection is not None
        except Exception as e:
            logger.error(f"Error checking collection existence: {str(e)}")
            return False
    def increment_document_count(self, collection_id: str):
        """
        Increment the document count for a collection by 1
        """
        try:
            if collection_id.startswith(settings.PREFIX_COLLECTION_NAME):
                collection_id = collection_id[len(settings.PREFIX_COLLECTION_NAME):]


            current_time = get_gmt7_datetime_for_db().isoformat()
            result = self.mongodb.COLLECTIONS.update_one(
                {'_id': ObjectId(collection_id)},
                {
                    '$inc': {'document_count': 1},
                    '$set': {'updated_at': current_time}
                }
            )

            if result.matched_count == 0:
                logger.warning(f"Collection {collection_id} not found when incrementing document count")
                return False

            logger.debug(f"Incremented document count for collection {collection_id}")
            return True

        except Exception as e:
            logger.error(f"Error incrementing document count: {str(e)}")
            return False
    def decrement_document_count(self, collection_id: str):
        """
        Decrement the document count for a collection by 1
        """
        try:
            if collection_id.startswith("ai_"):
                collection_id = collection_id[3:]

            current_time = get_gmt7_datetime_for_db().isoformat()
            result = self.mongodb.COLLECTION.update_one(
                {'_id': ObjectId(collection_id)},
                {
                    '$inc': {'document_count': -1},
                    '$set': {'updated_at': current_time}
                }
            )

            if result.matched_count == 0:
                LOGGER.warning(f"Collection {collection_id} not found when decrementing document count")
                return False

            LOGGER.debug(f"Decremented document count for collection {collection_id}")
            return True

        except Exception as e:
            LOGGER.error(f"Error decrementing document count: {str(e)}")
            return False

    def increment_collection_size(self, collection_id: str, size_bytes: int):
        """
        Increment the total size of a collection by the specified number of bytes
        """
        try:
            if collection_id.startswith("ai_"):
                collection_id = collection_id[3:]

            current_time = get_gmt7_datetime_for_db().isoformat()
            result = self.mongodb.COLLECTION.update_one(
                {'_id': ObjectId(collection_id)},
                {
                    '$inc': {'total_size_bytes': size_bytes},
                    '$set': {'updated_at': current_time}
                }
            )

            if result.matched_count == 0:
                LOGGER.warning(f"Collection {collection_id} not found when incrementing size")
                return False

            LOGGER.debug(f"Incremented collection size by {size_bytes} bytes for collection {collection_id}")
            return True

        except Exception as e:
            LOGGER.error(f"Error incrementing collection size: {str(e)}")
            return False

    def decrement_collection_size(self, collection_id: str, size_bytes: int):
        """
        Decrement the total size of a collection by the specified number of bytes
        """
        try:
            if collection_id.startswith("ai_"):
                collection_id = collection_id[3:]

            current_time = get_gmt7_datetime_for_db().isoformat()
            result = self.mongodb.COLLECTION.update_one(
                {'_id': ObjectId(collection_id)},
                {
                    '$inc': {'total_size_bytes': -size_bytes},
                    '$set': {'updated_at': current_time}
                }
            )

            if result.matched_count == 0:
                LOGGER.warning(f"Collection {collection_id} not found when decrementing size")
                return False

            LOGGER.debug(f"Decremented collection size by {size_bytes} bytes for collection {collection_id}")
            return True

        except Exception as e:
            LOGGER.error(f"Error decrementing collection size: {str(e)}")
            return False