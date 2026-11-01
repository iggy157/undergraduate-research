#!/usr/bin/env bash
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
$S/stage/model_stage.sh qwenplan $S/qwen/start_vllm_qwen.sh qwen3.8-27b qwen $R/log/main_qwen38 single-batch-process,multi-private-process,multi-private-stepped-process $R/scenarios_qwen38 /home/yharada/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/ $S/annot_qwen $R/hidden/main_qwen38
touch $S/stage/qwen.done
$S/stage/model_stage.sh mistral $S/mistral/start_one.sh mistral-small-3.2-24b mis $R/log/main_mistral32 single-batch,single-batch-stepped,single-online,multi-public,multi-private,multi-private-stepped,multi-public-stepped,single-batch-process,multi-private-process,multi-private-stepped-process $R/scenarios_mistral32 /home/yharada/.cache/huggingface/hub/models--mistralai--Mistral-Small-3.2-24B-Instruct-2506/snapshots/95a6d26c4bfb886c58daf9d3f7332c857cb27b43/ $S/annot_mistral $R/hidden/main_mistral32
touch $S/stage/mistral.done
echo "$(date +%m-%d\ %H:%M:%S) ALL DONE" >> $S/stage/stage.log
