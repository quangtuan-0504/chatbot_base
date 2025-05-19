from openai import OpenAI

# Cấu hình API OpenAI để sử dụng vLLM
openai_api_key = "hehedegicungdc"
openai_api_base = "http://localhost:8320/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)


# # Dữ liệu mẫu
# query = "100 + 100 = ?"
# chat_history = "1 + 1 =? 1 + 1 =2"
# print(f"""You are a smart and helpful AI assistant, based on the provided dialogue answer the user's question accurately and concisely .\
#        Conversation : {chat_history}\
#         Question: {query}\
#             Answer: """)
# # Gửi request đến vLLM : sử dụng một giao diện python do OpenAI cung cấp để tương tác với server
# completion = client.completions.create(model="kevinbazira/aya-expanse-8b-awq-4bit",
                                    
#                                       prompt=f"""You are a smart and helpful AI assistant, based on the provided dialogue answer the user's question accurately and concisely .
#                                                 Conversation : {chat_history}
#                                                 Question: {query}
#                                                 Answer: """)
# print("Completion result:", completion.choices[0].text)




# Dữ liệu mẫu
query = "100 + 100 = ?"
chat_history = [
    {"role": "user", "content": "1+1 = ?"},
    {"role": "assistant", "content": "1+1 = 2"}
]
# retrieved_context = """
# Elasticsearch is a distributed search engine used for efficient data indexing and querying.
# LangChain can integrate with Elasticsearch via ElasticVectorSearch for embedding storage and text searching.
# """

messages = [
                {"role": "system", "content": "You are a helpful AI assistant.   Based on the conversation between User and assistant. Just answer the last question of User and do nothing else. "}
            ]
# # Thêm lịch sử chat
messages.extend(chat_history)
# # print(messages)

# Thêm câu hỏi hiện tại
messages.append({"role": "user", "content": query})

# Gửi request đến vLLM : sử dụng một giao diện python do OpenAI cung cấp để tương tác với server
response = client.chat.completions.create(
        model= "kevinbazira/aya-expanse-8b-awq-4bit",  # Đảm bảo model này đã được chạy trên vLLM
        messages=messages,
        max_tokens=512,
        temperature=0.1,
        stream= True
)

# print(response.choices[0].message.content)
# for chunk in response:
#     if chunk.choices[0].delta.content is not None:
#         print(chunk.choices[0].delta.content, end="")
# print("\n")
def res(response):
    for chunk in response:
        chunk_text =  chunk.choices[0].delta.content
        print("chunk_text:",chunk_text)
        yield chunk_text
    yield [1,2,3,4,5]
    yield "[END]"
for chunk in res(response):# duyệt qua tất cả các yield
    print("chunk:",chunk)




# # Dữ liệu mẫu
# query = "How to integrate LangChain with Elasticsearch?"
# chat_history = [
#     {"role": "user", "content": "I want to learn about Elasticsearch."},
#     {"role": "assistant", "content": "Elasticsearch is a data search and analytics engine based on Lucene."}
# ]
# retrieved_context = """
# Elasticsearch is a distributed search engine used for efficient data indexing and querying.
# LangChain can integrate with Elasticsearch via ElasticVectorSearch for embedding storage and text searching.
# """

# # Xây dựng danh sách messages cho OpenAI API
# messages = [
#     {"role": "system", "content": "You are an AI assistant."},
# ]

# # Thêm thông tin từ RAG vào prompt
# if retrieved_context:
#     messages.append({"role": "system", "content": f"Related Information: {retrieved_context}"})

# # Thêm lịch sử chat
# messages.extend(chat_history)

# # Thêm câu hỏi hiện tại
# messages.append({"role": "user", "content": query})

# # Gửi request đến vLLM
# response = client.chat.completions.create(
#     model="kevinbazira/aya-expanse-8b-awq-4bit",  # Đảm bảo model này đã được chạy trên vLLM
#     messages=messages,
#     max_tokens=512,
#     temperature=0.7
# )

# # In kết quả
# print(response.choices[0].message.content)