#!/usr/bin/env bash
# gemma-4-12B-it on GPUs 0-5 (ports 8000..8050), batch-invariant, LEN 20480
cd /diskthalys/ssd14ta/yharada/vllm-server
for pair in "0 8000" "1 8010" "2 8020" "3 8030" "4 8040" "5 8050"; do
  set -- $pair
  LOG=logs/ugr_gemma4_12b_$(date +%Y%m%d_%H%M)_gpu$1.log
  VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-12B-it NAME=gemma-4-12b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
done
echo started
