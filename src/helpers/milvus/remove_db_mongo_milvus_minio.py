from pymilvus import MilvusClient
import os
from pprint import pprint

def delete_collection(client_milvus,collection_name: str):
    try:
        if client_milvus.has_collection(collection_name=collection_name):
            client_milvus.drop_collection(collection_name=collection_name)
            return "successfully"
        return "collection not found"
    except Exception as e:
        return "error"
def clear_collection_in_db(client):
    for collection in client.list_collections():
        print(f"Delete old collection {collection}")
        delete_collection(client_milvus=client,collection_name=collection)
def rm_db_milvus(db_name:str,only_clear_collection: bool = True):
    """
        (only clear all collection in db) or (clear all collection and remove database). 
        can not remove default database in milvus. Only clear collection in default database.
        https://milvus.io/docs/manage_databases.md
    """
    client = MilvusClient(
        # uri=os.getenv("MILVUS_ENDPOINT"),
        # token= os.getenv("MILVUS_TOKEN"),
        # db_name="test"
        host = "10.18.27.59",
        port = "19530",
        db_name=db_name

    )

    # List all existing databases
    print(client.list_databases())

    clear_collection_in_db(client)

    if db_name != "default" and only_clear_collection == False:
        client.drop_database(
            db_name=db_name
        )

from pymongo import MongoClient

def delete_database_mongodb(db_name):
    try:
        # Kết nối đến MongoDB (mặc định localhost, port 27017)
        client = MongoClient("mongodb://admin:password123@10.18.27.59:27017/")
        
        # Kiểm tra xem database có tồn tại không
        if db_name in client.list_database_names():
            # Xóa database
            client.drop_database(db_name)
            print(f"Database '{db_name}' đã được xóa thành công!")
        else:
            print(f"Database '{db_name}' không tồn tại!")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
def delete_collection_mongodb(db_name, collection_name):
    try:
        # Kết nối đến MongoDB (mặc định localhost, port 27017)
        client = MongoClient('mongodb://localhost:27017/')
        
        # Chọn database
        db = client[db_name]
        
        # Kiểm tra xem collection có tồn tại không
        if collection_name in db.list_collection_names():
            # Xóa collection
            db.drop_collection(collection_name)
            print(f"Collection '{collection_name}' trong database '{db_name}' đã được xóa thành công!")
        else:
            print(f"Collection '{collection_name}' không tồn tại trong database '{db_name}'!")
            
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
# Ví dụ sử dụng
if __name__ == "__main__":
    # Tên database mongodb cần xóa
    database_name = "chatbot_sit"
    delete_database_mongodb(database_name)

    rm_db_milvus(db_name="default",only_clear_collection=True)