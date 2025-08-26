from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from docx import Document as DocumentPythonDocx

import sys
sys.path.append("")
from src.config.load_config import config
import uuid
from typing import List
import os
import re
def sort_func(item):# os.listdir lộn xộn kể cả sorted
  return int(item.split('.')[0][5:])
def load_docx(
        file_path: str ,
        collection_name : str ,
        mongo_file_id : str = "mongo_file_id",
        chunk_size: int = 600,
        chunk_overlap: int = 200
    )-> List[Document]:
    # Mở file .docx
    doc = DocumentPythonDocx(file_path)

    FOLDER_SAVE_IMG = config["PATH_SAVE_IMG_OF_FILE"]
    file_name = os.path.basename(file_path)
    # lưu ảnh theo collection + file_name
    path_to_save_img_of_file = os.path.join(FOLDER_SAVE_IMG,collection_name, "".join(file_name.split('.')[:-1]))
    if not os.path.exists(path_to_save_img_of_file):
        os.makedirs(path_to_save_img_of_file)

    # Save list image in file , lưu theo thứ tự từ trên xuống nha .
    lst_name_img = []
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            image_name = os.path.basename(rel.target_ref)
            print(image_name)
            lst_name_img.append(image_name)
            image_path = os.path.join(path_to_save_img_of_file, image_name )
            with open(image_path, "wb") as img_file:
                img_file.write(image_data)

    lst_name_img =  sorted(lst_name_img , key=sort_func)
    print(lst_name_img)
    # Khởi tạo kết quả
    result_text = ""
    

    # Iterate through all elements in the document
    table_count = 0
    image_count = 0
    for element in doc.element.body:
        
        # print(dir(element))
        # print(element.xml) # xml là một kiểu ngôn ngữ dạng như html
        if element.tag.endswith('p'):  # Check if the element is a paragraph and image
            text = element.text.strip()
            if text:
                result_text += text + "\n"
            
            # Lấy nội dung XML của phần tử
            element_xml = element.xml
            
            # Kiểm tra nếu XML có chứa w:drawing hoặc w:pict
            if "<w:drawing>" in element_xml or "<w:pict>" in element_xml:
                if "<a:blip>" in element_xml:
                    if image_count < len(lst_name_img):
                        print("có ảnh")
                        result_text+=f"![]({lst_name_img[image_count]})" + "\n"
                        image_count+=1
        
        elif element.tag.endswith('tbl'):  # Check if the element is a table
            table = doc.tables[table_count]  # Lấy bảng từ element
            table_count+=1
            table_text = ""
            for row in table.rows:
                row_text = "\t".join(cell.text.strip() for cell in row.cells).replace('\n',' ')
                table_text += row_text + "\n"
            result_text += table_text

    # return result_text
    docs = [Document(
                page_content=result_text,
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
        chunk_size = chunk_size,  # chunk size (characters)
        chunk_overlap = chunk_overlap,  # chunk overlap (characters)
        add_start_index = True,  # track index in original document
    )
    docs_splitted = text_splitter.split_documents(docs)

    # Biểu thức chính quy để tìm các tên file hình
    pattern = r'!\[\]\((.*?)\)'# "! [ ]  ()" : là để khớp, "(.*?)" : là để lấy phần kết quả trả về .
    for i,doc in enumerate(docs_splitted):
        doc.metadata["lst_img_of_chunks"] = [os.path.join(path_to_save_img_of_file,img_name)
                                                for img_name in re.findall(pattern, doc.page_content)]
        doc.metadata["chunk_index_in_file"] = i

    return docs_splitted

if __name__ == "__main__":
    path_file = "test_data/test.docx"
    re= load_docx(file_path=path_file,
                   collection_name="tmp1")
    for chunk in re:
        print(chunk.page_content)
        print("#############")
    # print(re)
