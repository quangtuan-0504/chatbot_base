import os
from src.helpers.minio import minio_client
from src.tools.intergrations.minio_tools import get_file_from_minio
from src.configs import settings
from io import BytesIO
from typing import List
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from docx import Document as DocumentPythonDocx


def sort_func(item):
    return int(item.split('.')[0][5:])


def load_docx(
    file_path: str,
    file_id: str ,
    collection_id: str,
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP
) -> List[Document]:
    file_data =  get_file_from_minio(
        minio_client = minio_client,
        bucket_name = settings.BUCKET_NAME,
        object_name = file_path,
        return_type = "BytesIO"
    )
    # doc = DocumentPythonDocx(file_path)
    doc = DocumentPythonDocx(file_data)

    path_to_save_img_of_file = os.path.join(settings.DOCUMENT_IMAGES,collection_id, file_id)

    lst_name_img = []
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            image_name = os.path.basename(rel.target_ref)
            lst_name_img.append(image_name)

            image_path = os.path.join(path_to_save_img_of_file, image_name).replace("\\", "/")

            ext = os.path.splitext(image_name)[1].lower()
            content_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".bmp": "image/bmp"
            }.get(ext, "image/png")  


            minio_client.put_object(
                bucket_name=settings.BUCKET_NAME,
                object_name=image_path,
                data=BytesIO(image_data),  
                length=len(image_data),  
                part_size=5 * 1024 * 1024,  
                content_type=content_type
            )
            print(f"Uploaded '{image_path}' to '{settings.BUCKET_NAME}/{image_path}'.")

    lst_name_img = sorted(lst_name_img, key=sort_func)
    result_text = ""
    table_count = 0
    image_count = 0
    for element in doc.element.body:
        if element.tag.endswith('p'):
            text = element.text.strip()
            if text:
                result_text += text + "\n"
            element_xml = element.xml
            if "<w:drawing>" in element_xml or "<w:pict>" in element_xml:
                if "<a:blip " in element_xml or "<a:blip>" in element_xml:
                    if image_count < len(lst_name_img):
                        print("có ảnh")
                        result_text += f"![]({lst_name_img[image_count]})" + "\n"
                        image_count += 1

        elif element.tag.endswith('tbl'):
            table = doc.tables[table_count]
            table_count += 1
            table_text = ""
            for row in table.rows:
                row_text = "\t".join(cell.text.strip()
                                     for cell in row.cells).replace('\n', ' ')
                table_text += row_text + "\n"
            result_text += table_text
    docs = [Document(
        page_content=result_text,
        metadata={
            # "file_name":  os.path.basename(file_path),
            # "file_id": file_id,
        }
    )
    ]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    docs_splitted = text_splitter.split_documents(docs)

    pattern = r'!\[\]\((.*?)\)'
    for i, doc in enumerate(docs_splitted):
        doc.metadata["lst_img_of_chunks"] = [os.path.join(path_to_save_img_of_file, img_name)
                                             for img_name in re.findall(pattern, doc.page_content)]
        doc.metadata["chunk_index_in_file"] = i

    return docs_splitted


if __name__ == "__main__":
    pass
 