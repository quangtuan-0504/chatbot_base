from fastapi import HTTPException, File, Form, UploadFile , APIRouter
from ..tools.loadResources import resource
from datetime import datetime , timezone
from fastapi.responses import JSONResponse
import os
from src.config.load_config import config



router = APIRouter(
    prefix="/api"
)

@router.post("/add-document/{userId}")
async def addDocument(userId:str,
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    collection_id: str = Form(...),
    description: str = Form(...)
):
    """
    Endpoint để nhận file upload cùng với thông tin bổ sung từ frontend.

    Args:
        file (UploadFile): File được upload từ frontend.
        collection_name (str): Tên collection.
        description (str): Mô tả của file.

    Returns:
        JSONResponse: Trạng thái xử lý file.
    """
    try:
        # Lưu file tạm vào bộ nhớ hoặc xử lý ngay
        file_content = await file.read()
        file_size = len(file_content)
        
        # Xử lý thông tin khác
        print(f"Collection Name: {collection_name}")
        print(f"Description: {description}")
        print(f"File Name: {file.filename}, Size: {file_size} bytes")
        
        db = resource["mongoDB"]
        file_table = db["documents"]
        # lst_file_name_of_collection =['test.pdf']# sẽ sửa lại load danh sách từ mongoDB
        check_file = file_table.find_one({"collection_id":collection_id, "file_name": file.filename})
        print(check_file)

        lst_file_name_of_collection = file_table.find({"collection_id":collection_id},{"_id":0,"file_name":1})
        lst_file_name_of_collection_ = [ file_n["file_name"] for file_n  in lst_file_name_of_collection]
        print(lst_file_name_of_collection_)
        # Nếu file đã được add vào collection.
        if file.filename in lst_file_name_of_collection_:
            print("file already exists in collection")
            raise HTTPException(status_code=500, detail="file already exists in collection")
        else: 
            # Bạn có thể lưu file vào đĩa hoặc cơ sở dữ liệu tại đây
            if not os.path.exists(f"{config['PATH_SAVE_FILE_UPLOAD']}/{collection_name}"):
                os.makedirs(f"{config['PATH_SAVE_FILE_UPLOAD']}/{collection_name}")
            with open(f"{config['PATH_SAVE_FILE_UPLOAD']}/{collection_name}/{file.filename}", "wb") as f:
                f.write(file_content)

        collection_table = db['collection']
        check_collection_exits = collection_table.find_one({"collection_name": collection_name})

        document_collection = db['documents']
        if not check_collection_exits:
            raise  HTTPException(status_code=500, detail="collection not exists")      
        else:
            # Nếu collection đã tồn tại, cập nhật `updateAt`
            collection_table.update_one(
                {"collection_name": collection_name},
                {"$set": {"updateAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}}
            )
        fileAdd = document_collection.insert_one({"collection_id": collection_id,
                                            "description": description,
                                            "file_name": file.filename,
                                            "path": f"{config['PATH_SAVE_FILE_UPLOAD']}/{collection_name}/{file.filename}",
                                            "addAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                                            "type": file.filename.split('.')[-1],
                                            "size": file_size})

        ###############
        indexing = resource["indexing"]
        status = indexing.add_document(
            path_file=f"{config['PATH_SAVE_FILE_UPLOAD']}/{collection_name}/{file.filename}" , 
            collection_name="hello" + collection_id,# tên collection trong milvus sẽ là id của collection trong mongoDB
            mongo_document_id=str(fileAdd.inserted_id)
        )
        print(status)
            
            
            
            
        
        return JSONResponse(content={
            "message": "File uploaded successfully",
            "file_name": file.filename,
            "file_size": file_size,
            "collection_name": collection_name,
            "description": description
        }, status_code=200)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))