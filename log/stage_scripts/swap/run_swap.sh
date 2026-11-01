#!/usr/bin/env bash
# goal swap: gemma on GPUs 2-5, then Qwen on GPUs 2-5 (pinned by setup)
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
L=$S/swap/swap.log; cd $R
log() { echo "$(date +%H:%M:%S) $*" >> $L; }
up() { local name=$1; for i in $(seq 1 120); do n=0; for p in 8020 8030 8040 8050; do curl -s localhost:$p/v1/models | grep -q "\"$name\"" && n=$((n+1)); done; [ $n = 4 ] && break; sleep 10; done; log "$name servers up: $n/4"; }
stopall() { for p in 8020 8030 8040 8050; do $S/stop_vllm_port.sh $p >> $L 2>&1; done; sleep 20; }
for g in 2 3 4 5; do $S/stage/gemma_one.sh $g 80${g}0 >> $L 2>&1; done
up gemma-4-31b
for src in multi-private multi-private-stepped; do
  .venv/bin/python scripts/goal_swap.py --log-dir log/main_gemma31b --source $src --models default_c,default_d,default_e,default_f --out $S/swap/gemma__$src.jsonl --threads-per-model 12 >> $S/swap/gemma__$src.out 2>&1 &
done; wait
log "gemma done: $(wc -l < $S/swap/gemma__multi-private.jsonl) + $(wc -l < $S/swap/gemma__multi-private-stepped.jsonl)"
stopall
for g in 2 3 4 5; do $S/qwen/start_vllm_qwen.sh $g 80${g}0 >> $L 2>&1; done
up qwen3.8-27b
for src in multi-private multi-private-stepped; do
  .venv/bin/python scripts/goal_swap.py --log-dir log/main_qwen38 --source $src --models qwen_c,qwen_d,qwen_e,qwen_f --out $S/swap/qwen__$src.jsonl --pin-by-setup --threads-per-model 2 >> $S/swap/qwen__$src.out 2>&1 &
done; wait
log "qwen done: $(wc -l < $S/swap/qwen__multi-private.jsonl) + $(wc -l < $S/swap/qwen__multi-private-stepped.jsonl)"
stopall
touch $S/swap/done
