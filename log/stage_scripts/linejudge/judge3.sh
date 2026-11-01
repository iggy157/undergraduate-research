#!/usr/bin/env bash
# the 3-way Llama judging (servers already up on 8040, 8045, 8047), with the seat in the done key
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/linejudge/judge.log; cd $R; O=log/line_judge
log() { echo "$(date +%H:%M:%S) $*" >> $L; }
PORTS=(8040 8045 8047)
ST="log/steering_2026-10-30/pilot_gemma_s0.jsonl log/steering_2026-10-30/pilot_gemma_s1.jsonl log/steering_2026-10-30/pilot_gemma_L20.jsonl log/steering_2026-10-30/pilot_gemma_L52.jsonl"
for m in gemma qwen; do
  ld=main_gemma31b; [ $m = qwen ] && ld=main_qwen38
  extra=""; [ $m = gemma ] && extra="--steer $ST"
  for i in 0 1 2; do
    others="$O/llama__$m.jsonl"; for j in 0 1 2; do [ $j != $i ] && others="$others $O/llama__$m.p$j.jsonl"; done
    .venv/bin/python scripts/line_judge.py --log-dir log/$ld --swap log/goal_swap/${m}__multi-private.jsonl log/goal_swap/${m}__multi-private-stepped.jsonl $extra --base-url http://localhost:${PORTS[$i]}/v1 --model llama-3.3-70b --rater llama --out $O/llama__$m.p$i.jsonl --done-from $others --part $i/3 --threads 32 > $S/linejudge/judge_llama_${m}_p$i.out 2>&1 &
  done
done
wait
log "JUDGE LLAMA ALL DONE: $(cat $O/llama__*.jsonl | wc -l) lines"
