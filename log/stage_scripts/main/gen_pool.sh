#!/usr/bin/env bash
# generate the missing process scenarios, 8 setups at a time, alternating the two gemma servers that stay up
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
i=0
for d in aiwolf candidate_selection shared_living; do
  for f in setups/$d/*.json; do
    sid=$(basename $f .json)
    [ -f scenarios/$d/$sid.json ] && continue
    m=default; [ $((i % 2)) = 1 ] && m=default_d; i=$((i+1))
    echo "$sid $m"
  done
done | xargs -P 8 -L 1 bash -c '.venv/bin/python scripts/gen_scenarios.py --setups $0 --model $1 > '"$S"'/main/gen/$0.out 2>&1; echo "$0 rc=$? $(date +%H:%M:%S)" >> '"$S"'/main/gen_pool_progress.txt'
touch $S/main/gen_pool.done
