from fastapi import APIRouter, HTTPException, WebSocket
from bson import ObjectId
from ..tools.load_resources import resource
# print("Resource after import:", resource)
from src.data_models.chat_dataclass import GetChatRequest
from datetime import datetime , timezone
import json

router = APIRouter()


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
async def get_chat_history(chatId: str, request: GetChatRequest):
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
        required_fields = ["userId", "question", "modelName"]
        for field in required_fields:
            if field not in request or request[field] is None:
                await websocket.send_text(json.dumps({"type": "error", "data": f"Missing or invalid field: {field}"}))
                await websocket.close()
                raise HTTPException(status_code=400, detail=f"Missing or invalid field: {field}")

        user_id = request["userId"]
        question = request["question"]
        chat_id = request.get("chatId")
        file_ids = request.get("fileIds")
        collection_id = request.get("collectionId")
        model_name = request["modelName"]

        if not question or not isinstance(question, str):
            await websocket.send_text(json.dumps({"type": "error", "data": "Question is required and must be a string"}))
            await websocket.close()
            raise HTTPException(status_code=400, detail="Question is required and must be a string")

        print("gửi request thành công")
        print("chatId:", chat_id)
        print(question)
        print(type(collection_id))
        print('collection_name_inVS:', collection_id)
        print("file_ids:", file_ids)

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

        gpt4omini = resource["aya-expanse-8b"]
        answer = ""
        source = []
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
    
chatbot_model = ChatbotRAG()
chat_service = ChatService()
mongo_conn = MongoDBConnections()
@sio.event
async def chat(sid, data):
    """Handle chat streams with authentication and authorization"""
    LOGGER.info(f'Starting stream for client: {sid}')
    try:
        # Check if client is authenticated
        if sid not in active_clients:
            LOGGER.warning(f'Unauthenticated client {sid} attempted to chat')
            await sio.emit('error', 'Not authenticated', room=sid)
            return

        client_info = active_clients[sid]
        authenticated_user = client_info['user']
        authenticated_user_id = client_info['user_id']

        # Update client status
        client_info['active_chat'] = True
        client_info['last_activity'] = time.time()

        # Parse incoming data
        LOGGER.debug(f"Raw data: {data}")
        if not isinstance(data, dict):
            data = json.loads(data)

        LOGGER.debug(f"Parsed data: {data}")

        # Validate required fields
        for key in ['question']:
            if key not in data:
                LOGGER.warning(f"Missing required field: {key}")
                await sio.emit('stream_end', room=sid)
                await clean_up_connection(active_clients, sio, sid)
                return

        query = data['question']
        collection_id = data.get('collectionId', None)
        chat_id = data.get('chatId', None)
        # Use authenticated user ID instead of trusting client-provided userId
        user_id = authenticated_user_id
        file_ids = data.get('fileIds', [])
        LOGGER.debug(f"Received query: {query}, collection_id: {collection_id}, chat_id: {chat_id}, user_id: {user_id}, file_ids: {file_ids}")
        # Verify collection ownership if collection_id is provided
        if collection_id:
            if not await verify_collection_ownership(collection_id, authenticated_user):
                LOGGER.warning(f'User {authenticated_user["username"]} attempted to access unauthorized collection {collection_id}')
                await sio.emit('error', 'Unauthorized access to collection', room=sid)
                await clean_up_connection(active_clients, sio, sid)
                return

        # Verify chat ownership if chat_id is provided
        if chat_id:
            if not await verify_chat_ownership(chat_id, authenticated_user):
                LOGGER.warning(f'User {authenticated_user["username"]} attempted to access unauthorized chat {chat_id}')
                await sio.emit('error', 'Unauthorized access to chat', room=sid)
                await clean_up_connection(active_clients, sio, sid)
                return

        if chat_id is None or chat_id == "":
            # Create a new chat and ensure we get a valid chat ID
            try:
                chat_id = await asyncio.to_thread(chat_service.create_new_chat, user_id, collection_id, query)
                LOGGER.info(f"Created new chat with ID: {chat_id}")
            except Exception as e:
                LOGGER.error(f"Failed to create new chat: {str(e)}")
                await sio.emit('error', 'Failed to create new chat', room=sid)
                await clean_up_connection(active_clients, sio, sid)
                return

        # Get chat history
        history_chat_process = []
        if chat_id:
            history_chat = await asyncio.to_thread(chat_service.get_chat_history, chat_id=chat_id)
            for mes in history_chat['history']:
                if 'Nguồn:' in mes['content']:
                    mes['content'] = " ".join(mes['content'].split('Nguồn:')[0])
                elif 'Source:' in mes['content']:
                    mes['content'] = " ".join(mes['content'].split('Source:')[0])
                history_chat_process.append({
                    'role': mes['role'],
                    'content': mes['content']
                })

        # Get chat stream response
        answer_generator = await asyncio.to_thread(
            chatbot_model.chat_stream,
            query=query,
            history_chat=history_chat_process,
            collection_name=collection_id,
            file_ids=file_ids
        )

        await sio.emit('stream_begin', {'sid': sid, 'metadata': {'chatId': chat_id}}, room=sid)

        results = []
        list_files_relevant = []

        for chunk in answer_generator:
            if isinstance(chunk, str):
                await sio.emit('stream_data', {'answer': chunk}, room=sid)
                results.append(chunk)

            elif isinstance(chunk, list):
                await sio.emit('relevant_files', {'files': chunk}, room=sid)
                list_files_relevant = chunk
                LOGGER.debug(f"relevant_files: {len(chunk)} files")

            elif isinstance(chunk, dict):
                await sio.emit('lst_img', {'imgs': chunk['lst_img']}, room=sid)
                LOGGER.debug(f"lst_img: {len(chunk['lst_img'])} imgs")
                break

        await sio.emit('stream_end', room=sid)
        LOGGER.info(f"Stream ended for client: {sid}")

        answer = "".join(results)

        # Update chat history
        success = await asyncio.to_thread(
            chat_service.update_chat_history,
            chat_id=chat_id,
            question=query,
            answer=answer,
            user_list_files=file_ids,
            list_files_relevant=list_files_relevant
        )
        if not success:
            LOGGER.warning(f"Failed to update chat history for chat_id: {chat_id}")

        # Clean up the connection
        await clean_up_connection(active_clients, sio, sid)

    except json.JSONDecodeError:
        LOGGER.error(f"Invalid JSON data received from {sid}")
        await sio.emit('error', 'Invalid data format', room=sid)
        await clean_up_connection(active_clients, sio, sid)

    except Exception as e:
        LOGGER.error(f"Error processing stream for {sid}: {str(e)}", exc_info=True)
        await sio.emit('error', f'Server error occurred: {str(e)}', room=sid)
        await clean_up_connection(active_clients, sio, sid)
 