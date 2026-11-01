#!/usr/bin/env bash
# usage: run_annot2.sh <annot dir> <url1,url2,...> <model name> <rater> [workers=12] [max_tokens=12000]
# like run_annot.sh, but the workers alternate over several servers of the same judge
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
D=$1; IFS=, read -ra URLS <<< "$2"; MODEL=$3; R=$4; NW=${5:-12}; MT=${6:-12000}; P=$D/${R}_progress.txt
games=$(ls $D/games | sort)
for w in $(seq 0 $((NW-1))); do
  url=${URLS[$((w % ${#URLS[@]}))]}
  list=$(echo "$games" | awk -v w=$w -v n=$NW 'NR % n == w' | tr '\n' ',' | sed 's/,$//')
  ( .venv/bin/python scripts/annotate_llm.py --annot-dir $D --base-url $url --model $MODEL --rater $R --games "$list" --max-tokens $MT > $D/${R}_w$w.out 2>&1; echo "worker $w done rc=$? $(date +%H:%M:%S)" >> $P ) &
done
wait; touch $D/$R.done
