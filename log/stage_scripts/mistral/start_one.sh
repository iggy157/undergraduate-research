#!/usr/bin/env bash
# Mistral-Small-3.2-24B on GPU $1 port $2, batch-invariant, mistral tokenizer/config/load format, no images
cd /diskthalys/ssd14ta/yharada/vllm-server
VLLM_BATCH_INVARIANT=1 MODEL=mistralai/Mistral-Small-3.2-24B-Instruct-2506 NAME=mistral-small-3.2-24b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--tokenizer-mode mistral --config-format mistral --load-format mistral --limit-mm-per-prompt {"image":0}' setsid nohup ./start.sh > logs/ugr_mistral_small32_$(date +%Y%m%d_%H%M)_gpu$1.log 2>&1 < /dev/null &
echo started
