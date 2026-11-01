#!/usr/bin/env bash
# Llama 3.3 70B Instruct (bf16) on GPUs 0,1 (tensor parallel 2), port 8040, served-model-name llama-3.3-70b
cd /diskthalys/ssd14ta/yharada/vllm-server
LOG=logs/ugr_llama33_70b_$(date +%Y%m%d_%H%M).log
MODEL=meta-llama/Llama-3.3-70B-Instruct NAME=llama-3.3-70b GPUS=0,1 PORT=8045 LEN=32768 BATCH=8192 UTIL=0.90 setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
echo started "$LOG"
