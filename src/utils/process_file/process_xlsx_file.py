from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List

def load_xlsx(file_path: str ,
                    collection_name : str ,
                    mongo_file_id : str = "mongo_file_id",
                    chunk_size: int = 600,
                    chunk_overlap: int = 200
    )-> List[Document]:
    loader = UnstructuredExcelLoader(file_path)
    langchain_documents = loader.load()

    langchain_documents[0].metadata.update({
        "source": file_path,
        "file_name" : file_path.split("/")[-1],
        "mongo_file_id" : mongo_file_id,
        "collection_name": collection_name,
        "file_type" : file_path.split(".")[-1],
        "lst_img_of_chunks": []
    })

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    langchain_documents_splited = text_splitter.split_documents(langchain_documents)
    for i,doc in enumerate(langchain_documents_splited):
        doc.metadata["chunk_index_in_file"] = i

    return langchain_documents_splited