#!/usr/bin/env bash
# parallel retry (8 attempts, forbidden-word feedback) of the Qwen plans that failed after 4 attempts; 6 at a time
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
P=scenarios_qwen38
i=0
for f in $P/*/*.failed.json; do sid=$(basename $f .failed.json); d=$(basename $(dirname $f))
  [ -f $P/$d/$sid.json ] && continue
  m=$(echo qwen,qwen_b,qwen_c,qwen_d,qwen_e,qwen_f | cut -d, -f$(( i % 6 + 1 ))); i=$((i+1)); echo "$sid $m"
done | xargs -P 6 -L 1 bash -c '.venv/bin/python scripts/gen_scenarios.py --setups $0 --model $1 --out-dir scenarios_qwen38 --attempts 8 --force > '"$S"'/stage/gen_qwenplan_retry/$0.out 2>&1; echo "$0 rc=$? $(date +%H:%M:%S)" >> '"$S"'/stage/gen_qwenplan_retry/progress.txt'
echo "RETRY DONE $(date +%H:%M:%S)" >> $S/stage/gen_qwenplan_retry/progress.txt
