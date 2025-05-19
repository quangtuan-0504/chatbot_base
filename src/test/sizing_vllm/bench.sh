#bench.sh
# Quy trình chạy code benchmark vLLM.
# Code trong repo này : https://github.com/vllm-project/vllm/blob/main/benchmarks/README.md
# clone source code về, cd vô đúng thư mục repo
# tạo venv, kích hoạt venv, cài thư viện vllm và các thư viện cần thiết.
# các bước cơ bản là sẽ chạy theo như trong hướng dẫn này : https://github.com/vllm-project/vllm/blob/main/benchmarks/README.md
# đọc kĩ hướng dẫn trước khi chạy.
# tạo file shell script .sh để chạy các lệnh như trong hướng dẫn dễ dàng hơn . chỉnh các tham số cho phù hợp, tham số của model, data. 
# trong hướng dẫn sẽ có các option dataset test cho mình chọn. vô file code xem thêm để hiểu rõ các tham số này.
# fix bug tham số : https://github.com/vllm-project/vllm/issues/10158


# giải thích đầu ra : https://grok.com/share/bGVnYWN5_c7db9120-e3c7-45e2-983f-0b29b598ee8c

# download dataset
# wget https://huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered/resolve/main/ShareGPT_V3_unfiltered_cleaned_split.json
MODEL_NAME="/home/data/LLM/LLMs/kevinbazira/aya-expanse-8b-awq-4bit"
NUM_PROMPTS=100
BACKEND="vllm"
# BACKEND="openai-chat"
DATASET_NAME="sonnet"
HOST="10.18.27.59"
PORT="8000"
DATASET_PATH="/home/tuanndq/test_chatbot/vllm/benchmarks/sonnet.txt"


python3 ./benchmarks/benchmark_serving.py --backend ${BACKEND}  \
                                --host ${HOST} --port ${PORT} \
                                --model ${MODEL_NAME}  \
                                --endpoint /v1/completions \
                                --dataset-name ${DATASET_NAME} \
                                --dataset-path ${DATASET_PATH} \
                                --num-prompts ${NUM_PROMPTS} \
                                --request-rate 100 \
                                --served-model-name /LLM/LLMs/kevinbazira/aya-expanse-8b-awq-4bit




# backend='vllm', base_url=None, host='127.0.0.1', port=8000, endpoint='/v1/completions', dataset_name='sonnet',
# dataset_path='/home/tuanndq/test_chatbot/vllm/benchmarks/sonnet.txt', max_concurrency=None, model='/home/data/LLM/LLMs/kevinbazira/aya-expanse-8b-awq-4bit',
# tokenizer=None, use_beam_search=False, num_prompts=10, logprobs=None, request_rate=inf, burstiness=1.0, seed=0, trust_remote_code=False, disable_tqdm=False, 
# profile=False, save_result=False, save_detailed=False, metadata=None, result_dir=None, result_filename=None, ignore_eos=False,
# percentile_metrics='ttft,tpot,itl', metric_percentiles='99', goodput=None, sonnet_input_len=550, sonnet_output_len=150, sonnet_prefix_len=200, 
# sharegpt_output_len=None, random_input_len=1024, random_output_len=128, random_range_ratio=1.0,
# random_prefix_len=0, hf_subset=None, hf_split=None, hf_output_len=None, tokenizer_mode='auto', served_model_name=None, lora_modules=None