#!/usr/bin/env bash
# two batch-invariant vLLM instances of gemma-4-31B on GPU 6 (:8000) and GPU 7 (:8001)
cd /diskthalys/ssd14ta/yharada/vllm-server
for pair in "6 8000" "7 8010"; do
  set -- $pair
  LOG=logs/ugr_gemma4_31b_$(date +%Y%m%d_%H%M)_gpu$1.log
  VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-31B-it NAME=gemma-4-31b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
done
echo started
