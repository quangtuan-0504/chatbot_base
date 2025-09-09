#indexingMilvus
import sys
sys.path.append("") # Add the root directory to the Python path D:\NAM_A_BANK\chatbot\chatbot_base

import os
os.environ['CUDA_LAUNCH_BLOCKING']="1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"
from tqdm import tqdm


from pymilvus import DataType
# Bản pymilvus 2.5.x so với 2.2.x chỉ bổ sung thêm các chức năng mới thuận tiện hơn chứ không xóa các chức năng cũ nha
from src.tools.document_processing.get_documents import load_document
from configs import settings
from pymilvus import connections, db, MilvusClient
from openai import OpenAI
import time
from loggers.logapp import logger



class IndexingMilvusOriVLLM:
    def __init__(
        self,
        milvus_client: MilvusClient,
        openai_client: OpenAI, 
        embedding_model_name_or_path: str = "text-embedding-3-small"
    ):

        self.client_vector_store = milvus_client
        self.client_embedding_model = openai_client
        self.embedding_model_name_or_path = embedding_model_name_or_path

    def create_collection(self, collection_name: str):
        """The collection name in Milvus is collection id in MongoDB
        Because Milvus require collection name must be start with alphabet, 
        So, we need to add prefix in front of the collection id
        Args:
            collection_name (str): prefix + collection id in mongodb

        Raises:
            Exception: _description_

        Returns:
            _type_: _description_
        """
        res = self.client_vector_store.list_collections()
        if collection_name not in res:
            # Create schema
            schema = self.client_vector_store.create_schema(
                auto_id=True,
                enable_dynamic_field=True,
            )
            # Add fields to schema
            schema.add_field(field_name="pk", datatype=DataType.INT64, is_primary=True)
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=settings.embedding_model['dim'])
            schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="lst_img_of_chunks", datatype=DataType.ARRAY, element_type=DataType.VARCHAR, max_length = 65535 ,max_capacity=20)

            schema.add_field(field_name="chunk_index_in_file", datatype=DataType.INT16)
            schema.add_field(field_name="source", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="file_name", datatype=DataType.VARCHAR, max_length=65535)
            schema.add_field(field_name="file_id", datatype=DataType.VARCHAR, max_length=65535)
            # schema.add_field(field_name="collection_name", datatype=DataType.VARCHAR, max_length=65535)
            # schema.add_field(field_name="page", datatype=DataType.INT64)
            # schema.add_field(field_name="file_type", datatype=DataType.VARCHAR, max_length=65535)



            # Prepare index parameters
            index_params = self.client_vector_store.prepare_index_params()

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
                params={ "nlist": settings.nlist }  # Number of clusters for IVF index
            )
            # Create a collection with the index loaded simultaneously
            self.client_vector_store.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params
            )
            logger.info(f"Create collection successfully!")
            return "Create collection in Milvus successfully!"
        else:
            logger.warning(f"Collection {collection_name} already exists in Milvus.")
            raise Exception(f"Error, collection {collection_name} already exists in Milvus.")

    def add_document(
        self, 
        file_path: str,
        collection_id: str,
        file_id: str,
        file_name: str,
        batch_size: int = 50
    ):
        try:
            if self.client_vector_store.has_collection(collection_name=settings.PREFIX_COLLECTION_NAME + collection_id):

                documents = load_document(
                    file_path= file_path,
                    file_id= file_id,
                    collection_id= collection_id

                )
                # Add file_id to metadata for each document
                for doc in documents: 
                    if not hasattr(doc, 'metadata'):
                        doc.metadata = {}
                    doc.metadata['file_id'] = file_id
                    doc.metadata['file_name'] = file_name
                    doc.metadata['source'] = file_path

                # list document langchain object 
                texts = [doc.page_content for doc in documents]
                for i in tqdm(range(0, len(documents), batch_size), desc="Load data to vector store"):
                    batch_text = texts[i:i+batch_size]
                    # Convert batch text to batch vector
                    batch_emb = self.client_embedding_model.embeddings.create(
                        input=batch_text,
                        model=self.embedding_model_name_or_path
                    )
                    # print(batch_emb.data[0].embedding)
                    logger.info(f"Embedding length: {len(batch_emb.data[0].embedding)}")
                    batch_add = []
                    for emb , doc in zip(batch_emb.data , documents[i:i+batch_size]):
                        batch_add.append({
                            "vector" : emb.embedding, 
                            "text" : doc.page_content, 
                            "lst_img_of_chunks" : doc.metadata['lst_img_of_chunks'], 
                            "chunk_index_in_file" : doc.metadata['chunk_index_in_file'], 
                            "source" : doc.metadata['source'], 
                            "file_name" : doc.metadata['file_name'],
                            "file_id" : doc.metadata['file_id'], 
                            # "collection_name" : doc.metadata['collection_name'], 
                        })


                    res = self.client_vector_store.insert(
                        collection_name=settings.PREFIX_COLLECTION_NAME + collection_id,
                        data=batch_add
                    )

                    # print(res)


                logger.info("Add document successfully")
                return len(texts)
            else:
                logger.warning("Collection not found")
                raise "Collection not found"
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise f"Error adding documents: {str(e)}"

    def delete_collection(self, collection_name: str):
        try:
            if self.client_vector_store.has_collection(collection_name=collection_name):
                self.client_vector_store.drop_collection(collection_name=collection_name)
                return "successfully"
            else:
                raise ValueError("Collection not found")
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            raise ValueError(f"Error deleting collection: {str(e)}")
    def delete_file(self, collection_name: str, file_id: str):
        """collection_name in milvus = prefix + collection_id in mongodb """
        try:
            res = self.client_vector_store.delete(
                collection_name=collection_name,
                # highlight-next-line
                filter= f"source in ['{file_id}']"
            )
            return f"successfully delete {res} entities"
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return "error"
if __name__ == "__main__":

    conn = connections.connect(host="10.18.27.59", port=19530)
    if "tuan_milvus" not in db.list_database():
        database = db.create_database("tuan_milvus")


    indexing = IndexingMilvusOriVLLM(embedding_model_name_or_path="/home/tuanndq/test_chatbot/download_model/model/embedding_models/bge/bge-m3-model")
    indexing.create_collection(collection_name="testne")
    start = time.time()
    indexing.add_document(path_file="test_data/LIVE_MDTV_CapNuoc_CamLam_v.1.0_20240729.docx",collection_name="testne")
    print(time.time()-start)
