#!/usr/bin/env bash
# Qwen smoke test: 1 setup per domain x 5 core conditions on :8070, then checks
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/qwen/smoke.log
for i in $(seq 1 90); do curl -s localhost:8070/v1/models | grep -q qwen && break; sleep 10; done
echo "$(date +%H:%M:%S) qwen up: $(curl -s localhost:8070/v1/models | grep -o '"id":"qwen[^"]*"')" >> $L
rm -rf log/_smoke_qwen
.venv/bin/python scripts/run_queue.py --log-dir log/_smoke_qwen --models qwen_smoke --per-model 5 --port-base 24000 --setups aiwolf_0001,candidate_selection_0001,shared_living_0001 --conditions single-batch,single-batch-stepped,single-online,multi-public,multi-private >> $L 2>&1
echo "$(date +%H:%M:%S) smoke games done: $(ls -d log/_smoke_qwen/*/*/*/ | wc -l)" >> $L
cat log/_smoke_qwen/_queue/progress.txt >> $L
echo "SMOKE DONE" >> $L
