#!/usr/bin/env bash
# when the hidden-state extraction and the gpt-oss subset are done: 3 Llama judges, the remaining lines split in 3
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/linejudge/judge.log; cd $R; O=log/line_judge
log() { echo "$(date +%H:%M:%S) $*" >> $L; }
until grep -q "HIDDEN DONE" $S/linejudge/hidden.log 2>/dev/null; do sleep 60; done
while ps -eo args | grep -q "[l]ine_judge.py.*--rater gptoss"; do sleep 60; done
log "hidden done and gpt-oss subset done; scaling Llama judges"
$S/stop_vllm_port.sh 8060 >> $L 2>&1; sleep 30
$S/linejudge/start_llama_01.sh >> $L 2>&1; $S/linejudge/start_llama_25.sh >> $L 2>&1
for i in $(seq 1 90); do n=0; for p in 8045 8047; do curl -s localhost:$p/v1/models | grep -q llama && n=$((n+1)); done; [ $n = 2 ] && break; sleep 10; done
log "extra Llama judges up: $n/2"
# stop the single-server Llama judges (they resume from their output files)
for p in $(ps -eo pid=,args= | awk '/[l]ine_judge.py.*--rater llama/ {print $1}'); do [ "$p" = "$$" ] && continue; kill -TERM $p; done
sleep 20
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
