#!/usr/bin/env bash
# extra gpt-oss annotation rounds (12 workers) alongside the orchestrator's 6
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
A=$S/annot_main; L=$S/main/gptoss_fast.log
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
while true; do
  n0=$(ls $A/out | grep -c '^gptoss_')
  $S/pilot8/run_annot.sh $A http://localhost:8060/v1 gpt-oss-120b gptoss 12 20000
  n1=$(ls $A/out | grep -c '^gptoss_'); ng=$(ls $A/games | wc -l)
  echo "$(date +%H:%M:%S) round: gptoss $n0 -> $n1 of $ng games" >> $L
  if [ -f log/main_gemma31b/_queue/queue.done ] && [ "$ng" -ge 630 ] && [ "$n1" -ge "$ng" ]; then echo "$(date +%H:%M:%S) GPTOSS DONE" >> $L; break; fi
  sleep 300
done
