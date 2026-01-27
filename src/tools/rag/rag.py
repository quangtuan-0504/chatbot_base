import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..'))) # thư mục cha của file hiện tại nhảy ra 2 nấc "src\tools\rag\..\.."

from tools.rag.prompts import prompts
from typing import List, Dict, Optional, Tuple, Generator
from openai import OpenAI
from pymilvus import MilvusClient
from collections import defaultdict
from tools.rag.searchers import vicinity_search
from tools.intergrations.minio_tools import get_file_from_minio
from loggers.logapp import logger
from configs import settings
from helpers.minio import minio_client



class ChatbotRAGvLLM:
    def __init__(
        self,
        chat_model_name : str,
        embedding_model_name : str,
        client_chat_model: OpenAI ,
        client_embedding_model: OpenAI,
        milvus_client: MilvusClient 
    ):
        self.client_chat_model = client_chat_model
        self.chat_model_name = chat_model_name

        self.client_embedding_model = client_embedding_model
        self.embedding_model_name = embedding_model_name
        self.milvus_client = milvus_client
    def _prepare_messages(self, query: str,model_name:str, image_urls: List, history_chat: List[Dict[str, str]], context: str = ""):
        """
        Prepare messages for the chat completion
        history_chat: 
            - role: assistant / user
            - content: "text"
        """
        messages = []
        if context:
            if prompts[model_name]["rag"]:
                system_content = prompts[model_name]["rag"].format(query_=query)
                system_content += f"\ncontext information: {context}"
                messages = [{"role": "system", "content": system_content}]
        else:
            if prompts[model_name]["normal"]:
                messages = [{"role": "system", "content": prompts[model_name]["normal"]}]

        messages.extend(history_chat)

        # Make sure the last message is from the user
        if not history_chat or messages[-1]["role"] == "assistant" or len(messages)==1:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    *[
                        {"type": "image_url", "image_url": {"url": image_url}} for image_url in image_urls
                    ]
                ]})

        # print(messages[:1])
        return messages
    def chat_stream(self, query: str,model_name: str, image_urls: List, history_chat, collection_name : str | None  = None, file_ids : List | None = None):
        """
        Chat with the bot

        Args:
            query: User's input question/message

        Returns:
            str: Bot's response
        """
        context = ""
        lst_file_relevant = []
        lst_img = []
        if collection_name:
            logger.info(f"have collection")
            start = time.time()
            response_emb = self.client_embedding_model.embeddings.create(
                input=query,
                model=self.embedding_model_name
            )
            # print(response_emb)

            query_vector = response_emb.data[0].embedding
            context, lst_file_relevant, lst_img  = vicinity_search(
                client = self.milvus_client ,
                query_vector = query_vector,
                file_ids = file_ids,
                collection_name = collection_name 
            )
            logger.info(f"search time: {time.time()-start}")

        messages = self._prepare_messages(query,model_name, image_urls, history_chat, context)

        response = self.client_chat_model.chat.completions.create(
                model= self.chat_model_name,  # Đảm bảo model này đã được chạy trên vLLM
                messages=messages,
                # max_tokens=1024, # số token dành cho toàn bộ đoạn chat, nếu để quá ít, cấu trả lời có thể bị rỗng ''.
                max_completion_tokens=500, # số token dành cho câu trả lời
                temperature=0.1,
                stream = True
        )

        for chunk in response:
            chunk_text = chunk.choices[0].delta.content
            if chunk_text:
                yield chunk_text
        yield lst_file_relevant if collection_name else []
        # get image from MinIO and convert it into format base64.
        lst_img_base64 = [
            get_file_from_minio(
                minio_client=minio_client,
                bucket_name=settings.BUCKET_NAME,
                object_name=img_path, 
                return_type="base64"
            )
        for img_path in lst_img]

        yield {"lst_img":lst_img_base64}
        yield "[END]"
 

# Example usage
def main():
    # Initialize the chatbot
    chatbot = ChatbotRAGvLLM(model_name="/LLM/LLMs/kevinbazira/aya-expanse-8b-awq-4bit")

    # Example conversation

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            break

        response = chatbot.chat(query=user_input, history_chat=[])
        print(f"Bot: {response}\n\n")


if __name__ == "__main__":
    main()
    # print(type(config['LST_LLM_USE']))