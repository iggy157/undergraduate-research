#!/usr/bin/env bash
# gemma-4-31B on GPU $1 port $2, batch-invariant
cd /diskthalys/ssd14ta/yharada/vllm-server
VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-31B-it NAME=gemma-4-31b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > logs/ugr_gemma-4-31b_$(date +%Y%m%d_%H%M)_gpu$1.log 2>&1 < /dev/null &
echo started
