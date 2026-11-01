#!/usr/bin/env bash
# hidden states of every goal-swap state under both framings: gemma then Qwen, 3 shards on GPUs 0-2
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
GM=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
QM=/home/yharada/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/
cd $R
L=$S/linejudge/hidden.log
for spec in "gemma main_gemma31b $GM 20,40,48,56" "qwen main_qwen38 $QM 20,32,48,52"; do
  set -- $spec; m=$1; ld=$2; mp=$3; lay=$4
  for src in multi-private multi-private-stepped; do
    for i in 0 1 2; do
      CUDA_VISIBLE_DEVICES=$i $VPY scripts/swap_hidden.py --log-dir log/$ld --swap log/goal_swap/${m}__$src.jsonl --model-path $mp --layers $lay --out-dir hidden/goal_swap/${m}__$src --shard $i/3 > $S/linejudge/hidden_${m}_${src}_$i.out 2>&1 &
    done
    wait
    echo "$(date +%H:%M:%S) $m $src: $(ls hidden/goal_swap/${m}__$src/*.npz 2>/dev/null | wc -l)/3 shards" >> $L
  done
done
echo "$(date +%H:%M:%S) HIDDEN DONE" >> $L
