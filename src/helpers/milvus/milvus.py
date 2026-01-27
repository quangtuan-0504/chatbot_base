import os 
from pymilvus import MilvusClient,db, connections
import sys
import os
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))
from configs import settings
from loggers.logapp import logger

def get_milvus_connection_args():
    connection_type  = settings.MILVUS_TYPE
    if connection_type =='CLOUD':
        connection_args = { # This case use only 1 cluster(database) default if you have free version cloud.
            "uri": settings.MILVUS_ENDPOINT,
            "token":  settings.MILVUS_TOKEN,
            # "db_name": settings.MILVUS_DB
        }
    else:
        connection_args = {
            "host": settings.MILVUS_HOST,
            "port":  settings.MILVUS_PORT,
            # "uri": settings.MILVUS_ENDPOINT,
            # "token":  settings.MILVUS_TOKEN,
            "db_name" : settings.MILVUS_DB
        }

    return connection_args

def create_database_in_milvus():
    if settings.MILVUS_TYPE == 'DOCKER':
        conn = connections.connect( 
            host = settings.MILVUS_HOST,
            port =  settings.MILVUS_PORT,
            # uri = settings.MILVUS_ENDPOINT,
            # token =  settings.MILVUS_TOKEN,
        )
        db_name = settings.MILVUS_DB
        # logger.info("connect: ", conn)
        # logger.info("database name: ", db_name)
        logger.info(f"list database: {db.list_database()}")
        if db_name not in db.list_database():
            database = db.create_database(db_name)

def get_milvus_connection():
    """ 
        Connect to Milvus server
        if use cloud milvus free version. you just have one database and you must use it. SO you can't specify db_name in this code.
        if use container local milvus. you can use any database you want. you can specify db_name in this code.
        with MilvusClient: if db_name is specified and it does exits in milvus server, it will use this database.
        if db_name is not specified or it does not exist in milvus server, it will use databse default.

        fix logger: https://grok.com/chat/fc6a369b-07dd-41b5-866b-813d3e54ebd4
    """
    connnect_args = get_milvus_connection_args()
    logger.info(f'Connection milvus arguments: {connnect_args}')

    create_database_in_milvus()

    client = MilvusClient(
        **connnect_args
    )

    lst_collections = client.list_collections()
    if lst_collections:
        logger.info(f"List collection in database: {lst_collections}")
    else:
        logger.info("No collections found in the database.")
    return client

if __name__ == "__main__":
    client = get_milvus_connection()

# kết nối milvus
# case dùng docker -> tạo rồi kết nối đến database đã tạo, or kết nối đến database mặc định, xong tạo và chuyển sang database đã tạo
# case dùng cloud -> chỉ có 1 database mặc định, không cần tạo database mới   