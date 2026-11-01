#!/usr/bin/env bash
# multi-private-stepped smoke test on gemma :8000 (GPU 0): one setup per domain
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/main/smoke_mps.log
for i in $(seq 1 90); do curl -s localhost:8000/v1/models | grep -q gemma-4-31b && break; sleep 10; done
echo "$(date +%H:%M:%S) gemma up" >> $L
rm -rf log/_smoke_mps
.venv/bin/python scripts/run_queue.py --log-dir log/_smoke_mps --models default --per-model 3 --port-base 25000 --setups aiwolf_0001,candidate_selection_0001,shared_living_0001 --conditions multi-private-stepped >> $L 2>&1
cat log/_smoke_mps/_queue/progress.txt >> $L
echo "SMOKE DONE" >> $L
