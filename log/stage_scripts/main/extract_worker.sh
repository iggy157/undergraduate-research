#!/usr/bin/env bash
# standalone hidden-state extractor on GPU $1, same claim protocol as orchestrate_main.sh (hidden/main_gemma31b/.claim)
gpu=$1
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
H=$R/hidden/main_gemma31b
SNAP=$HOME/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
L=$S/main/orchestrate.log
cd $R
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
while true; do
  list=()
  for f in $R/log/main_gemma31b/*/*/*/*.log; do
    d=$(dirname "$f"); gid=$(basename $d)
    [ -f $H/$gid.npz ] && continue
    grep -q ",result," "$f" || continue
    mkdir $H/.claim/$gid 2>/dev/null || continue
    list+=("$d"); [ ${#list[@]} -ge 10 ] && break
  done
  if [ ${#list[@]} -gt 0 ]; then
    t0=$(date +%s)
    CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $SNAP --out-dir $H >> $S/main/hidden_gpu$gpu.out 2>&1
    rc=$?
    for d in "${list[@]}"; do gid=$(basename $d); [ -f $H/$gid.npz ] || { rmdir $H/.claim/$gid 2>/dev/null; log "hidden: $gid missing after rc=$rc (gpu $gpu)"; }; done
    log "hidden gpu$gpu: ${#list[@]} games in $(( $(date +%s) - t0 ))s rc=$rc, total $(ls $H/*.npz 2>/dev/null | wc -l)"
  else
    [ "$(ls $H/*.npz 2>/dev/null | wc -l)" -ge 630 ] && { log "hidden gpu$gpu: nothing left"; exit 0; }
    sleep 120
  fi
done
