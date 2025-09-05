from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredWordDocumentLoader,
)
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from . import load_docx, load_pdf, load_xlsx
from tools.intergrations.minio_tools import download_file_from_minio
from helpers.minio import minio_client
from configs import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
def load_document(
        file_path : str,
        collection_id : str,
        file_id : str = "",
    ):
    """
    Load a document from various file formats (PDF, DOCX, TXT, DOC) and add metadata.
    Args:
        file_path (str): Full path to the document file to be loaded
        document_id (str): Unique identifier for the document
    Returns:
        list: List of Document objects, where each object represents a page or section
              of the loaded document. Returns empty list if loading fails.
              Each Document object includes metadata with:
              - document_id: The provided identifier
              - file_type: The extension of the source file

    Supported file types:
        - PDF (.pdf): Uses PyPDFLoader
        - Word (.docx): Uses Docx2txtLoader
        - Text (.txt): Uses TextLoader
        - Word 97-2003 (.doc): Uses UnstructuredWordDocumentLoader

    Example:
        >>> docs = load_document("path/to/document.pdf", "doc123")
        >>> print(docs[0].metadata)
        {'document_id': 'doc123', 'file_type': 'pdf', ...}

    Raises:
        Catches all exceptions during loading and prints error message
    """
    try:

        # if it is a .pdf, .docx file, then from file_path get the file from minIO in BytesIO format, and pass it to the processing function. No need to save the tmp file again.
        # if it is a .xlsx,... file, then from file_path get the file from minIO, save it to the tmp folder, the file processing function will read the file from this tmp folder to process.
        # when finished processing, delete this tmp file.

        if file_path.endswith('.pdf'):
            docs = load_pdf(
                file_path=file_path,
                file_id=file_id,
                collection_id=collection_id
            )

        elif file_path.endswith('.docx'):
            docs = load_docx(
                file_path=file_path,
                file_id=file_id,
                collection_id=collection_id
            )
        elif file_path.endswith('.xlsx'):
            docs = load_xlsx(
                file_path=file_path,
                file_id=file_id,
                collection_id=collection_id
            )
        elif file_path.endswith('.txt'):
            temp_file_path = download_file_from_minio(
                minio_client=minio_client,
                bucket_name=settings.BUCKET_NAME,
                object_name = file_path,
                local_file_path= file_path
            )
            loader = TextLoader(temp_file_path)
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.split_documents(docs)
            os.unlink(temp_file_path)
        elif file_path.endswith('.doc'):
            temp_file_path = download_file_from_minio(
                minio_client=minio_client,
                bucket_name=settings.BUCKET_NAME,
                object_name = file_path,
                local_file_path= file_path
            )
            loader = UnstructuredWordDocumentLoader(temp_file_path)
            docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.split_documents(docs)
            os.unlink(temp_file_path)
        else:
            docs = []
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        docs = []
    return docs 

if __name__ == "__main__":
    res=load_document("test_data/test.docx")
    print(res[0])
 