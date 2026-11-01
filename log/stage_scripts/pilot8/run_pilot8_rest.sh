#!/usr/bin/env bash
# Pilot 8, remaining conditions with the current shared rules: stepped, online (writer), public (reveal),
# single-batch-process, multi-private-process. gemma on :8000 (default) and :8030 (default_d). log/_pilot8
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/pilot8
PY=.venv/bin/python; LOGDIR=log/_pilot8; P=$S/progress_rest.txt
for port in 8000 8030; do curl -s http://localhost:$port/v1/models | grep -q gemma-4-31b || { echo "vllm :$port not up" >> $P; exit 1; }; done
echo "start $(date)" >> $P
SETS="aiwolf_0001 aiwolf_0002 aiwolf_0003 candidate_selection_0001 candidate_selection_0002 candidate_selection_0003 shared_living_0001 shared_living_0002 shared_living_0003"
# chain A (:8000): single-batch-process, stepped, multi-private-process
(
  for sid in $SETS; do
    $PY scripts/run_single.py --setup $sid --log-dir $LOGDIR --scenario auto --plan-granularity process > $S/sbp_$sid.out 2>&1
    echo "single-batch-process $sid rc=$? $(date +%H:%M:%S)" >> $P
  done
  port=13000
  for sid in $SETS; do
    $PY scripts/run_multi.py --setup $sid --log-dir $LOGDIR --port $port --model default --stepped > $S/stepped_$sid.out 2>&1
    echo "stepped $sid rc=$? $(date +%H:%M:%S)" >> $P; port=$((port+1))
  done
  for sid in $SETS; do
    $PY scripts/run_multi.py --setup $sid --log-dir $LOGDIR --port $port --model default --scenario auto --plan-granularity process > $S/mpp_$sid.out 2>&1
    echo "multi-private-process $sid rc=$? $(date +%H:%M:%S)" >> $P; port=$((port+1))
  done
  touch $S/restA.done
) &
# chain B (:8030): online, public
(
  port=13100
  for cond in writer reveal; do for sid in $SETS; do
    $PY scripts/run_multi.py --setup $sid --log-dir $LOGDIR --port $port --model default_d --$cond > $S/${cond}_$sid.out 2>&1
    echo "$cond $sid rc=$? $(date +%H:%M:%S)" >> $P; port=$((port+1))
  done; done
  touch $S/restB.done
) &
wait; touch $S/rest.done
