#!/usr/bin/env bash
# gemma-4-31B on GPUs 0,1,2,4,5 (ports 8000,8010,8020,8040,8050); GPU 3 (:8030) is already up
cd /diskthalys/ssd14ta/yharada/vllm-server
for pair in "0 8000" "1 8010" "2 8020" "4 8040" "5 8050"; do
  set -- $pair
  LOG=logs/ugr_gemma4_31b_$(date +%Y%m%d_%H%M)_gpu$1.log
  VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-31B-it NAME=gemma-4-31b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
done
echo started
