#!/usr/bin/env bash
# Mistral smoke + determinism: 3 setups x {single-batch, single-batch-stepped, multi-private, multi-private-stepped} on A (:8000),
# the same single-batch + multi-private on B (:8010) (cross-instance), and single-batch again on A (same instance).
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/mistral/smoke.log
for i in $(seq 1 120); do curl -s localhost:8000/v1/models | grep -q mistral && curl -s localhost:8010/v1/models | grep -q mistral && break; sleep 10; done
echo "$(date +%H:%M:%S) servers: A $(curl -s localhost:8000/v1/models | grep -c mistral) B $(curl -s localhost:8010/v1/models | grep -c mistral)" >> $L
rm -rf log/_mis_A log/_mis_A2 log/_mis_B
SET=aiwolf_0001,candidate_selection_0001,shared_living_0001
.venv/bin/python scripts/run_queue.py --log-dir log/_mis_A --models mis --per-model 2 --port-base 32000 --setups $SET --conditions single-batch,single-batch-stepped,multi-private,multi-private-stepped >> $L 2>&1 &
.venv/bin/python scripts/run_queue.py --log-dir log/_mis_B --models mis_b --per-model 2 --port-base 32100 --setups $SET --conditions single-batch,multi-private >> $L 2>&1 &
wait
.venv/bin/python scripts/run_queue.py --log-dir log/_mis_A2 --models mis --per-model 2 --port-base 32200 --setups $SET --conditions single-batch,multi-private >> $L 2>&1
for d in log/_mis_A/*/*/*/ log/_mis_A2/*/*/*/ log/_mis_B/*/*/*/; do touch $d/.r 2>/dev/null; rm -f $d/.r; done
.venv/bin/python - >> $L 2>&1 <<'PY'
import glob, csv, json, statistics as st
def rows(d):
    fs=glob.glob(d+"/*.log"); return list(csv.reader(open(fs[0]))) if fs else None
def talks(d):
    r=rows(d); return [(x[1],x[2],x[4],x[6]) for x in r if x[3] in ("talk","pass")] if r else None
for c in ["single-batch","single-batch-stepped","multi-private","multi-private-stepped"]:
    for sid in ["aiwolf_0001","candidate_selection_0001","shared_living_0001"]:
        a=glob.glob(f"log/_mis_A/*/*/{sid}__{c}__*")
        if not a: print(c, sid, "missing"); continue
        r=rows(a[0]); t=[x for x in r if x[3]=="talk"]; p=[x for x in r if x[3]=="pass"]
        w=[json.loads(x[7]).get("words",0) for x in t if x[7]]
        res="result" if any(x[3]=="result" for x in r) else "NO RESULT"
        line=f"{c} {sid}: talk {len(t)}, pass {len(p)}, words/utt {st.mean(w) if w else 0:.1f}, {res}"
        if c in ("single-batch","multi-private"):
            a2=glob.glob(f"log/_mis_A2/*/*/{sid}__{c}__*"); b=glob.glob(f"log/_mis_B/*/*/{sid}__{c}__*")
            ta=talks(a[0]); line+=f" | same-instance identical {bool(a2) and talks(a2[0])==ta} | cross-instance identical {bool(b) and talks(b[0])==ta}"
        print(line)
PY
echo "SMOKE DONE" >> $L
