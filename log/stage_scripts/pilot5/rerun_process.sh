#!/usr/bin/env bash
# Regenerate the 9 plans under the strict process-prose rules (--force) and rerun the 18 process-plan games.
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/pilot5
PY=.venv/bin/python; LOGDIR=log/_pilot5; SETUPS="0001 0002 0003"; DOMAINS="aiwolf candidate_selection shared_living"
for i in $(seq 1 120); do curl -s http://localhost:8000/v1/models | grep -q gemma-4-31b && break; sleep 10; done
curl -s http://localhost:8000/v1/models | grep -q gemma-4-31b || { echo "vllm not up" >> $S/progress2.txt; exit 1; }
ids=""; for d in $DOMAINS; do for n in $SETUPS; do ids="$ids,${d}_$n"; done; done
$PY scripts/gen_scenarios.py --setups ${ids#,} --force --attempts 8 > $S/gen2.out 2>&1
echo "plans rc=$? $(date +%H:%M:%S)" >> $S/progress2.txt
port=10400
for d in $DOMAINS; do for n in $SETUPS; do
  [ -f scenarios/$d/${d}_$n.json ] || { echo "no plan $d $n" >> $S/progress2.txt; continue; }
  $PY scripts/run_single.py --setup ${d}_$n --log-dir $LOGDIR --scenario auto --plan-granularity process > $S/sbp2_${d}_$n.out 2>&1
  echo "single-batch-process $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress2.txt
  $PY scripts/run_multi.py --setup ${d}_$n --log-dir $LOGDIR --port $port --scenario auto --plan-granularity process > $S/mpp2_${d}_$n.out 2>&1
  echo "multi-private-process $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress2.txt
  port=$((port+1))
done; done
touch $S/rerun.done
