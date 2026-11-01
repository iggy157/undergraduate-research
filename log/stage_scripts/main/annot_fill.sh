#!/usr/bin/env bash
# annotate the games that are still missing for each judge (stable names): gpt-oss as soon as :8060 is up,
# Llama once the extractors on GPUs 1,2 are finished and :8040 is up again.
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
A=$S/annot_main; L=$S/main/annot_fill.log
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
log() { echo "$(date +%H:%M:%S) $*" >> $L; }
# gpt-oss
for i in $(seq 1 90); do curl -s localhost:8060/v1/models | grep -q gpt-oss && break; sleep 10; done
log "gpt-oss up; missing $(ls $A/games | wc -l) - $(ls $A/out | grep -c '^gptoss__')"
$S/pilot8/run_annot.sh $A http://localhost:8060/v1 gpt-oss-120b gptoss 12 20000
log "gptoss now $(ls $A/out | grep -c '^gptoss__')/630"
$S/stop_vllm_port.sh 8060 >> $L 2>&1
# llama: wait for the extractors on GPUs 1 and 2
until grep -q "hidden gpu1: nothing left" $S/main/orchestrate.log && grep -q "hidden gpu2: nothing left" $S/main/orchestrate.log; do sleep 60; done
sleep 20
$S/llama/start_vllm_llama.sh >> $L 2>&1
for i in $(seq 1 90); do curl -s localhost:8040/v1/models | grep -q llama && break; sleep 10; done
log "llama up; missing $(ls $A/games | wc -l) - $(ls $A/out | grep -c '^llama__')"
$S/pilot8/run_annot.sh $A http://localhost:8040/v1 llama-3.3-70b llama 12 12000
log "llama now $(ls $A/out | grep -c '^llama__')/630"
log "FILL DONE"
