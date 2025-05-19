from dotenv import load_dotenv
from dotenv import find_dotenv


import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),)))
from src.helpers.mongoDB.getMongoDB import  get_mongoDB
from src.config.load_config import config
from src.tools.indexingMilvus import IndexingMilvus
from src.tools.retrievalAndGeneration import ChatbotRAG

env_file = find_dotenv()
load_dotenv(env_file)


db = get_mongoDB()


if config["SERVICE_VECTOR_STORE"] == "MILVUS":
    providerModelEmb = config["PROVIDER_MODEL_EMB"]
    indexing = IndexingMilvus(providerModelEmb=providerModelEmb)
    # indexing = None # test mà ko cần load model
elif config["SERVICE_VECTOR_STORE"] == "QDRANT":
    pass
if config["HUGGINGFACE_MODEL"]["CHAT_MODEL_PATH"]["aya-expanse-8b"]:
    chatbot_aya_expanse_8b = ChatbotRAG(providerModelChat="HUGGINGFACE",modelId="aya-expanse-8b")
    # chatbot_aya_expanse_8b= None
# if config["OPENAI_API_MODEL"]["CHAT_MODEL"]["gpt-4o-mini"]:
#     chatbot_gpt4o_mini = ChatbotRAG(providerModelChat="OPENAIAPI",modelId="gpt-4o-mini")
# if config["OPENAI_API_MODEL"]["CHAT_MODEL"]["gpt-4o"]:
#     chatbot_gpt4o_mini = ChatbotRAG(providerModelChat="OPENAIAPI",modelId="gpt-4o")