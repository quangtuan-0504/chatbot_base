from fastapi import HTTPException,  Form, APIRouter
from fastapi.responses import FileResponse

from ...tools.load_resources import resource
from bson import ObjectId
from urllib.parse import quote



router = APIRouter(
    prefix="/api"
)



@router.post('/download-file/{userId}')
async def downloadFile(userId : str,collection_id: str = Form(...),file_id : str = Form(...)):

    db = resource["mongoDB"]
    doc_collection = db["documents"]

    # Tìm tài liệu trong cơ sở dữ liệu
    doc = doc_collection.find_one({"_id": ObjectId(file_id), "collection_id": collection_id})

    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = doc["path"]

    try:
        # Lấy tên file từ đường dẫn
        file_name = file_path.split("/")[-1]

        # Mã hóa tên file để hỗ trợ Unicode
        encoded_file_name = quote(file_name)

        # Trả về file với tên gốc và định dạng đúng
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=file_name,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_file_name}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))