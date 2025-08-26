import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..')))

from src.utils.prompts.prompts import PROMPT, PROMPT_GPT
from typing import List
from openai import OpenAI
from pymilvus import MilvusClient

from src.utils.searchers import vicinity_search



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
    def chat_stream(self, query: str, history_chat, collection_name : str | None  = None, file_names : List | None = None):
        """
        Chat with the bot

        Args:
            query: User's input question/message

        Returns:
            str: Bot's response
        """
        if collection_name:
            print("have collection")
            start = time.time()
            # query_vector = self.embeddings.embed_query(query)
            response_emb = self.client_embedding_model.embeddings.create(
                input=query,
                model=self.embedding_model_name
            )
            # print(response_emb)

            query_vector = response_emb.data[0].embedding

            total_text_retrieved , lst_file_relevant = vicinity_search(
                client=self.milvus_client,
                query_vector=query_vector,
                collection_name=collection_name,
                limit=3,
                file_names=file_names,
                metric_type='COSINE',
                upper_bound = 1,
                lower_bound = 1 
            )
            print("search time:", time.time()-start)
            print(total_text_retrieved)
            
            # Xây dựng danh sách messages cho OpenAI API
            messages = [
                { "role": "system", "content": PROMPT_GPT.format(
                        query_ = query
                    )
                },
            ]
            # Thêm thông tin từ RAG vào prompt
            if total_text_retrieved:
                messages[0]['content'] += f"\ncontext information : {total_text_retrieved}"

            # Thêm lịch sử chat
            messages.extend(history_chat)

            # Thêm câu hỏi hiện tại
            if messages[-1]["role"] == "assistant" or len(messages)==1:
                messages.append({"role": "user", "content": query})

            # print("messages:", messages)

            response = self.client_chat_model.chat.completions.create(
                    model= self.chat_model_name,  # Đảm bảo model này đã được chạy trên vLLM
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.1,
                    stream = True
            )


            for chunk in response:
                chunk_text =  chunk.choices[0].delta.content
                # print(chunk_text)
                if chunk_text:
                    yield chunk_text
            yield lst_file_relevant
            yield "[END]"
        else:
            print("no collection")
            
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant.   Based on the conversation between User and assistant. Just answer the last question of User and do nothing else. "}
            ]
            # Thêm lịch sử chat
            messages.extend(history_chat)
            
            # Thêm câu hỏi hiện tại
            if messages[-1]["role"]== "assistant" or len(messages)==1:
                messages.append({"role": "user", "content": query})

            # Gửi request đến vLLM : sử dụng một giao diện python do OpenAI cung cấp để tương tác với server
            response = self.client_chat_model.chat.completions.create(
                    model= self.chat_model_name,  # Đảm bảo model này đã được chạy trên vLLM
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.1,
                    stream= True
            )
            
            for chunk in response:
                chunk_text =  chunk.choices[0].delta.content
                if chunk_text:
                    yield chunk_text
            yield []
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