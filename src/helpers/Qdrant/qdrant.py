from qdrant_client import QdrantClient
import os 

import sys
sys.path.append("")

from dotenv import load_dotenv
load_dotenv()

print("HOST:" ,os.getenv("QDRANT_HOST"))
def get_qdrant_client():
    connection_type  = os.getenv("QDRANT_TYPE")
    if connection_type =='CLOUD':
        connection_args = {
            "uri": os.getenv("QDRANT_ENDPOINT"),
            "token":  os.getenv("QDRANT_TOKEN")
        }
    else:
        connection_args = {
            "host": os.getenv("QDRANT_HOST"),
            "port":  os.getenv("QDRANT_PORT")
        }

    client = QdrantClient(
       **connection_args
    )
    return client

if __name__ == "__main__":
    client= get_qdrant_client()
    print(client)
    try:
        collections = client.get_collections()
        collection_names = [collection.name for collection in collections.collections]
        print(collection_names)
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        print(f"Current connection settings:")
        print(f"QDRANT_TYPE: {os.getenv('QDRANT_TYPE')}")
        print(f"QDRANT_HOST: {os.getenv('QDRANT_HOST')}")
        print(f"QDRANT_PORT: {os.getenv('QDRANT_PORT')}")