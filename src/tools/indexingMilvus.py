#indexingMilvus
import sys
sys.path.append("")

import os
os.environ['CUDA_LAUNCH_BLOCKING']="1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"
from tqdm import tqdm


from pymilvus import DataType
# Bản pymilvus 2.5.x so với 2.2.x chỉ bổ sung thêm các chức năng mới thuận tiện hơn chứ không xóa các chức năng cũ nha

from src.helpers.Milvus.milvus import  get_milvus_connection
from src.utils.get_documents import load_document
from src.config.load_config import config

from pymilvus import connections, db
from openai import OpenAI
import time



class IndexingMilvusOriVLLM:
    def __init__(self, embedding_model_name: str):
        self.clientVectorStore=get_milvus_connection()

        openai_api_key_model_embedding = os.getenv("OPENAI_API_KEY")
        # openai_api_urlbase_model_embedding = "http://localhost:8001/v1"
        self.client_embedding_model = OpenAI(
            api_key=openai_api_key_model_embedding,
            # base_url=openai_api_urlbase_model_embedding,
        )
        self.embedding_model_name = embedding_model_name

    def create_collection(self, collection_name: str):

        res = self.clientVectorStore.list_collections()
        if collection_name not in res:
            # Create schema
            schema = self.clientVectorStore.create_schema(
                auto_id=True,
                enable_dynamic_field=True,
            )
            # Add fields to schema
            schema.add_field(field_name="pk", datatype=DataType.INT64, is_primary=True)
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=1024)
            schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="lst_img_of_chunks", datatype=DataType.ARRAY, element_type=DataType.VARCHAR, max_length = 65535 ,max_capacity=20)

            schema.add_field(field_name="chunk_index_in_file", datatype=DataType.INT16)
            schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="file_name", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="mongo_file_id", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="collection_name", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="file_type", datatype=DataType.VARCHAR, max_length=65535)
            


            # Prepare index parameters
            index_params = self.clientVectorStore.prepare_index_params()

            # Add indexes
            index_params.add_index(
                field_name="pk",
                index_type="STL_SORT"
            )
            # Add indexes
            index_params.add_index(
                field_name="file_name",
                index_type="Trie",
                # index_type="AUTOINDEX",
                index_name='filename_index'
            )
            index_params.add_index(
                field_name="vector",
                metric_type="COSINE",
                index_type="IVF_FLAT",
                index_name="vector_index",
                params={ "nlist": 128 }
            )
            # Create a collection with the index loaded simultaneously
            self.clientVectorStore.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params
            )
            print("Create collection successfully!")
            return "Create collection successfully!"
        else:
            print(f"Collection {collection_name} already exists.")
            return "error"

    def add_document(self, path_file: str | None, collection_name: str, mongo_document_id : str = "mongo_doc_id" , batch_size=50 ):
        try:
            if self.clientVectorStore.has_collection(collection_name=collection_name):
        
                documents = load_document(filepath=path_file, collection_name=collection_name , mongo_file_id=mongo_document_id )
                # list document langchain object 
                texts = [doc.page_content for doc in documents]
                for i in tqdm(range(0, len(documents), batch_size), desc="Load data to vector store"):
                    batch_text = texts[i:i+batch_size]
                    # Convert batch text to batch vector
                    batch_emb = self.client_embedding_model.embeddings.create(
                        input=batch_text,
                        model=self.embedding_model_name
                    )
                    batch_add = []
                    for emb , doc in zip(batch_emb.data , documents[i:i+batch_size]):
                        batch_add.append({
                            "vector" : emb.embedding, 
                            "text" : doc.page_content, 
                            "lst_img_of_chunks" : doc.metadata['lst_img_of_chunks'], 
                            "chunk_index_in_file" : doc.metadata['chunk_index_in_file'], 
                            "source" : doc.metadata['source'], 
                            "file_name" : doc.metadata['file_name'],
                            "mongo_file_id" : doc.metadata['mongo_file_id'], 
                            "collection_name" : doc.metadata['collection_name'], 
                            "file_type" : doc.metadata['file_type']
                        })
                  

                    res = self.clientVectorStore.insert(
                        collection_name=collection_name,
                        data=batch_add
                    )

                    print(res)


                print("successfully")
                return "successfully"
            else:
                print("Collection not found")
                return "Collection not found"
        except Exception as e:
                print(f"Error adding documents: {str(e)}")
                return "error"

    def delete_collection(self, collection_name: str):
        try:
            if self.clientVectorStore.has_collection(collection_name=collection_name):
                self.clientVectorStore.drop_collection(collection_name=collection_name)
                return "successfully"
            return "collection not found"
        except Exception as e:
            print(f"Error deleting collection: {str(e)}")
            return "error"
    def delete_file(self, collection_name: str, file_name: str):
        try:
            res = self.clientVectorStore.delete(
                collection_name=collection_name,
                # highlight-next-line
                filter= f"source in ['{file_name}']"
            )
            return f"successfully delete {res} entities"
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return "error"       
if __name__ == "__main__":

    conn = connections.connect(host="10.18.27.59", port=19530)
    if "tuan_milvus" not in db.list_database():
        database = db.create_database("tuan_milvus")


    indexing = IndexingMilvusOriVLLM(embedding_model_name="/home/tuanndq/test_chatbot/download_model/model/embedding_models/bge/bge-m3-model")
    indexing.create_collection(collection_name="testne")
    start = time.time()
    indexing.add_document(path_file="test_data/LIVE_MDTV_CapNuoc_CamLam_v.1.0_20240729.docx",collection_name="testne")
    print(time.time()-start)
