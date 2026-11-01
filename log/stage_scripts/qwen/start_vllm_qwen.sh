#!/usr/bin/env bash
# Qwen3.8-27B (bf16) on GPU $1, port $2. No batch-invariant mode (unsupported for its linear attention); instead the
# batch is fixed at one sequence (--max-num-seqs 1) and prefix caching is off, so every request takes the same path.
# Thinking disabled by the server's default chat-template kwargs.
cd /diskthalys/ssd14ta/yharada/vllm-server
LOG=logs/ugr_qwen38_27b_$(date +%Y%m%d_%H%M)_gpu$1.log
TRITON_CACHE_AUTOTUNING=1 MODEL=Qwen/Qwen3.8-27B NAME=qwen3.8-27b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--max-num-seqs 1 --no-enable-prefix-caching --default-chat-template-kwargs {"enable_thinking":false}' setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
echo started "$LOG"
