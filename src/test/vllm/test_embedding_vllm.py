from openai import OpenAI

# Cấu hình API OpenAI để sử dụng vLLM
openai_api_key = "hehedegicungdc"
openai_api_base = "http://localhost:8320/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

response = client.embeddings.create(
    input="how are you ?",
    model="/home/tuanndq/test_chatbot/download_model/model/embedding_models/bge/bge-m3-model"
)

print(response.data[0].embedding)