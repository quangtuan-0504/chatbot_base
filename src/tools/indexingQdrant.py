import sys
sys.path.append("")

import os
os.environ['CUDA_LAUNCH_BLOCKING']="1"
os.environ['TORCH_USE_CUDA_DSA'] = "1"
from tqdm import tqdm
import torch

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client.http.models import VectorParams, Distance
from langchain_qdrant import QdrantVectorStore
# from langchain_openai import OpenAIEmbeddings



from src.helpers.Qdrant.qdrants import get_qdrant_client
from src.config.load_config import config
from src.utils.get_documents import load_document

def getEmbeddingModel(providerModel : str):
    if providerModel == "HUGGINGFACE":
        embedding_model = HuggingFaceEmbeddings(model_name=config["HUGGINGFACE_MODEL"]["EMBEDDING_MODEL_PATH"])
    elif providerModel == "OPENAIAPI":
        # embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
        pass
    return embedding_model

class IndexingQdrant:
    def  __init__(  self ,
                    providerModel : str = "HUGGINGFACE"):
        self.clientVectorStore = get_qdrant_client()
        self.embeddingModel = getEmbeddingModel(providerModel=providerModel)

    def create_collection(self, collection_name: str ):
        lst_collections = self.clientVectorStore.get_collections()
        lst_collection_names = [collection.name for collection in lst_collections.collections]
        if collection_name not in lst_collection_names:
            self.clientVectorStore.create_collection(# tạo collection mới
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.DOT),
            )
            print("create collection successfully!")
            return "success"
        else:
            print(f"Collection {collection_name} already exists.")
            return "error"
       
    def add_document(self, collection_name : str, path_file :str, batch_size=50):
        try:
            vector_store = QdrantVectorStore( # instance control collection
                client=self.clientVectorStore,
                collection_name=collection_name,
                embedding=self.embeddingModel,
                distance=Distance.DOT
            )
            documents= load_document(filepath= path_file, document_id=os.path.splitext(path_file)[0])# thêm ID file trong mongoID vào đây
            # documents= load_many_document(folderpath= path_folder, document_id=os.path.splitext(path_folder)[0])
            for i in tqdm(range(0, len(documents), batch_size), desc="Load data to vector store"):
                batch = documents[i:i+batch_size]
                vector_store.add_documents(documents=batch)
                # Giải phóng vector store và làm sạch bộ nhớ GPU
                del batch
            del vector_store
            torch.cuda.empty_cache()
            return "successfully"
        except:
            return "error"
    def delete_collection(self, collection_name):
        pass
    def delete_file(self,file_name):
        pass


if __name__ == "__main__":
    # các cấu hình cho indexing chỉ để ở gọn lại 1 nơi
    # admin load config để khởi tạo
    indexing = IndexingQdrant()
    print(indexing.create_collection("hi"))
    print(indexing.add_document("hi","./test_data/test.docx"))