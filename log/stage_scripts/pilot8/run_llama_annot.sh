#!/usr/bin/env bash
# Llama 3.3 70B annotation (v2) of all games in $1 (annot dir), 3 processes over disjoint game lists
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
D=$1; P=$D/llama_progress.txt
games=$(ls $D/games | sort)
for w in 0 1 2 3 4 5; do
  list=$(echo "$games" | awk -v w=$w 'NR % 6 == w' | tr '\n' ',' | sed 's/,$//')
  ( .venv/bin/python scripts/annotate_llm.py --annot-dir $D --base-url http://localhost:8040/v1 --model llama-3.3-70b --rater llama --games "$list" --max-tokens 12000 > $D/llama_w$w.out 2>&1; echo "worker $w done rc=$? $(date +%H:%M:%S)" >> $P ) &
done
wait; touch $D/llama.done
