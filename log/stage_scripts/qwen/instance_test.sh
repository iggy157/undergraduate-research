#!/usr/bin/env bash
# cross-instance identity test with TRITON_CACHE_AUTOTUNING=1: instance A (GPU 0 :8000) warms the autotune cache with
# one game, then instance B (GPU 1 :8010) starts; the same 3 setups x single-batch run on both; compare.
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/qwen/instance_test.log
$S/qwen/start_vllm_qwen.sh 0 8000 >> $L 2>&1
for i in $(seq 1 90); do curl -s localhost:8000/v1/models | grep -q qwen && break; sleep 10; done
echo "$(date +%H:%M:%S) A up" >> $L
rm -rf log/_inst_A log/_inst_B log/_inst_warm
.venv/bin/python scripts/run_queue.py --log-dir log/_inst_warm --models qwen --per-model 1 --port-base 29000 --setups shared_living_0002 --conditions single-batch,multi-private >> $L 2>&1
echo "$(date +%H:%M:%S) warm-up done; autotune cache entries: $(ls ~/.triton/cache 2>/dev/null | wc -l)" >> $L
$S/qwen/start_vllm_qwen.sh 1 8010 >> $L 2>&1
for i in $(seq 1 90); do curl -s localhost:8010/v1/models | grep -q qwen && break; sleep 10; done
echo "$(date +%H:%M:%S) B up" >> $L
.venv/bin/python scripts/run_queue.py --log-dir log/_inst_A --models qwen --per-model 1 --port-base 29100 --setups aiwolf_0001,candidate_selection_0001,shared_living_0001 --conditions single-batch,multi-private >> $L 2>&1 &
.venv/bin/python scripts/run_queue.py --log-dir log/_inst_B --models qwen_b --per-model 1 --port-base 29200 --setups aiwolf_0001,candidate_selection_0001,shared_living_0001 --conditions single-batch,multi-private >> $L 2>&1 &
wait
for d in log/_inst_A/*/*/*/ log/_inst_B/*/*/*/; do touch $d/.r 2>/dev/null; rm -f $d/.r; done
.venv/bin/python - >> $L 2>&1 <<'PY'
import glob, csv
def talks(d):
    fs=glob.glob(d+"/*.log"); return [(r[1],r[2],r[4],r[6]) for r in csv.reader(open(fs[0])) if r[3] in ("talk","pass")] if fs else None
for c in ["single-batch","multi-private"]:
    for sid in ["aiwolf_0001","candidate_selection_0001","shared_living_0001"]:
        a=glob.glob(f"log/_inst_A/*/*/{sid}__{c}__*"); b=glob.glob(f"log/_inst_B/*/*/{sid}__{c}__*")
        ta,tb=(talks(a[0]) if a else None),(talks(b[0]) if b else None)
        if ta is None or tb is None: print(c, sid, "missing"); continue
        k=next((i for i,(x,y) in enumerate(zip(ta,tb)) if x!=y), None)
        print(f"{c} {sid}: identical {ta==tb} (lines {len(ta)}/{len(tb)}, first divergence {k})")
PY
echo "INST DONE" >> $L
