#!/usr/bin/env bash
# after the running Qwen plan stage: the 4 missing plan conditions for gemma-31B, then for Qwen (14-condition grid)
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
until grep -q "\[qwenplan\] STAGE DONE" $S/stage/stage.log; do sleep 60; done
$S/stage/model_stage2.sh gemmagrid $S/stage/gemma_one.sh gemma-4-31b default $R/log/main_gemma31b single-batch-stepped-process,single-online-process,multi-public-process,multi-public-stepped-process $R/scenarios /home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475 $S/annot_main $R/hidden/main_gemma31b 4
$S/stage/model_stage2.sh qwengrid $S/qwen/start_vllm_qwen.sh qwen3.8-27b qwen $R/log/main_qwen38 single-batch-stepped-process,single-online-process,multi-public-process,multi-public-stepped-process $R/scenarios_qwen38 /home/yharada/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/ $S/annot_qwen $R/hidden/main_qwen38 1
echo "$(date +%m-%d\ %H:%M:%S) GRID DONE" >> $S/stage/stage.log
touch $S/stage/grid.done
