#!/usr/bin/env bash
# Pilot 8, multi-private on 3 vLLM instances (:8010 default_b, :8020 default_c, :8030 default_d). log/_pilot8
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/pilot8
for port in 8010 8020 8030; do
  for i in $(seq 1 150); do curl -s http://localhost:$port/v1/models | grep -q gemma-4-31b && break; sleep 10; done
  curl -s http://localhost:$port/v1/models | grep -q gemma-4-31b || { echo "vllm :$port not up" >> $S/progress_multi.txt; exit 1; }
done
echo "vllm up $(date)" >> $S/progress_multi.txt
JOBS=(); for d in candidate_selection shared_living aiwolf; do for n in 0001 0002 0003; do JOBS+=("${d}_$n"); done; done
worker() {
  local w=$1 model=$2; shift 2
  local port=$((12000 + w*100))
  for sid in "$@"; do
    .venv/bin/python scripts/run_multi.py --setup $sid --log-dir log/_pilot8 --port $port --model $model > $S/mp_${sid}.out 2>&1
    echo "multi-private $sid rc=$? $(date +%H:%M:%S)" >> $S/progress_multi.txt
    port=$((port+1))
  done
}
W1=(); W2=(); W3=()
for i in "${!JOBS[@]}"; do case $((i % 3)) in 0) W1+=("${JOBS[$i]}");; 1) W2+=("${JOBS[$i]}");; 2) W3+=("${JOBS[$i]}");; esac; done
worker 1 default_b "${W1[@]}" & worker 2 default_c "${W2[@]}" & worker 3 default_d "${W3[@]}" &
wait; touch $S/multi.done
