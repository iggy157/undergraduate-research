#!/usr/bin/env bash
# gemma-4-31B cross-instance identity check: two batch-invariant instances (GPU 4 :8040, GPU 5 :8050),
# single-batch + multi-private on 3 setups on each, compared with each other and with the main run.
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/gemma_xinst/log.txt
cd /diskthalys/ssd14ta/yharada/vllm-server
for pair in "4 8040" "5 8050"; do set -- $pair
  VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-31B-it NAME=gemma-4-31b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > logs/ugr_gemma-4-31b_xinst_$(date +%Y%m%d_%H%M)_gpu$1.log 2>&1 < /dev/null &
done
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
for i in $(seq 1 120); do curl -s localhost:8040/v1/models | grep -q gemma && curl -s localhost:8050/v1/models | grep -q gemma && break; sleep 10; done
echo "$(date +%H:%M:%S) up" >> $L
rm -rf log/_gx_A log/_gx_B
SET=aiwolf_0004,candidate_selection_0004,shared_living_0004
.venv/bin/python scripts/run_queue.py --log-dir log/_gx_A --models default_e --per-model 3 --port-base 33000 --setups $SET --conditions single-batch,multi-private >> $L 2>&1 &
.venv/bin/python scripts/run_queue.py --log-dir log/_gx_B --models default_f --per-model 3 --port-base 33100 --setups $SET --conditions single-batch,multi-private >> $L 2>&1 &
wait
for d in log/_gx_A/*/*/*/ log/_gx_B/*/*/*/ log/main_gemma31b/*/single-batch/ log/main_gemma31b/*/multi-private/; do touch $d/.r 2>/dev/null; rm -f $d/.r; done
.venv/bin/python - >> $L 2>&1 <<'PY'
import glob, csv
def talks(d):
    fs=glob.glob(d+"/*.log"); return [(r[1],r[2],r[4],r[6]) for r in csv.reader(open(fs[0])) if r[3] in ("talk","pass")] if fs else None
for c in ["single-batch","multi-private"]:
    for sid in ["aiwolf_0004","candidate_selection_0004","shared_living_0004"]:
        a=glob.glob(f"log/_gx_A/*/*/{sid}__{c}__*"); b=glob.glob(f"log/_gx_B/*/*/{sid}__{c}__*"); m=glob.glob(f"log/main_gemma31b/*/{c}/{sid}__{c}__*")
        ta=talks(a[0]) if a else None; tb=talks(b[0]) if b else None; tm=talks(m[0]) if m else None
        print(f"{c} {sid}: A==B {ta==tb}  A==main {ta==tm}  B==main {tb==tm}")
PY
echo "XINST DONE" >> $L
for port in 8040 8050; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
