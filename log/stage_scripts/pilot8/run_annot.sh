#!/usr/bin/env bash
# usage: run_annot.sh <annot dir> <base url> <model name> <rater> [workers=6] [max_tokens=12000]
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
D=$1; URL=$2; MODEL=$3; R=$4; NW=${5:-6}; MT=${6:-12000}; P=$D/${R}_progress.txt
games=$(ls $D/games | sort)
for w in $(seq 0 $((NW-1))); do
  list=$(echo "$games" | awk -v w=$w -v n=$NW 'NR % n == w' | tr '\n' ',' | sed 's/,$//')
  ( .venv/bin/python scripts/annotate_llm.py --annot-dir $D --base-url $URL --model $MODEL --rater $R --games "$list" --max-tokens $MT > $D/${R}_w$w.out 2>&1; echo "worker $w done rc=$? $(date +%H:%M:%S)" >> $P ) &
done
wait; touch $D/$R.done
