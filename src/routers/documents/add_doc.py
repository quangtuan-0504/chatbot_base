from fastapi import HTTPException, File, Form, UploadFile , APIRouter
from datetime import datetime , timezone
from fastapi.responses import JSONResponse
from typing import Optional
from dataclasses import asdict
import os
import uuid
from ...tools.load_resources import resource
from ...configs import settings
from ...loggers.logapp import logger
from ...data_models import *

router = APIRouter(
    prefix="/api"
)

@router.post("/add-document/{userId}")
async def add_document(userId:str,
    file: UploadFile = File(...),
    collection_id: str = Form(...),
    description: str|None = Form(None),
    file_type: Optional[str] = Form(None),
    file_name: Optional[str] = Form(None),
):
    logger.debug(f"File upload request: {file.filename}, collectionId: {collection_id}, fileType: {file_type}, fileName: {file_name}")
    try:
        if file.filename == '':
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('filename')
                )),
                status_code=400
            )

        # Extract metadata
        if file_type is None:
            file_type = file.filename.split(".")[-1]

        if file_name is None:
            file_name = file.filename

        if not collection_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('collectionId')
                )),
                status_code=400
            )

        if not resource['collection_tool'].collection_exists(collection_id):
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.COLLECTION_NOT_FOUND
                )),
                status_code=400
            )

        collection_folder = os.path.join(settings.UPLOAD_FOLDER, collection_id)
        file_name_nosuffix, file_extension = os.path.splitext(file.filename)[1]
        temp_name = f"{file_name_nosuffix}_{str(uuid.uuid4())}{file_extension}"
        temp_path = os.path.join(collection_folder, temp_name)

        # Lưu file tạm vào bộ nhớ hoặc xử lý ngay
        file_content = await file.read()
        file.file.seek(0)  # Reset file pointer
        file_size = len(file_content)

        # Save file into MinIO
        resource['minio_client'].put_object(
            bucket_name=settings.BUCKET_NAME,
            object_name=temp_path,
            data=file.file,  
            length=file_size,  
            part_size=5 * 1024 * 1024,  
            content_type=file.content_type
        )
        logger.info(f"Uploaded '{temp_path}' to '{settings.BUCKET_NAME}/{temp_path}'.")

        # Create file record in mongoDB
        file_data = resource['document_tool'].create_file(
            original_filename=file_name,
            stored_filename=temp_name,
            file_path=temp_path,  # path in minIO
            user_id=userId,
            collection_id=collection_id,
            file_type=file_type,
            description= description
        )

        # Increment document count in collection
        resource['collection_tool'].increment_document_count(collection_id)

        file_item = FileItem.from_dict(file_data).asdict()

        return asdict(FileResponse(
            code=200,
            data=file_item,
            message=ResponseMessage.UPDATE_SUCCESS  # TODO
        ))

    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )
@router.post("/add-document/{userId}")
async def add_document(userId:str,
    file: UploadFile = File(...),
    collection_name: str = Form(...),
    collection_id: str = Form(...),
    description: str = Form(...)
):
    """
    Endpoint để nhận file upload cùng với thông tin bổ sung từ frontend.
    add metadata của file vô mongodb, lưu file vào đĩa, load file từ đĩa lên xử lý và add vô milvus.

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
            if not os.path.exists(f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}"):
                os.makedirs(f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}")
            with open(f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}/{file.filename}", "wb") as f:
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
                                            "path": f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}/{file.filename}",
                                            "addAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                                            "type": file.filename.split('.')[-1],
                                            "size": file_size})

        ###############
        indexing = resource["indexing"]
        status = indexing.add_document(
            path_file=f"{settings.PATH_SAVE_FILE_UPLOAD}/{collection_name}/{file.filename}" , 
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