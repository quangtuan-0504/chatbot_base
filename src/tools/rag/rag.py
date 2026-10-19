import os
import time
from dataclasses import asdict

from src.tools.rag.prompts import prompts, QUERY_REWRITE_PROMPT
from typing import List, Dict, Optional, Tuple, Generator
from openai import OpenAI
from pymilvus import MilvusClient
from collections import defaultdict
from src.tools.rag.searchers import vicinity_search
from src.tools.rag.search_metrics import SearchMetrics
from src.tools.intergrations.minio_tools import get_file_from_minio
from src.loggers.logapp import logger
from src.configs import settings
from src.helpers.minio import minio_client


def temperature_kwargs() -> Dict:
    """Pass temperature only when RAG_TEMPERATURE is set; some models (e.g. reasoning models) reject the parameter."""
    return {} if settings.RAG_TEMPERATURE is None else {"temperature": settings.RAG_TEMPERATURE}


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
    def _rewrite_query(self, query: str, history_chat: List[Dict], metrics: Optional[SearchMetrics] = None) -> str:
        """
        Rewrite a follow-up question into a standalone question using the last turns of history.
        Only used for vector search; falls back to the original query on any failure.
        Token usage and latency of the rewrite call are recorded in metrics.
        """
        metrics = metrics or SearchMetrics()
        n_messages = settings.RAG_REWRITE_HISTORY_TURNS * 2 # 1 turn = user + assistant
        if not history_chat or n_messages <= 0:
            return query

        lines = []
        for message in history_chat[-n_messages:]:
            content = message.get("content", "")
            if isinstance(content, list): # multimodal content: keep text parts only
                content = " ".join(part.get("text", "") for part in content if part.get("type") == "text")
            if content:
                lines.append(f"{message.get('role', 'user')}: {content}")
        if not lines:
            return query

        start = time.perf_counter()
        try:
            response = self.client_chat_model.chat.completions.create(
                model=self.chat_model_name,
                messages=[{
                    "role": "user",
                    "content": QUERY_REWRITE_PROMPT.format(history_="\n".join(lines), query_=query),
                }],
                max_completion_tokens=settings.RAG_REWRITE_MAX_TOKENS,
                stream=False,
                **temperature_kwargs(),
            )
            metrics.add_rewrite_usage(getattr(response, "usage", None))
            rewritten = (response.choices[0].message.content or "").strip()
        except Exception as e:
            logger.warning(f"query rewrite failed, using original query: {e}")
            return query
        finally:
            metrics.rewrite_ms = (time.perf_counter() - start) * 1000

        if not rewritten:
            logger.warning("query rewrite returned empty, using original query")
            return query
        logger.info(f"rewritten query: {query!r} -> {rewritten!r}")
        metrics.rewritten = True
        return rewritten
    def chat_stream(self, query: str,model_name: str, image_urls: List, history_chat, collection_name : str | None  = None, file_ids : List | None = None, debug: Optional[Dict] = None):
        """
        Chat with the bot

        Args:
            query: User's input question/message
            debug: optional dict filled with the search query, retrieval ranking, context and search metrics (evaluation only)

        Returns:
            str: Bot's response
        """
        context = ""
        lst_file_relevant = []
        lst_img = []
        if collection_name:
            logger.info(f"have collection")
            metrics = SearchMetrics()
            start = time.perf_counter()
            try:
                search_query = self._rewrite_query(query, history_chat, metrics)

                step = time.perf_counter()
                response_emb = self.client_embedding_model.embeddings.create(
                    input=search_query,
                    model=self.embedding_model_name
                )
                metrics.embedding_ms = (time.perf_counter() - step) * 1000
                metrics.add_embedding_usage(getattr(response_emb, "usage", None))

                query_vector = response_emb.data[0].embedding
                step = time.perf_counter()
                context, lst_file_relevant, lst_img  = vicinity_search(
                    client = self.milvus_client ,
                    query_vector = query_vector,
                    file_ids = file_ids,
                    collection_name = collection_name,
                    query_text = search_query,
                    debug = debug
                )
                metrics.vector_search_ms = (time.perf_counter() - step) * 1000
                metrics.context_chars = len(context)
                metrics.n_files = len(lst_file_relevant)
            except Exception as e:
                metrics.error = type(e).__name__
                raise
            finally:
                metrics.total_ms = (time.perf_counter() - start) * 1000
                logger.info(metrics.to_log())
                if debug is not None:
                    debug["search_query"] = search_query
                    debug["context"] = context
                    debug["search_metrics"] = asdict(metrics)

        messages = self._prepare_messages(query,model_name, image_urls, history_chat, context)

        response = self.client_chat_model.chat.completions.create(
                model= self.chat_model_name,  # Đảm bảo model này đã được chạy trên vLLM
                messages=messages,
                # max_tokens=1024, # số token dành cho toàn bộ đoạn chat, nếu để quá ít, cấu trả lời có thể bị rỗng ''.
                max_completion_tokens=settings.RAG_MAX_COMPLETION_TOKENS, # số token dành cho câu trả lời
                stream = True,
                **temperature_kwargs()
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