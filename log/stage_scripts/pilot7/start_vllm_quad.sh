#!/usr/bin/env bash
# four batch-invariant vLLM instances of gemma-4-31B on GPUs 0-3 (:8000 :8010 :8020 :8030)
cd /diskthalys/ssd14ta/yharada/vllm-server
for pair in "0 8000" "1 8010" "2 8020" "3 8030"; do
  set -- $pair
  LOG=logs/ugr_gemma4_31b_$(date +%Y%m%d_%H%M)_gpu$1.log
  VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-31B-it NAME=gemma-4-31b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
done
echo started
