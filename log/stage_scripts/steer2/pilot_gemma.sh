#!/usr/bin/env bash
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
M=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
cd $R
for i in 0 1; do
  CUDA_VISIBLE_DEVICES=$i $VPY scripts/steer_goal2.py --log-dir log/main_gemma31b --model-path $M --layer 40 --out $S/steer2/pilot_gemma_s$i.jsonl --vector $S/steer2/gemma.v40.npy --alphas=0,0.5,1,1.5 --shard $i/2 --limit-tests 15 > $S/steer2/pilot_gemma_s$i.out 2>&1 &
done
wait
echo "$(date +%H:%M:%S) pilot gemma done: $(cat $S/steer2/pilot_gemma_s*.jsonl | wc -l) lines" >> $S/steer2/steer.log
