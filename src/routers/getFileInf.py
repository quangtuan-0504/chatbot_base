from fastapi import  Form, APIRouter

router = APIRouter(
    prefix="/api"
)


@router.post('/get-file-information/{userId}')
async def get_file_inf(userId:str, collection_name: str = Form(...), file_name : str = Form(...)):
    return {"collection_name": collection_name, "file_name": file_name}