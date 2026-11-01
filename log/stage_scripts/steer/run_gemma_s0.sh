#!/usr/bin/env bash
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
M=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
cd $R
CUDA_VISIBLE_DEVICES=0 $VPY scripts/steer_goal.py --log-dir log/main_gemma31b --model-path $M --layer 40 --out $S/steer/gemma_s0.jsonl --vector $S/steer/gemma.v40.npy --train-setups 60 --states-per-setup 6 --test-states-per-setup 12 --alphas=-1,0,1,2 --shard 0/2 > $S/steer/gemma_s0.out 2>&1
echo "$(date +%H:%M:%S) gemma shard 0 done: $(wc -l < $S/steer/gemma_s0.jsonl) lines" >> $S/steer/steer.log
