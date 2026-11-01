#!/usr/bin/env bash
# when a Llama judge has finished its annotation dirs: stop it and put two extra extraction workers on its GPUs
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
F=$S/fewshot; L=$F/run.log
( until grep -q "llama gemma__ex-long" $L; do sleep 60; done; $S/stop_vllm_port.sh 8040 >> $L 2>&1; sleep 40
  echo "$(date +%m-%d\ %H:%M:%S) llama 8040 stopped; extra hidden on GPUs 2,3" >> $L
  $F/xw2.sh 2 & $F/xw2.sh 3 & wait ) &
( until grep -q "llama qwen__ex-long" $L; do sleep 60; done; $S/stop_vllm_port.sh 8045 >> $L 2>&1; sleep 40
  echo "$(date +%m-%d\ %H:%M:%S) llama 8045 stopped; extra hidden on GPUs 0,1" >> $L
  $F/xw2.sh 0 & $F/xw2.sh 1 & wait ) &
wait
touch $F/hidden_extra.done
