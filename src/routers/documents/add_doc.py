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
    file_name: Optional[str] = Form(None), # to user change file name if them want
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
                    message=ResponseMessage.missing_field('collection_id')
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
        file_name_nosuffix, file_extension = os.path.splitext(file_name)[1]
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
            original_file_name=file_name,
            minio_stored_file_name=temp_name,
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