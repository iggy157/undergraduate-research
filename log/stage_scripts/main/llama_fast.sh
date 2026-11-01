#!/usr/bin/env bash
# restart Llama without batch-invariant mode (judge: temperature 0 only) and annotate with 12 workers in rounds
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
A=$S/annot_main; L=$S/main/llama_fast.log
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
$S/stop_vllm_port.sh 8040 >> $L 2>&1
$S/llama/start_vllm_llama.sh >> $L 2>&1
for i in $(seq 1 60); do sleep 10; curl -s localhost:8040/v1/models | grep -q llama && break; done
echo "$(date +%H:%M:%S) llama restarted (non-invariant): $(python3 -c "import json;print(json.load(open('/diskthalys/ssd14ta/yharada/vllm-server/running/8040.json'))['VLLM_BATCH_INVARIANT'])")" >> $L
while true; do
  n0=$(ls $A/out | grep -c '^llama_')
  $S/pilot8/run_annot.sh $A http://localhost:8040/v1 llama-3.3-70b llama 12 12000
  n1=$(ls $A/out | grep -c '^llama_'); ng=$(ls $A/games | wc -l)
  echo "$(date +%H:%M:%S) round: llama $n0 -> $n1 of $ng games" >> $L
  if [ -f log/main_gemma31b/_queue/queue.done ] && [ "$ng" -ge 630 ] && [ "$n1" -ge "$ng" ]; then echo "$(date +%H:%M:%S) LLAMA DONE" >> $L; break; fi
  sleep 300
done
