#!/usr/bin/env bash
# Qwen determinism check on :8070 (qwen_smoke): 3 setups x {single-batch, multi-private} twice each, then compare
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/qwen/determinism.log
for i in $(seq 1 120); do curl -s localhost:8070/v1/models | grep -q qwen && break; sleep 10; done
curl -s localhost:8070/v1/models | grep -q qwen || { echo "server not up" >> $L; echo "DET DONE" >> $L; exit 1; }
echo "$(date +%H:%M:%S) qwen up" >> $L
for rep in 1 2; do
  rm -rf log/_det_qwen_$rep
  .venv/bin/python scripts/run_queue.py --log-dir log/_det_qwen_$rep --models qwen_smoke --per-model 1 --port-base $((26000 + rep*10)) --setups aiwolf_0001,candidate_selection_0001,shared_living_0001 --conditions single-batch,multi-private >> $L 2>&1
  echo "$(date +%H:%M:%S) replicate $rep done" >> $L
done
.venv/bin/python - >> $L 2>&1 <<'PY'
import glob, csv
def talks(d):
    f=glob.glob(d+"/*.log")[0]
    return [(r[1],r[2],r[4],r[6]) for r in csv.reader(open(f)) if r[3] in ("talk","pass")]
for c in ["single-batch","multi-private"]:
    for sid in ["aiwolf_0001","candidate_selection_0001","shared_living_0001"]:
        a=glob.glob(f"log/_det_qwen_1/*/*/{sid}__{c}__*")[0]; b=glob.glob(f"log/_det_qwen_2/*/*/{sid}__{c}__*")[0]
        ta,tb=talks(a),talks(b); same=sum(1 for x,y in zip(ta,tb) if x==y)
        print(f"{c} {sid}: lines {len(ta)} vs {len(tb)}, identical {same}, first divergence at line {next((i for i,(x,y) in enumerate(zip(ta,tb)) if x!=y), None)}")
PY
echo "DET DONE" >> $L
