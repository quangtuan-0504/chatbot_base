from fastapi import APIRouter, Depends, HTTPException, WebSocket ,WebSocketDisconnect
from bson import ObjectId
from ..tools.loadResources import resource
from src.schemas.model_request import request_GetChat, request_Chat , request_AddChat , request_UpdateChat
from datetime import datetime , timezone
import json
from openai import OpenAI
import time

router = APIRouter(
    prefix="/api/chat"
)


@router.get("/listchats/{userId}")
async def getListChatOfUser(userId):
    db = resource["mongoDB"]
    chat_table = db["chats_2"]
    lst_chat = chat_table.find({"userId": userId},{"_id": 1,"title": 1, "createAt": 1 , "updateAt" : 1})
    print(lst_chat)
    if not lst_chat:
        return []
    result = [
        {
            "_id": str(chat["_id"]),  # Chuyển ObjectId sang chuỗi
            "title": chat.get("title"),
            "createAt": chat.get("createAt"),
            "updateAt" : chat.get("updateAt")
        }
        for chat in lst_chat
    ]
    
    return result



@router.post("/chat-history/{chatId}")
async def getChatHistory(chatId: str, request: request_GetChat):
    db = resource["mongoDB"]
    userId= request.userId
    chat_table = db["chats_2"]
    chat = chat_table.find_one({"_id": ObjectId(chatId), "userId": userId})
    # print(chat)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"chat_id": str(chat['_id']) ,"history":chat['history']}


@router.post("/delete-chat/{chatId}")
async def deleteChat(chatId: str):
    db = resource["mongoDB"]
    chat_table = db["chats_2"]
    # for x in chat_table.find():
    #     print(x)
    try:
        # Kiểm tra nếu chatId có thể chuyển thành ObjectId
        query = {"_id": ObjectId(chatId)}

        result = chat_table.delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete chat failed: {str(e)}")
    
    return {"message": "Delete chat successfully!"}

@router.post("/new-chat")
async def createNewChat(request: request_AddChat):
    userId = request.userId
    text = request.text
    db = resource["mongoDB"]
    chat_table = db["chats_2"]
    chat = {"title" : text[:40] ,
                "userId" : userId ,
                "createAt" : datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") ,
                "updateAt" : datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") ,
                "history" : [{"role": "user","content": text}]
            }
    newChat = chat_table.insert_one(chat)
    chatId = str(newChat.inserted_id)
    return {"id" : chatId}

@router.put("/save-message/{chatId}")
async def saveMessage(chatId : str, request: request_UpdateChat):
    userId = request.userId
    question = request.question
    answer = request.answer
    source = request.source
  


    db = resource["mongoDB"]
    chat_table = db['chats_2']
    new_items = []
    if question:
        new_items.append({"role": "user", "content": question})
    new_items.append({"role": "assistant", "content": {"answer" : answer, "source" : source}})
    result = chat_table.update_one(
        {"_id": ObjectId(chatId), "userId": userId},
        {"$set":{"updateAt" : datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} ,"$push": {"history": {"$each": new_items}}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found or not updated")
    return {"chatId": chatId}


@router.websocket("/chat-stream")
async def streamChatwebsocket(websocket: WebSocket):
    await websocket.accept()# chấp nhận mở 1 kết nối
    
        
    data = await websocket.receive_text()# nhận request
    request = json.loads(data)  # Chuyển đổi JSON từ client

    userId = request.get("userId")
    question = request.get("question")
    chatId = request.get("chatId")
    fileNames = request.get("fileNames")
    collection_name_inVS = request.get("collection_name_inVS")
    llm = request.get("LLM")
    sysMode = request.get("sysMode")

    print("gửi request thành công")
    print(question)
    print(type(collection_name_inVS))
    print('collection_name_inVS:',collection_name_inVS)
    print("fileNames:" , fileNames)

    db = resource["mongoDB"]
    chat_table = db['chats_2']
    historyChat = []
    if chatId:
        chat = chat_table.find_one({"_id": ObjectId(chatId), "userId": userId})
        historyChat = chat['history']
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
                

    chatbot_aya_expanse_8b = resource["chatbot_aya_expanse_8b_vllm"]
    
    if historyChat:
        for mes in historyChat:
            if 'answer' in mes['content']:
                mes['content'] = mes['content']['answer']
            if 'Nguồn:' in mes['content']:
                mes['content'] = " ".join(mes['content'].split('Nguồn:')[0])
            elif 'Source:' in mes['content']:
                mes['content'] = " ".join(mes['content'].split('Source:')[0])
    # print('historyChat:',historyChat)
    # xin cực kỳ lưu ý ràng chỗ này history đã có 1 message là question của user nha chứ k phải []

    answer = ""
    source = []
    if sysMode == "RAG":
        if llm == "aya-expanse-8b":
            collection_name_inVS = f"hello{collection_name_inVS}" if collection_name_inVS else None                
            for response_chunk in chatbot_aya_expanse_8b.chat_stream(query=question, historyChat=historyChat, collection_name = collection_name_inVS, file_names = fileNames):
                if type(response_chunk) == str:
                    if response_chunk != "[END]":
                        answer += response_chunk
                    await websocket.send_text(response_chunk)
                elif type(response_chunk) == list:
                    source = response_chunk
                    await websocket.send_text(json.dumps(response_chunk)) # gửi đi str      
            await websocket.close()