#!/usr/bin/env bash
# re-run the process-plan games that failed on the old scenarios (regenerated now)
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/pilot8
PY=.venv/bin/python; LOGDIR=log/_pilot8; P=$S/progress_fix.txt
(
  for sid in aiwolf_0001 aiwolf_0002 aiwolf_0003 shared_living_0003; do
    $PY scripts/run_single.py --setup $sid --log-dir $LOGDIR --scenario auto --plan-granularity process > $S/sbp_fix_$sid.out 2>&1
    echo "single-batch-process $sid rc=$? $(date +%H:%M:%S)" >> $P
  done
) &
(
  port=13300
  for sid in aiwolf_0001 aiwolf_0002 aiwolf_0003; do
    $PY scripts/run_multi.py --setup $sid --log-dir $LOGDIR --port $port --model default_d --scenario auto --plan-granularity process > $S/mpp_fix_$sid.out 2>&1
    echo "multi-private-process $sid rc=$? $(date +%H:%M:%S)" >> $P; port=$((port+1))
  done
) &
wait; touch $S/fix.done
