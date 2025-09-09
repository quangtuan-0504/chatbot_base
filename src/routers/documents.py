from fastapi import HTTPException, File, Form, UploadFile , APIRouter
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from typing import Optional
from urllib.parse import quote
from dataclasses import asdict
import os
import uuid
from ..tools.load_resources import resource
from ..configs import settings
from ..loggers.logapp import logger
from ..data_models import *

router = APIRouter()

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
@router.post("/get-list-docs-collection/{userId}")
async def get_documents_of_collection(
    userId: str , 
    request : FilesQueryRequest
):  
    try:
        if not request.collection_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('collection_id')
                )),
                status_code=400
            )

        files_data = resource['document_tool'].get_files_of_collection(
            query=request
        )
        file_items = [FileItem.from_dict(file).asdict() for file in files_data]
        if not file_items:
            file_items = []

        response = FileListResponse(
            code=200,
            data=file_items,
            total=len(file_items)
        )

        return asdict(response)

    except Exception as e:
        logger.error(f"Get files error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.put("/delete-file/{userId}")
async def delete_file(userId: str,
    request: DeleteFileRequest
    ):

    try:
        if not request.file_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('file_id')
                )),
                status_code=400
            )
        try:
            response_data = resource['document_tool'].remove_file(
                file_id=request.file_id,
                collection_id=request.collection_id,
                indexing_milvus=resource['indexing']                   
            )

            # Decrement document count in collection if file was successfully removed
            if response_data:
                file_collection_id = response_data.get('collection_id') or request.collection_id
                if file_collection_id:
                    resource['collection_tool'].decrement_document_count(file_collection_id)

            return asdict(FileResponse(
                code=200,
                data=FileItem.from_dict(response_data) if response_data else None,
                message=ResponseMessage.DELETE_SUCCESS
            ))

        except ValueError as ve:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=404,
                    message=str(ve)
                )),
                status_code=404
            )
    except Exception as e:
        logger .error(f"Remove file error: {str(e)}")
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )
@router.post('/download-file/{userId}')
async def download_file(
    userId : str,
    collection_id: str = Form(...),
    file_id : str = Form(...)
):
    try:
        if not file_id or not collection_id:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_field('file_id or collection_id')
                )),
                status_code=400
            )
        # First check if file exists and get its collection
        file_data = resource['document_tool'].get_file(file_id)
        if not file_data:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=404,
                    message="File not found"
                )),
                status_code=404
            )
        file_path_in_minio = file_data['file_path']

        response = resource['document_tool'].download_file(
            file_path = file_path_in_minio
        )
        # response = minio_client.get_object(bucket_name, file_path)

        # Trả về file dưới dạng StreamingResponse
        return StreamingResponse(
            content=response,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={file_path_in_minio.split('/')[-1]}"
            }
        )
    except Exception as e:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )