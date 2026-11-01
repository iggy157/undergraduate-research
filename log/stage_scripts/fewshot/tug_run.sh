#!/usr/bin/env bash
# Examples vs history on identical states: multi-online states (long history) re-generated with 3 short examples
# (the model's own single-batch games, other setups), under the batch and under the online goal. Runs after fewshot_run.sh.
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
F=$S/fewshot; L=$F/tug.log; cd $R; O=log/goal_swap_ex; mkdir -p $O
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
GM=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
QM=/home/yharada/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
PORTS=(8000 8010 8020 8030 8040 8050 8070 8075)
up() { local name=$1; for i in $(seq 1 120); do n=0; for p in ${PORTS[@]}; do curl -s localhost:$p/v1/models | grep -q "\"$name\"" && n=$((n+1)); done; [ $n = 8 ] && break; sleep 10; done; log "$name servers up: $n/8"; }
stopall() { $S/main/kill_vllm_all.sh >> $L 2>&1; sleep 30; }
until [ -f $F/done ]; do sleep 60; done
log "fewshot run done; starting the examples-vs-history run"
stopall
for i in 0 1 2 3 4 5 6 7; do $F/gemma_one_32k.sh $i ${PORTS[$i]} >> $L 2>&1; done
up gemma-4-31b
M=default,default_b,default_c,default_d,default_e,default_f,default_g,default_h; EX='{"src": "log/main_gemma31b", "cond": "single-batch", "n": 3}'
for t in batch online; do
  .venv/bin/python scripts/goal_swap.py --log-dir log/main_gemma31b --source multi-private --target $t --examples "$EX" --models $M --threads-per-model 8 --out $O/gemma__${t}_exshort.jsonl > $F/tug_gemma_$t.out 2>&1 &
done; wait
log "gemma: $(wc -l < $O/gemma__batch_exshort.jsonl) + $(wc -l < $O/gemma__online_exshort.jsonl)"
stopall
for i in 0 1 2 3 4 5 6 7; do $F/qwen_32k.sh $i ${PORTS[$i]} >> $L 2>&1; done
up qwen3.8-27b
M=qwen,qwen_b,qwen_c,qwen_d,qwen_e,qwen_f,qwen_g,qwen_h; EX='{"src": "log/main_qwen38", "cond": "single-batch", "n": 3}'
for t in batch online; do
  .venv/bin/python scripts/goal_swap.py --log-dir log/main_qwen38 --source multi-private --target $t --examples "$EX" --models $M --pin-by-setup --threads-per-model 2 --out $O/qwen__${t}_exshort.jsonl > $F/tug_qwen_$t.out 2>&1 &
done; wait
log "qwen: $(wc -l < $O/qwen__batch_exshort.jsonl) + $(wc -l < $O/qwen__online_exshort.jsonl)"
stopall
# judges (Llama on 0,1 / 2,3 / 4,5) + hidden states (6, 7)
$S/linejudge/start_llama_01.sh >> $L 2>&1; $F/start_llama_23.sh >> $L 2>&1; $F/start_llama_45.sh >> $L 2>&1
for i in $(seq 1 90); do n=0; for p in 8045 8040 8047; do curl -s localhost:$p/v1/models | grep -q llama && n=$((n+1)); done; [ $n = 3 ] && break; sleep 10; done
log "llama judges up: $n/3"
JP=(8045 8040 8047)
for m in gemma qwen; do
  ld=main_gemma31b; [ $m = qwen ] && ld=main_qwen38
  for i in 0 1 2; do
    others=""; for j in 0 1 2; do [ $j != $i ] && others="$others log/line_judge/llama__${m}_ex.p$j.jsonl"; done
    .venv/bin/python scripts/line_judge.py --log-dir log/$ld --swap $O/${m}__batch_exshort.jsonl $O/${m}__online_exshort.jsonl --base-url http://localhost:${JP[$i]}/v1 --model llama-3.3-70b --rater llama --out log/line_judge/llama__${m}_ex.p$i.jsonl --done-from $others --part $i/3 --threads 32 > $F/tug_judge_${m}_p$i.out 2>&1 &
  done
done
( for m in gemma qwen; do mp=$GM; ld=main_gemma31b; lay=20,40,48,56; [ $m = qwen ] && { mp=$QM; ld=main_qwen38; lay=20,32,48,52; }
    for t in batch online; do
      for i in 0 1; do CUDA_VISIBLE_DEVICES=$((6+i)) $VPY scripts/swap_hidden.py --log-dir log/$ld --swap $O/${m}__${t}_exshort.jsonl --model-path $mp --layers $lay --out-dir hidden/goal_swap_ex/${m}__${t}_exshort --shard $i/2 > $F/tug_hidden_${m}_${t}_$i.out 2>&1 & done; wait
      log "hidden $m $t: $(ls hidden/goal_swap_ex/${m}__${t}_exshort/*.npz 2>/dev/null | wc -l)/2"
    done
  done ) &
wait
log "TUG DONE: judged $(cat log/line_judge/llama__*_ex.p*.jsonl | wc -l) lines"
stopall
touch $F/tug.done
