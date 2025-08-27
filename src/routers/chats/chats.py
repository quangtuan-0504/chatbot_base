from fastapi import APIRouter, HTTPException, WebSocket
from bson import ObjectId
from ...tools.load_resources import resource
# print("Resource after import:", resource)
from src.schemas.model_request import requestGetChat
from datetime import datetime , timezone
import json

router = APIRouter(
    prefix="/api/chat"
)


@router.get("/list-chats/{userId}")
async def get_list_chat_of_user(userId):
    # print(resource)
    db = resource["mongoDB"]
    chat_table = db["chats"]
    lst_chat = chat_table.find(
        {"userId": userId},
        {"_id": 1,"title": 1, "createAt": 1 , "updateAt" : 1}
    )
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
async def get_chat_history(chatId: str, request: requestGetChat):
    db = resource["mongoDB"]
    userId= request.userId
    chat_table = db["chats"]
    chat = chat_table.find_one({"_id": ObjectId(chatId), "userId": userId})
    # print(chat)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"chat_id": str(chat['_id']) ,"history":chat['history']}


@router.post("/delete-chat/{chatId}")
async def delete_chat(chatId: str):
    db = resource["mongoDB"]
    chat_table = db["chats"]
    try:
        # Kiểm tra nếu chatId có thể chuyển thành ObjectId
        query = {"_id": ObjectId(chatId)}

        result = chat_table.delete_one(query)
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Chat not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete chat failed: {str(e)}")
    
    return {"message": "Delete chat successfully!"}


@router.websocket("/chat-stream")
async def stream_chat_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        # Nhận và kiểm tra dữ liệu từ client
        data = await websocket.receive_text()
        try:
            request = json.loads(data)
        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({"type": "error", "data": "Invalid JSON format"}))
            await websocket.close()
            raise HTTPException(status_code=400, detail="Invalid JSON format")

        # Kiểm tra các trường bắt buộc
        required_fields = ["userId", "question", "LLM", "sysMode"]
        for field in required_fields:
            if field not in request or request[field] is None:
                await websocket.send_text(json.dumps({"type": "error", "data": f"Missing or invalid field: {field}"}))
                await websocket.close()
                raise HTTPException(status_code=400, detail=f"Missing or invalid field: {field}")

        user_id = request["userId"]
        question = request["question"]
        chat_id = request.get("chatId")
        file_names = request.get("fileNames")
        collection_name_inVS = request.get("collection_name_inVS")
        llm = request["LLM"]
        sys_mode = request["sysMode"]

        if not question or not isinstance(question, str):
            await websocket.send_text(json.dumps({"type": "error", "data": "Question is required and must be a string"}))
            await websocket.close()
            raise HTTPException(status_code=400, detail="Question is required and must be a string")

        print("gửi request thành công")
        print("chatId:", chat_id)
        print(question)
        print(type(collection_name_inVS))
        print('collection_name_inVS:', collection_name_inVS)
        print("file_names:", file_names)

        db = resource["mongoDB"]
        chat_table = db['chats']
        history_chat_processed = []
        if chat_id:
            chat = chat_table.find_one({"_id": ObjectId(chat_id), "userId": user_id})
            if not chat:
                await websocket.send_text(json.dumps({"type": "error", "data": "Chat not found or you don't have permission"}))
                await websocket.close()
                raise HTTPException(status_code=403, detail="Chat not found or you don't have permission")
            history_chat = chat['history']
            if not history_chat:
                await websocket.send_text(json.dumps({"type": "error", "data": "Chat history not found"}))
                await websocket.close()
                raise HTTPException(status_code=404, detail="Chat history not found")
            for mes in history_chat:
                if not isinstance(mes, dict) or "role" not in mes or "content" not in mes:
                    await websocket.send_text(json.dumps({"type": "error", "data": "Invalid chat history format"}))
                    await websocket.close()
                    raise HTTPException(status_code=500, detail="Invalid chat history format")
                content = mes["content"]
                if isinstance(content, dict) and "answer" in content:
                    content = content["answer"]
                if isinstance(content, str):
                    if "Nguồn:" in content:
                        content = " ".join(content.split("Nguồn:")[0])
                    elif "Source:" in content:
                        content = " ".join(content.split("Source:")[0])
                history_chat_processed.append({
                    "role": mes["role"],
                    "content": content
                })

        gpt4omini = resource["gpt-4o-mini"]
        answer = ""
        source = []
        if sys_mode == "RAG":
            if llm in ["aya-expanse-8b", "gpt-4o-mini"]:
                collection_name_inVS = f"hello{collection_name_inVS}" if collection_name_inVS else None
                for response_chunk in gpt4omini.chat_stream(query=question, history_chat=history_chat_processed, collection_name=collection_name_inVS, file_names=file_names):
                    if isinstance(response_chunk, str):
                        if response_chunk != "[END]":
                            answer += response_chunk
                            await websocket.send_text(json.dumps({"type": "answer_chunk", "data": response_chunk}))
                        else:
                            await websocket.send_text(json.dumps({"type": "end_chunk", "data": response_chunk}))
                    elif isinstance(response_chunk, list):
                        source = response_chunk
                        await websocket.send_text(json.dumps({"type": "source", "data": response_chunk}))
            else:
                await websocket.send_text(json.dumps({"type": "error", "data": f"Unsupported LLM: {llm}"}))
                await websocket.close()
                raise HTTPException(status_code=400, detail=f"Unsupported LLM: {llm}")
        else:
            await websocket.send_text(json.dumps({"type": "error", "data": f"Invalid sys_mode: {sys_mode}"}))
            await websocket.close()
            raise HTTPException(status_code=400, detail=f"Invalid sys_mode: {sys_mode}")

        if chat_id is None or chat_id == "":
            chat = {
                "title": question[:40],
                "userId": user_id,
                "createAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "updateAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "history": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": {"answer": answer, "source": source}}
                ]
            }
            new_chat = chat_table.insert_one(chat)
            chat_id = str(new_chat.inserted_id)
        else:
            new_items = []
            if history_chat_processed and history_chat_processed[-1]["role"] == "assistant":
                new_items.append({"role": "user", "content": question})
            new_items.append({"role": "assistant", "content": {"answer": answer, "source": source}})
            result = chat_table.update_one(
                {"_id": ObjectId(chat_id), "userId": user_id},
                {"$set": {"updateAt": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}, "$push": {"history": {"$each": new_items}}}
            )
            if result.modified_count == 0:
                await websocket.send_text(json.dumps({"type": "error", "data": "Chat not found or not updated"}))
                await websocket.close()
                raise HTTPException(status_code=404, detail="Chat not found or not updated")

        # Gửi chat_id đến client
        await websocket.send_text(json.dumps({"type": "chatId", "data": chat_id}))

        # Đóng kết nối WebSocket
        await websocket.close()

    except HTTPException as e:
        await websocket.send_text(json.dumps({"type": "error", "data": str(e.detail)}))
        await websocket.close()
        raise
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "data": f"Unexpected error: {str(e)}"}))
        await websocket.close()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")