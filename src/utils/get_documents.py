import sys
sys.path.append("")
from src.utils.process_file.process_pdf_file import load_pdf
from src.utils.process_file.process_xlsx_file import load_xlsx
from src.utils.process_file.process_docx_file import load_docx



def load_document(filepath : str,
                   collection_name : str ="tmp",
                     mongo_file_id : str = "mongo_file_id"):
    """
    Load a document from various file formats (PDF, DOCX, TXT, DOC) and add metadata.
    Args:
        filepath (str): Full path to the document file to be loaded
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
        if filepath.endswith('.pdf'):
           
            docs = load_pdf(
                filepath,
                collection_name=collection_name,
                mongo_file_id=mongo_file_id
            )

        elif filepath.endswith('.docx'):
           
            docs = load_docx(
                filepath,
                collection_name=collection_name,
                mongo_file_id=mongo_file_id
            )
        elif filepath.endswith('.xlsx'):
          
            docs = load_xlsx(
                filepath,
                collection_name=collection_name,
                mongo_file_id=mongo_file_id
            )
        else:
            print(f"{filepath} skipped")
       
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
        docs = []
    return docs 

if __name__ == "__main__":
    res=load_document("test_data/test.docx")
    print(res[0])