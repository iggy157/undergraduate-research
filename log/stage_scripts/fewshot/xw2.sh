#!/usr/bin/env bash
# extra hidden-state extraction worker on GPU $1, sharing the claim directories of fewshot_run.sh (30 games per load)
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
F=$S/fewshot; L=$F/run.log; cd $R; gpu=$1
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
GM=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
QM=/home/yharada/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/
DIRS="gemma__ex-short gemma__ex-long qwen__ex-short qwen__ex-long"
while true; do
  list=(); mp=""
  for d in $DIRS; do
    H=$R/hidden/fewshot/$d; mkdir -p $H/.claim
    for f in log/fewshot/$d/*/*/*/*.log; do gd=$(dirname "$f"); gid=$(basename $gd)
      [ -f $H/$gid.npz ] && continue; grep -q ",result," "$f" || continue
      mkdir $H/.claim/$gid 2>/dev/null || continue; list+=("$gd"); [ ${#list[@]} -ge 30 ] && break
    done
    if [ ${#list[@]} -gt 0 ]; then mp=$GM; [[ $d == qwen* ]] && mp=$QM; break; fi
  done
  [ ${#list[@]} -eq 0 ] && { echo "$(date +%m-%d\ %H:%M:%S) extra hidden gpu$gpu: nothing left" >> $L; exit 0; }
  CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $mp --out-dir $H >> $F/hidden_extra_gpu$gpu.out 2>&1
  for gd in "${list[@]}"; do gid=$(basename $gd); [ -f $H/$gid.npz ] || { rmdir $H/.claim/$gid 2>/dev/null; echo "$(date +%m-%d\ %H:%M:%S) hidden: $gid missing" >> $L; }; done
done
