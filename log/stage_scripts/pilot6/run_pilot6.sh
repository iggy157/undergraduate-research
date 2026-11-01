#!/usr/bin/env bash
# Pilot 6 (after the 2026-10-28 audits): all conditions on 3 domains x 3 setups with two vLLM instances
# (:8000 model=default, :8001 model=default_b; both VLLM_BATCH_INVARIANT=1). single-batch is run twice (replicate:
# the noise floor). Plans regenerated under the strict process rules, then single-batch-process and multi-private-process.
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/pilot6
PY=.venv/bin/python; LOGDIR=log/_pilot6; SETUPS="0001 0002 0003"; DOMAINS="aiwolf candidate_selection shared_living"
for port in 8000 8010; do
  for i in $(seq 1 120); do curl -s http://localhost:$port/v1/models | grep -q gemma-4-31b && break; sleep 10; done
  curl -s http://localhost:$port/v1/models | grep -q gemma-4-31b || { echo "vllm :$port not up" >> $S/progress.txt; exit 1; }
done
echo "vllm up $(date)" >> $S/progress.txt
# chain A (:8000): single-batch x2, plans, single-batch-process
(
  for rep in 1 2; do for d in $DOMAINS; do for n in $SETUPS; do
    $PY scripts/run_single.py --setup ${d}_$n --log-dir $LOGDIR > $S/sb${rep}_${d}_$n.out 2>&1
    echo "single-batch(rep$rep) $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
  done; done; done
  ids=""; for d in $DOMAINS; do for n in $SETUPS; do ids="$ids,${d}_$n"; done; done
  $PY scripts/gen_scenarios.py --setups ${ids#,} --attempts 8 > $S/gen.out 2>&1
  echo "plans rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
  for d in $DOMAINS; do for n in $SETUPS; do
    [ -f scenarios/$d/${d}_$n.json ] || { echo "single-batch-process $d $n no plan" >> $S/progress.txt; continue; }
    $PY scripts/run_single.py --setup ${d}_$n --log-dir $LOGDIR --scenario auto --plan-granularity process > $S/sbp_${d}_$n.out 2>&1
    echo "single-batch-process $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
  done; done
  touch $S/chainA.done
) &
# chain B (:8001): stepped, online
(
  port=10500
  for cond in stepped writer; do for d in $DOMAINS; do for n in $SETUPS; do
    $PY scripts/run_multi.py --setup ${d}_$n --log-dir $LOGDIR --port $port --model default_b --$cond > $S/${cond}_${d}_$n.out 2>&1
    echo "cond=$cond $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
    port=$((port+1))
  done; done; done
  touch $S/chainB.done
) &
# chain C (:8000): multi-public, multi-private
(
  port=10600
  for cond in reveal base; do for d in $DOMAINS; do for n in $SETUPS; do
    flags=""; [ $cond = reveal ] && flags="--reveal"
    $PY scripts/run_multi.py --setup ${d}_$n --log-dir $LOGDIR --port $port $flags > $S/${cond}_${d}_$n.out 2>&1
    echo "cond=$cond $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
    port=$((port+1))
  done; done; done
  touch $S/chainC.done
) &
# chain D (:8001): multi-private-process after the plans
(
  while [ ! -e $S/chainA.done ]; do sleep 20; done
  port=10700
  for d in $DOMAINS; do for n in $SETUPS; do
    [ -f scenarios/$d/${d}_$n.json ] || { echo "multi-private-process $d $n no plan" >> $S/progress.txt; continue; }
    $PY scripts/run_multi.py --setup ${d}_$n --log-dir $LOGDIR --port $port --model default_b --scenario auto --plan-granularity process > $S/mpp_${d}_$n.out 2>&1
    echo "multi-private-process $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
    port=$((port+1))
  done; done
  touch $S/chainD.done
) &
wait
touch $S/all.done
