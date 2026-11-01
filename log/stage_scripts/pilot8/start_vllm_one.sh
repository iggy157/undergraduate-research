#!/usr/bin/env bash
cd /diskthalys/ssd14ta/yharada/vllm-server
LOG=logs/ugr_gemma4_31b_$(date +%Y%m%d_%H%M)_gpu0.log
VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-31B-it NAME=gemma-4-31b GPUS=0 PORT=8000 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
echo started
