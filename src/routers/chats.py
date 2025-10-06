from fastapi import APIRouter, HTTPException, WebSocket, Depends, Query
from typing import Annotated
import json
from fastapi.responses import JSONResponse
from dataclasses import asdict
from ..tools.load_resources import resource, provider_model
from ..data_models import *
from ..utils.auth_utils import get_current_active_user

router = APIRouter()

@router.get("/list-chats")
async def get_list_chat_of_user(
    current_user: dict = Depends(get_current_active_user),
    search: str = Query(None, description="Search chats by title")
):
    try:
        user_id = current_user['id']
        # Query MongoDB for user's chat history with optional title search
        chats = resource['chat_tool'].get_list_chat(user_id, search)
        chat_list = [ChatListItem.from_dict(chat) for chat in chats]
        chat_list = sorted(chat_list, key=lambda x: x.update_at, reverse=True)

        response = ChatListResponse(
            data=chat_list,
            total=len(chat_list)
        )

        return asdict(response)

    except Exception as e:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/chat-history/{chatId}")
async def get_chat_history(chatId: str, current_user: dict = Depends(get_current_active_user)):
    try:
        if not chatId:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_param('chatId')
                )),
                status_code=400
            )
        chat = resource['chat_tool'].get_chat(chat_id=chatId,user_id=current_user['id'])
        history = chat['history']
        if  len(history) >=50:
            history = history[-50:]
        chat_history = ChatHistory(
            chat_id=chatId,
            history=history
        )
        response = ChatHistoryResponse(data=chat_history, total=len(chat_history.history))
        return asdict(response)

    except Exception as e:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.post("/delete-chat/{chatId}")
async def delete_chat(chatId: str, current_user = Annotated[dict,Depends(get_current_active_user)]):
    """Delete a chat for the authenticated user."""
    try:
        if not chatId:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_param('chatId')
                )),
                status_code=400
            )

        # Attempt to delete the chat
        success = resource['chat_tool'].delete_chat(chat_id=chatId, user_id=current_user['id'])

        if not success:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=404,
                    message=ResponseMessage.CHAT_NOT_FOUND
                )),
                status_code=404
            )

        return asdict(BaseResponse(
            code=200,
            message=ResponseMessage.SUCCESS
        ))
    except Exception as e:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )

@router.put("/rename-chat")
async def rename_chat(request: RenameChatRequest, current_user: dict = Depends(get_current_active_user)):
    """Rename a chat for the authenticated user."""
    try:
        # Validate required parameters
        if not request.chat_id or not request.new_title:
            missing_params = []
            if not request.chat_id:
                missing_params.append('chat_id')
            if not request.new_title:
                missing_params.append('new_title')

            return JSONResponse(
                content=asdict(BaseResponse(
                    code=400,
                    message=ResponseMessage.missing_param(', '.join(missing_params))
                )),
                status_code=400
            )
        # Attempt to rename the chat
        success = resource['chat_tool'].rename_chat(request.chat_id, current_user['id'], request.new_title)

        if not success:
            return JSONResponse(
                content=asdict(BaseResponse(
                    code=404,
                    message=ResponseMessage.CHAT_NOT_FOUND
                )),
                status_code=404
            )

        return asdict(BaseResponse(
            code=200,
            message=ResponseMessage.SUCCESS
        ))
    except Exception as e:
        return JSONResponse(
            content=asdict(BaseResponse(
                code=500,
                message=ResponseMessage.error_occurred(e)
            )),
            status_code=500
        )


@router.websocket("/chat-stream")
async def stream_chat_websocket(websocket: WebSocket, current_user: Annotated[dict, Depends(get_current_active_user)]):
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
        required_fields = ["question", "modelName"]
        for field in required_fields:
            if field not in request or request[field] is None:
                await websocket.send_text(json.dumps({"type": "error", "data": f"Missing or invalid field: {field}"}))
                await websocket.close()
                raise HTTPException(status_code=400, detail=f"Missing or invalid field: {field}")

        user_id = current_user.get('id')
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

        history_chat_processed = []
        if chat_id:
            chat = resource['chat_tool'].get_chat(chat_id=chat_id,user_id=user_id)
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

        chat_model = resource[model_name] 
        answer = ""
        source = []
        if model_name in provider_model.get('openai-api', []) + provider_model.get('vllm',[]): # use dict.get instead of dict['key'] to avoid error key doesn't exist
            for response_chunk in chat_model.chat_stream(
                query=question,
                history_chat=history_chat_processed, 
                collection_name=collection_id, 
                file_ids=file_ids
            ):
                if isinstance(response_chunk, str):
                    if response_chunk != "[END]":
                        answer += response_chunk
                        await websocket.send_text(json.dumps({"type": "answer_chunk", "data": response_chunk}))
                    else:
                        await websocket.send_text(json.dumps({"type": "end_chunk", "data": response_chunk}))
                elif isinstance(response_chunk, list):
                    source = response_chunk
                    await websocket.send_text(json.dumps({"type": "source", "data": response_chunk}))
        elif model_name in provider_model.get('huggingface-transformer',[]):
            pass
        else:
            await websocket.send_text(json.dumps({"type": "error", "data": f"Unsupported LLM: {model_name}"}))
            await websocket.close()
            raise HTTPException(status_code=400, detail=f"Unsupported LLM: {model_name}")

        if chat_id is None or chat_id == "":
            chat_id = resource['chat_tool'].create_chat(
                question=question,
                user_id=user_id,
                answer=answer,
                source=source
            )
        else:
            new_items = []
            if history_chat_processed and history_chat_processed[-1]["role"] == "assistant":
                new_items.append({"role": "user", "content": question})
            new_items.append({"role": "assistant", "content": {"answer": answer, "source": source}})
            modified_count = resource['chat_tool'].update_chat_history(
                chat_id=chat_id,
                user_id=user_id,
                new_items=new_items
            )
            if modified_count == 0:
                await websocket.send_text(json.dumps({"type": "error", "data": "Chat not found or not updated"}))
                await websocket.close()
                raise HTTPException(status_code=404, detail="Chat not found or not updated")

        # Gửi chat_id đến client
        await websocket.send_text(json.dumps({"type": "chat_id", "data": chat_id}))

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