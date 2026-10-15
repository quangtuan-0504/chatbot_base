from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import os
from src.helpers.minio import minio_client
from src.tools.intergrations.minio_tools import download_file_from_minio
from src.configs import settings


def load_xlsx(file_path: str,
              file_id: str,
              collection_id: str,
              chunk_size: int = settings.XLSX_CHUNK_SIZE,
              chunk_overlap: int = settings.CHUNK_OVERLAP
              ) -> List[Document]:
    temp_file_path = download_file_from_minio(
        minio_client= minio_client,
        bucket_name= settings.BUCKET_NAME,
        object_name = file_path,
        local_file_path= file_path
    )
    loader = UnstructuredExcelLoader(temp_file_path)
    langchain_documents = loader.load()

    langchain_documents[0].metadata.update({
        # "file_id": file_id,
        "lst_img_of_chunks": []
    })

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    langchain_documents_splited = text_splitter.split_documents(
        langchain_documents)
    for i, doc in enumerate(langchain_documents_splited):
        doc.metadata["chunk_index_in_file"] = i
    os.unlink(temp_file_path)

    return langchain_documents_splited
 