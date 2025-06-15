from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import Dict, List, Callable, Optional

import requests
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.output import save_output
import os
import re

import sys
sys.path.append("")
from src.config.load_config import config


            
def load_pdf(
        file_path: str ,
        collection_name : str ,
        mongo_file_id : str = "mongo_file_id",
        chunk_size: int = 600,
        chunk_overlap: int = 200 # chunk overlab =200 ko có nghĩa là thằng langchain nó sẽ lấy trùng đúng 200 ký tự mà nó lấy loanh quanh
    )-> List[Document]:

   
    converter = PdfConverter(
        artifact_dict=create_model_dict(),
    )
    if converter:
        rendered = converter(file_path)
        text, _, images = text_from_rendered(rendered)


        FOLDER_SAVE_IMG = config["PATH_SAVE_IMG_OF_FILE"]
        file_name = os.path.basename(file_path)
        # lưu ảnh theo collection + file_name
        path_to_save_img_of_file = os.path.join(FOLDER_SAVE_IMG,collection_name,"".join(file_name.split('.')[:-1]))
        if not os.path.exists(path_to_save_img_of_file):
            os.makedirs(path_to_save_img_of_file)
        for img_name,img in images.items():
            img.save(os.path.join(path_to_save_img_of_file,img_name))

        docs = [Document(
                    page_content=text,
                    metadata={  
                        "source": file_path,
                        "file_name" : file_path.split("/")[-1],
                        "mongo_file_id" : mongo_file_id,
                        "collection_name": collection_name,
                        "file_type" : file_path.split(".")[-1]
                        }
                    )
                ]

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,  # chunk size (characters)
            chunk_overlap=chunk_overlap,  # chunk overlap (characters)
            add_start_index=True,  # track index in original document
        )
        docs_splitted = text_splitter.split_documents(docs)

        # Biểu thức chính quy để tìm các tên file hình
        pattern = r'!\[\]\((.*?)\)'
        
        for i,doc in enumerate(docs_splitted):
            doc.metadata["lst_img_of_chunks"] = [os.path.join(path_to_save_img_of_file,img_name)
                                                    for img_name in re.findall(pattern, doc.page_content)]
            # doc.metadata.update({"lst_img_of_chunks" : [os.path.join(path_to_save_img_of_file,img_name)
            #                                         for img_name in re.findall(pattern, doc.page_content)]})
            doc.metadata["chunk_index_in_file"] = i


        return docs_splitted

if __name__ == "__main__":
    re=load_pdf("test_data/1503.03832v3.pdf", "tmp")
    print(re[:10])