import os 
from pymilvus import MilvusClient
from src.config.load_config import config

def get_milvus_connection_args():
    connection_type  = os.getenv("MILVUS_TYPE")
    if connection_type =='CLOUD':
        connection_args = {
            "uri": os.getenv("MILVUS_ENDPOINT"),
            "token":  os.getenv("MILVUS_TOKEN")
        }
    else:
        connection_args = {
            "host": os.getenv("MILVUS_HOST"),
            "port":  os.getenv("MILVUS_PORT"),
            "db_name" : config["MILVUS_DB"]
        }

    return connection_args


def get_milvus_connection():
    """Connect to Milvus server"""
    connnect_args= get_milvus_connection_args()
    client = MilvusClient(
        **connnect_args
    )
    res = client.list_collections()
    print(res)
    return client