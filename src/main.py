from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os


import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(file),'..')))
from src.tools.loadResources import resourcelifespan
from src.routers import ( 
    chats,
    newCollection,
    addDoc,
    deleteCollection,
    deleteDoc,
    downloadFile,
    getListCollections,
    getListDocOfCollection,
    addUserToCollection,
)


app = FastAPI(title="Chatbot pro",lifespan=resourcelifespan)

#print(resource)
#print($$$$$)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],  # Cho phép tất cả các nguồn gốc. Bạn có thể giới hạn lại theo nhu cầu
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # Quan trọng: Cho phép header này hiển thị
)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/sign-up") 
async def add_user():
    return "add user successfully!"

@app.post("/log-in")
async def check_user():
    return "Log-in sucessfully!"
@app.put("/reset_password")
async def resetpass():
    return "Reset pass successfully!"
@app.post("/log-out")
async def logout():
    return "Logout Successfully!"
@app.get("/api/getListDepartment/{userId}")
async def get_department(userId: str):
    lst_depart = ["depart 1","depart 2","depart 3","depart 4","depart 5"]
    return lst_depart


app.include_router(chats.router)
app.include_router(newCollection.router)
app.include_router(addDoc.router)
app.include_router(deleteCollection.router)
app.include_router(deleteDoc.router)
app.include_router(downloadFile.router)
app.include_router(getListCollections.router)
app.include_router(getListDocOfCollection.router)
app.include_router(addUserToCollection.router)


  
if name == "main":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)

# python src/main.py
# uvicorn src.main:app --host 0.0.0.0 --port 8050