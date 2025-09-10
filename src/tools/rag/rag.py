import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..'))) # thư mục cha của file hiện tại nhảy ra 2 nấc "src\tools\rag\..\.."

from tools.rag.prompts import PROMPT, PROMPT_GPT
from typing import List
from openai import OpenAI
from pymilvus import MilvusClient

from tools.rag.searchers import vicinity_search
from loggers.logapp import logger



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
            logger.info(f"have collection")
            start = time.time()
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
            logger.info(f"search time: {time.time()-start}")
            # logger.info(f"Total text retrieved: {total_text_retrieved}")

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
            logger.info(f"no collection")
            
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
class ChatbotRAGvLLM:
    def __init__(
        self,
        model_name= None
    ):
        """
        Initialize the ChatbotRAGvLLM instance

        Args:
            provider_model_embedding: The embedding provider to use
            model_name: The name of the LLM model to use
        """
        if model_name is None:
            model_name = os.getenv("LLM_MODEL")

        openai_api_key = "Placeholder_API_KEY"  # Placeholder API key
        openai_api_base = os.getenv("VLLM_LLM_API")

        self.client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_api_base,
        )

        self.model_name = model_name
        self.embeddings = get_embedding_model()

    def _process_relevant_docs(self, relevant_docs):
        """Process retrieved documents and format them for the prompt"""
        lst_file_relevant = []
        res_retrieval = ""
        dic_doc_texts_relevant = defaultdict(list)

        for langchain_doc in relevant_docs:
            LOGGER.debug(str(langchain_doc))
            LOGGER.debug(str(langchain_doc.metadata))
            file_name = langchain_doc.metadata['file_name']
            file_id = langchain_doc.metadata['file_id']

            dic_doc_texts_relevant[file_name].append(langchain_doc.page_content)

            check_file_exist = 0
            for file in lst_file_relevant:
                if file_id == file['file_id']:
                    check_file_exist = 1
                    break

            if check_file_exist == 0:
                lst_file_relevant.append({'file_name': file_name , 'file_id': file_id})

        for k, v in dic_doc_texts_relevant.items():
            res_retrieval += "\n".join(v) + f"\nthe above information is taken from file: {k}\n\n"

        return res_retrieval, lst_file_relevant

    def _prepare_messages(self, query: str, history_chat: List[Dict[str, str]], context: str = ""):
        """
        Prepare messages for the chat completion
        history_chat: 
            - role: assistant / user
            - content: "answer"
        """

        if context:
            system_content = RAG_SYSTEM_PROMPT.format(query=query)
            system_content += f"\ncontext information: {context}"
            messages = [{"role": "system", "content": system_content}]
        else:
            messages = [{"role": "system", "content": GENERAL_SYSTEM_PROMPT}]

        messages.extend(history_chat)

        # Make sure the last message is from the user
        if not history_chat or messages[-1]["role"] == "assistant":
            messages.append({"role": "user", "content": query})

        return messages

    def chat_stream(self, query: str, history_chat: List[Dict[str, str]] = [],
                   collection_name: Optional[str] = None, 
                   file_ids: Optional[List[str]] = None,
                   file_names: Optional[List[str]] = None,

        ) -> Generator:
        """
        Stream chat with the bot

        Args:
            query: User's input question/message
            history_chat: List of previous messages in the conversation
            collection_name: The name of the collection to search in
            file_ids: List of file id to filter results
            file_names: List of file name to filter results

        Yields:
            Chunks of the response and finally the sources and an end marker
        """
        context = ""
        lst_file_relevant = []
        lst_img = []
        if collection_name:



            client_milvus = get_milvus_connection()
            response_emb = self.embeddings.embed_query(query)

            query_vector = response_emb
            context, lst_file_relevant, lst_img  = vicinity_search(
                client = client_milvus ,
                query_vector = query_vector,
                file_ids = file_ids,
                collection_name= collection_name 
            )

            # print("context:", context)
            # print("lst_file_relevant:",lst_file_relevant)



        messages = self._prepare_messages(query, history_chat, context)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=512,
            temperature=0.1,
            stream=True
        )

        for chunk in response:
            chunk_text = chunk.choices[0].delta.content
            if chunk_text:
                yield chunk_text

        yield lst_file_relevant if collection_name else []

        # get image from MinIO and convert it into format base64.
        print("lst_img:",lst_img )
        lst_img_base64 = [get_file_from_minio(object_name=img_path, return_type="base64") for img_path in lst_img]

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