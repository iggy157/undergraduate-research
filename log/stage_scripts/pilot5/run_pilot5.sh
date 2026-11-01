#!/usr/bin/env bash
# Pilot 5 (greedy, models.yml default): the five core conditions on 3 domains x 3 setups (0001..0003), then the plans
# (turn granularity, same model) for those setups, then the process-plan conditions (single-batch-process,
# multi-private-process). vLLM must be up on :8000. Logs -> log/_pilot5.
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/pilot5
PY=.venv/bin/python
LOGDIR=log/_pilot5
SETUPS="0001 0002 0003"
DOMAINS="aiwolf candidate_selection shared_living"
for i in $(seq 1 120); do curl -s http://localhost:8000/v1/models | grep -q gemma-4-31b && break; sleep 10; done
curl -s http://localhost:8000/v1/models | grep -q gemma-4-31b || { echo "vllm not up" >> $S/progress.txt; exit 1; }
echo "vllm up $(date)" >> $S/progress.txt
# chain A: single-batch, plans, single-batch-process
(
  for d in $DOMAINS; do for n in $SETUPS; do
    $PY scripts/run_single.py --setup ${d}_$n --log-dir $LOGDIR > $S/single-batch_${d}_$n.out 2>&1
    echo "single-batch $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
  done; done
  ids=""; for d in $DOMAINS; do for n in $SETUPS; do ids="$ids,${d}_$n"; done; done
  $PY scripts/gen_scenarios.py --setups ${ids#,} > $S/gen.out 2>&1
  echo "plans rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
  for d in $DOMAINS; do for n in $SETUPS; do
    [ -f scenarios/$d/${d}_$n.json ] || { echo "single-batch-process $d $n no plan" >> $S/progress.txt; continue; }
    $PY scripts/run_single.py --setup ${d}_$n --log-dir $LOGDIR --scenario auto --plan-granularity process > $S/single-batch-process_${d}_$n.out 2>&1
    echo "single-batch-process $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
  done; done
  touch $S/chainA.done
) &
# chain B: the server-pipeline conditions, one game at a time
(
  port=10200
  for cond in stepped writer reveal base; do
    for d in $DOMAINS; do for n in $SETUPS; do
      flags=""; [ $cond = stepped ] && flags="--stepped"; [ $cond = writer ] && flags="--writer"; [ $cond = reveal ] && flags="--reveal"
      $PY scripts/run_multi.py --setup ${d}_$n --log-dir $LOGDIR --port $port $flags > $S/multi_${cond}_${d}_$n.out 2>&1
      echo "cond=$cond $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
      port=$((port+1))
    done; done
  done
  while [ ! -e $S/chainA.done ]; do sleep 20; done
  for d in $DOMAINS; do for n in $SETUPS; do
    [ -f scenarios/$d/${d}_$n.json ] || { echo "multi-private-process $d $n no plan" >> $S/progress.txt; continue; }
    $PY scripts/run_multi.py --setup ${d}_$n --log-dir $LOGDIR --port $port --scenario auto --plan-granularity process > $S/multi-private-process_${d}_$n.out 2>&1
    echo "multi-private-process $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
    port=$((port+1))
  done; done
  touch $S/chainB.done
) &
wait
touch $S/all.done
