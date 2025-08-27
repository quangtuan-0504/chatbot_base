from fastapi import  APIRouter
from ...tools.load_resources import resource
from src.schemas.model_request import request_addUsertoCollection




router = APIRouter(
    prefix="/api"
)
# DATABASE User, department ví dụ
data_user = [{"userID": "0", "department" : "PTUD" , "email" : "abc0@namabank.com.vn" },
             {"userID": "1", "department" : "Phòng quản lý dịch vụ", "email" : "abc1@namabank.com.vn" },
             {"userID": "2", "department" : "Phòng an ninh thông tin", "email" : "abc2@namabank.com.vn" },
             {"userID": "3", "department" : "PTUD", "email" : "abc3@namabank.com.vn" },
             {"userID": "4", "department" : "Phòng kế toán" , "email" : "abc4@namabank.com.vn"},
             {"userID": "5", "department" : "Phòng truyền thông", "email" : "abc5@namabank.com.vn" },
             {"userID": "6", "department" : "PTUD", "email" : "abc6@namabank.com.vn" },
             {"userID": "7", "department" : "Phòng truyền thông", "email" : "abc7@namabank.com.vn" },
             {"userID": "8", "department" : "PTUD" , "email" : "abc8@namabank.com.vn"},
             {"userID": "9", "department" : "Phòng kế toán", "email" : "abc9@namabank.com.vn" },
             {"userID": "10", "department" : "Phòng kế toán" , "email" : "abc10@namabank.com.vn"},]
@router.post("/add-users-to-collection/{userId}")
async def addUserCollection(userId : str, request : request_addUsertoCollection):
    collectionId = request.collection_id
    email = request.user_email
    department = request.department_name
    print("abc")
    print(collectionId)

    db = resource["mongoDB"]
    user_collection = db["user_collections"] 
    if request.user_email:
        # Tìm user thông qua email
        # add user_id,collection_id vào bảng user_collection
        for user in data_user:
            if email == user["email"]:
                user_collection.insert_one({"userId": user["userID"],"collection_id":collectionId })

        
        
    if request.department_name:

        # Lấy danh sách nhân viên thuộc phòng được add
        # add bộ user_id,collection_id của all user trong phòng ban này vào bẳng user_collection
        # sau này sửa thành find many và insert many sau
        for user in data_user:
            if department == user["department"]:
                user_collection.insert_one({"userId": user["userId"], "collection_id":collectionId})
        
    return "successfully!"