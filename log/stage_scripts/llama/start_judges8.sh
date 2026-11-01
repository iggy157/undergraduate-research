#!/usr/bin/env bash
# judges on 6 GPUs: Llama 3.3 70B on (1,2):8040 and (6,7):8045, gpt-oss-120b on 4:8060 and 5:8065 (temperature 0 clients, no batch-invariant)
cd /diskthalys/ssd14ta/yharada/vllm-server
ts=$(date +%Y%m%d_%H%M)
MODEL=meta-llama/Llama-3.3-70B-Instruct NAME=llama-3.3-70b GPUS=1,2 PORT=8040 LEN=32768 BATCH=8192 UTIL=0.90 setsid nohup ./start.sh > logs/ugr_llama33_70b_${ts}_a.log 2>&1 < /dev/null &
MODEL=meta-llama/Llama-3.3-70B-Instruct NAME=llama-3.3-70b GPUS=6,7 PORT=8045 LEN=32768 BATCH=8192 UTIL=0.90 setsid nohup ./start.sh > logs/ugr_llama33_70b_${ts}_b.log 2>&1 < /dev/null &
MODEL=openai/gpt-oss-120b NAME=gpt-oss-120b GPUS=4 PORT=8060 LEN=32768 BATCH=8192 UTIL=0.90 setsid nohup ./start.sh > logs/ugr_gptoss120b_${ts}_a.log 2>&1 < /dev/null &
MODEL=openai/gpt-oss-120b NAME=gpt-oss-120b GPUS=5 PORT=8065 LEN=32768 BATCH=8192 UTIL=0.90 setsid nohup ./start.sh > logs/ugr_gptoss120b_${ts}_b.log 2>&1 < /dev/null &
echo started judges
