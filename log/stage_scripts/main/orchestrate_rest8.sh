#!/usr/bin/env bash
# after Qwen: gemma-31B seat-stepped stage, then gemma-12B stage, both on 8 GPUs. Needs $S/main/gpu67.ok (GPUs 6,7 reserved).
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
until [ -f $S/qwen/all.done ] && [ -f $S/main/gpu67.ok ]; do sleep 60; done
$S/main/stage8.sh mps google/gemma-4-31B-it gemma-4-31b default $R/log/main_gemma31b multi-private-stepped,multi-private-stepped-process,multi-public-stepped \
  $S/annot_main $R/hidden/main_gemma31b $HOME/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475 4
touch $S/main/mps.done
$S/main/stage8.sh g12 google/gemma-4-12B-it gemma-4-12b g12 $R/log/main_gemma12b single-batch,single-batch-stepped,single-online,multi-public,multi-private,multi-private-stepped,multi-private-stepped-process,multi-public-stepped \
  $S/annot_g12 $R/hidden/main_gemma12b $HOME/.cache/huggingface/hub/models--google--gemma-4-12B-it/snapshots/707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7 4
touch $S/g12/all.done
echo "$(date +%m-%d\ %H:%M:%S) ALL STAGES DONE" >> $S/main/stage8.log
