#!/usr/bin/env bash
# steering, gemma: direction from 60 setups (6 states each) at layer 40; test on the other 30 setups (first turns + 12 random), 2 shards on GPUs 0,1
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
M=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
cd $R
for i in 0 1; do
  CUDA_VISIBLE_DEVICES=$i $VPY scripts/steer_goal.py --log-dir log/main_gemma31b --model-path $M --layer 40 --out $S/steer/gemma_s$i.jsonl --vector $S/steer/gemma.v40.npy --train-setups 60 --states-per-setup 6 --test-states-per-setup 12 --alphas=-1,0,1,2 --shard $i/2 > $S/steer/gemma_s$i.out 2>&1 &
done
wait
echo "$(date +%H:%M:%S) gemma steering done: $(cat $S/steer/gemma_s*.jsonl | wc -l) lines" >> $S/steer/steer.log
