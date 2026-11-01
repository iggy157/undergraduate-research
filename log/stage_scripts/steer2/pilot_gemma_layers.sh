#!/usr/bin/env bash
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
M=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
cd $R
CUDA_VISIBLE_DEVICES=0 $VPY scripts/steer_goal2.py --log-dir log/main_gemma31b --model-path $M --layer 20 --out $S/steer2/pilot_gemma_L20.jsonl --alphas=0,1,2,4 --limit-tests 15 > $S/steer2/pilot_gemma_L20.out 2>&1 &
CUDA_VISIBLE_DEVICES=1 $VPY scripts/steer_goal2.py --log-dir log/main_gemma31b --model-path $M --layer 52 --out $S/steer2/pilot_gemma_L52.jsonl --alphas=0,1,2,4 --limit-tests 15 > $S/steer2/pilot_gemma_L52.out 2>&1 &
wait
echo "$(date +%H:%M:%S) pilot gemma layers done" >> $S/steer2/steer.log
