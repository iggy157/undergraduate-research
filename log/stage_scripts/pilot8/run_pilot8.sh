#!/usr/bin/env bash
# Pilot 8: shared rules + "@Name" sentence; single-batch only, 9 setups, one vLLM (:8000). log/_pilot8
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/pilot8
for i in $(seq 1 150); do curl -s http://localhost:8000/v1/models | grep -q gemma-4-31b && break; sleep 10; done
curl -s http://localhost:8000/v1/models | grep -q gemma-4-31b || { echo "vllm not up" >> $S/progress.txt; exit 1; }
echo "vllm up $(date)" >> $S/progress.txt
for d in aiwolf candidate_selection shared_living; do for n in 0001 0002 0003; do
  .venv/bin/python scripts/run_single.py --setup ${d}_$n --log-dir log/_pilot8 > $S/sb_${d}_$n.out 2>&1
  echo "single-batch $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
done; done
touch $S/all.done
