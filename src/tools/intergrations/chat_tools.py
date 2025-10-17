import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..')))
from helpers.mongodb.get_mongodb import MongoDBConnections
from loggers.logapp import logger
from src.utils.timezone_utils import get_gmt7_datetime_for_db
from bson import ObjectId
from typing import List, Dict
from datetime import datetime , timezone


class ChatTool:
    def __init__(self, mongodb: MongoDBConnections = None):
        self.mongodb = mongodb
        self.chats_table = self.mongodb.CHATS

        # Create indexes for better performance
        self.chats_table.create_index([("user_id", 1),("_id",1)])
    def get_chat(self, chat_id: str, user_id: str):
        try:
            chat = self.chats_table.find_one({"user_id": user_id, "_id": ObjectId(chat_id)})
            return chat
        except Exception as e:
            logger.error(f"Error in get_chat: {str(e)}")
            raise f"Error in get_chat: {str(e)}"
    def create_chat(self,
        question: str,
        user_id: str,
        answer: str,
        source: List          
    ):
        try:
            current_time = get_gmt7_datetime_for_db().isoformat()
            chat = {
                "title": question[:40],
                "user_id": user_id,
                "create_at": current_time,
                "update_at": current_time,
                "history": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": {"answer": answer, "source": source}}
                ]
            }
            new_chat = self.chats_table.insert_one(chat)
            chat_id = str(new_chat.inserted_id)
            return chat_id
        except Exception as e:
            raise f"create new chat in mongodb faild: {str(e)}"
    def update_chat_history(self,
        chat_id: str,
        user_id: str,
        new_items: List[Dict]
    ):  
        try:
            current_time = get_gmt7_datetime_for_db().isoformat()
            result = self.chats_table.update_one(
                {"user_id": user_id, "_id": ObjectId(chat_id)},
                {
                    "$set": {"update_at": current_time}, 
                    "$push": {"history": {"$each": new_items}}
                }
            )
            return result.modified_count
        except Exception as e:
            raise f"update chat history in mongodb faild: {str(e)}"
    def delete_chat(self, chat_id: str, user_id: str):
        try:
            query = {"user_id": user_id, "_id": ObjectId(chat_id)}
            result = self.chats_table.delete_one(query)
            if result.deleted_count == 0:
                return False
            return True
        except Exception as e:
            raise f"Delete chat failed: {str(e)}"
    def get_list_chat(self, user_id: str, search: str = None):
        try:
            query = {"user_id": user_id}
            
            # Add title search filter if search parameter is provided
            if search:
                query["title"] = {"$regex": search, "$options": "i"}  # Case-insensitive search
            
            lst_chat = self.chats_table.find(
                query,
                {"_id": 1,"title": 1, "create_at": 1 , "update_at" : 1}
            )
            if not lst_chat:
                return []
            return lst_chat
        except Exception as e:
            raise f"not found list chat of user: {user_id} in mongodb: {str(e)}"
    def rename_chat(self, chat_id: str, user_id: str, new_title: str):
        try:
            query = {"user_id": user_id, "_id": ObjectId(chat_id)}
            result = self.chats_table.update_one(
                query,
                {
                    "$set": {"title": new_title}
                }

            )
            if not result:
                return False
            return True
        except Exception as e:
            raise f"Rename chat failed: {str(e)}"
