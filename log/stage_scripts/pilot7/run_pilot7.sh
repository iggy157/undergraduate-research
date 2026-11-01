#!/usr/bin/env bash
# Pilot 7 (2026-10-28): the shared Discussion-format block gained one sentence describing the talk as a conversation.
# 3 domains x 3 setups: single-batch (9, fast), single-online (9), multi-private (9) on four vLLM instances
# (:8000 default, :8010 default_b, :8020 default_c, :8030 default_d; all VLLM_BATCH_INVARIANT=1). log/_pilot7.
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/pilot7
PY=.venv/bin/python; LOGDIR=log/_pilot7
for port in 8000 8010 8020 8030; do
  for i in $(seq 1 150); do curl -s http://localhost:$port/v1/models | grep -q gemma-4-31b && break; sleep 10; done
  curl -s http://localhost:$port/v1/models | grep -q gemma-4-31b || { echo "vllm :$port not up" >> $S/progress.txt; exit 1; }
done
echo "vllm up $(date)" >> $S/progress.txt
# 18 long jobs (cond setup), distributed round-robin over 4 workers; worker 0 first runs the 9 single-batch games
JOBS=()
for cond in writer base; do for d in candidate_selection shared_living aiwolf; do for n in 0001 0002 0003; do JOBS+=("$cond ${d}_$n"); done; done; done
worker() {
  local w=$1 model=$2 port=$((11000 + w*100)); shift 2
  if [ $w = 0 ]; then
    for d in aiwolf candidate_selection shared_living; do for n in 0001 0002 0003; do
      $PY scripts/run_single.py --setup ${d}_$n --log-dir $LOGDIR > $S/sb_${d}_$n.out 2>&1
      echo "single-batch $d $n rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
    done; done
  fi
  for job in "$@"; do
    set -- $job; cond=$1; sid=$2
    flags=""; [ $cond = writer ] && flags="--writer"
    $PY scripts/run_multi.py --setup $sid --log-dir $LOGDIR --port $port --model $model $flags > $S/${cond}_${sid}.out 2>&1
    echo "cond=$cond $sid rc=$? $(date +%H:%M:%S)" >> $S/progress.txt
    port=$((port+1))
  done
  touch $S/worker$w.done
}
W0=(); W1=(); W2=(); W3=()
for i in "${!JOBS[@]}"; do case $((i % 4)) in 0) W0+=("${JOBS[$i]}");; 1) W1+=("${JOBS[$i]}");; 2) W2+=("${JOBS[$i]}");; 3) W3+=("${JOBS[$i]}");; esac; done
worker 0 default "${W0[@]}" &
worker 1 default_b "${W1[@]}" &
worker 2 default_c "${W2[@]}" &
worker 3 default_d "${W3[@]}" &
wait
touch $S/all.done
