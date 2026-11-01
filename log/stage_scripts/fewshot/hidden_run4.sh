#!/usr/bin/env bash
# relaunch of the few-shot hidden-state extraction (chunked fallback for long sequences) on GPUs 0-3, 5-7
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
F=$S/fewshot
for g in 0 1 2 3 5 6 7; do $F/xw2.sh $g & done
wait
echo "$(date +%m-%d\ %H:%M:%S) hidden run4 done" >> $F/run.log
touch $F/hidden_extra.done
