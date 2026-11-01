#!/usr/bin/env bash
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
until grep -q "^DONE" $S/llama/download_gptoss2.log 2>/dev/null; do
  if ! pgrep -f download_gptoss2.py > /dev/null; then echo "download process gone without DONE"; exit 1; fi
  sleep 20
done
echo "download done $(date +%H:%M)"
$S/llama/start_vllm_gptoss.sh
for i in $(seq 1 90); do
  sleep 10
  if curl -s localhost:8060/v1/models | grep -q gpt-oss; then echo "gpt-oss server ready $(date +%H:%M)"; exit 0; fi
done
echo "gpt-oss server not ready after 15 min"; exit 2
