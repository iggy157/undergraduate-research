#!/usr/bin/env bash
# $1 = HF model id, $2 = served name: 6 batch-invariant instances on GPUs 0-5 (ports 8000..8050)
cd /diskthalys/ssd14ta/yharada/vllm-server
HF=$1; NAME=$2
for pair in "0 8000" "1 8010" "2 8020" "3 8030" "4 8040" "5 8050"; do
  set -- $pair
  VLLM_BATCH_INVARIANT=1 MODEL=$HF NAME=$NAME GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > logs/ugr_${NAME}_$(date +%Y%m%d_%H%M)_gpu$1.log 2>&1 < /dev/null &
done
echo started
