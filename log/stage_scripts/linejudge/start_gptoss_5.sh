#!/usr/bin/env bash
# gpt-oss-120b (mxfp4) on GPU 5, port 8060, served-model-name gpt-oss-120b
cd /diskthalys/ssd14ta/yharada/vllm-server
LOG=logs/ugr_gptoss120b_$(date +%Y%m%d_%H%M).log
MODEL=openai/gpt-oss-120b NAME=gpt-oss-120b GPUS=5 PORT=8060 LEN=32768 BATCH=8192 UTIL=0.90 setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
echo started "$LOG"
