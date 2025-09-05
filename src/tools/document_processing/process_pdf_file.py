from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import requests
from io import BytesIO
import re
import requests
import base64
from PIL import Image
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from helpers.minio import minio_client
from tools.intergrations.minio_tools import get_file_from_minio
from configs import settings



def base64_to_pil_image(base64_str):
    try:
        # Decode the base64 string to bytes
        img_bytes = base64.b64decode(base64_str)
        # Create a BytesIO object from the bytes
        img_io = BytesIO(img_bytes)
        # Open the image using PIL
        img = Image.open(img_io)
        return img
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None

def process_response(response):
    # Assuming response is a dictionary with 'text' and 'images'
    text = response.get('text')
    images_base64 = response.get('images')  # Dictionary of image_name: base64_string

    # Convert base64 images back to PIL.Image.Image
    images_pil = {img_name: base64_to_pil_image(base64_str) for img_name, base64_str in images_base64.items()}

    return text, images_pil
def load_pdf(
    file_path: str,
    file_id: str,
    collection_id: str,
    chunk_size: int = 600,
    chunk_overlap: int = 200
) -> List[Document]:

    file_data = get_file_from_minio(
        minio_client = minio_client,
        bucket_name = settings.BUCKET_NAME,
        object_name= file_path,
        return_type="BytesIO"
    )
    file_name = os.path.basename(file_path)
    marker_pdf_url = settings.MARKER_PDF_URL

    try:
        response = requests.post(
            f"http://{marker_pdf_url}/process-file-pdf/?file_path={file_path}",
            files={"file_data": (file_name, file_data, "application/pdf")}
        )
        print(f"Status code: {response.status_code}")
        # print(f"Response text: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

    response_json = response.json()
    text, images = process_response(response_json)


    FOLDER_SAVE_IMG = settings.DOCUMENT_IMAGES
    path_to_save_img_of_file = os.path.join(FOLDER_SAVE_IMG, collection_id, file_id)


    for img_name, img in images.items():

        path_to_per_img_of_file = os.path.join(path_to_save_img_of_file, img_name).replace("\\", "/")  

        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format=img.format or "PNG")  
        img_byte_arr = img_byte_arr.getvalue() 

        minio_client.put_object(
            bucket_name=settings.BUCKET_NAME,
            object_name=path_to_per_img_of_file,
            data=BytesIO(img_byte_arr), 
            length=len(img_byte_arr),  
            part_size=5 * 1024 * 1024,  
        )
        print(f"Uploaded '{path_to_per_img_of_file}' to '{settings.BUCKET_NAME}/{path_to_per_img_of_file}'.")
    docs = [Document(
        page_content=text,
        metadata={
            # "file_name": file_path.split("/")[-1],
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
    re = load_pdf("test_data/1503.03832v3.pdf", "tmp")
    print(re[:10])

 