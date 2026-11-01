#!/usr/bin/env bash
# when both Qwen annotations are done, free the judge GPUs (1,2,4) and add hidden-state extractors there
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
LOGDIR=$R/log/main_qwen38; H=$R/hidden/main_qwen38; A=$S/annot_qwen
QS=$(ls -d $HOME/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/*/ | head -1)
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
L=$S/qwen/orchestrate.log
cd $R
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
until [ -f $A/llama.done ] && [ -f $A/gptoss.done ]; do sleep 60; done
log "annotations finished (llama $(ls $A/out | grep -c '^llama__'), gptoss $(ls $A/out | grep -c '^gptoss__')); judge GPUs -> extra extractors"
for port in 8040 8060; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
w() {
  local gpu=$1
  while true; do
    list=()
    for f in $LOGDIR/*/*/*/*.log; do
      d=$(dirname "$f"); gid=$(basename $d)
      [ -f $H/$gid.npz ] && continue
      grep -q ",result," "$f" || continue
      mkdir $H/.claim/$gid 2>/dev/null || continue
      list+=("$d"); [ ${#list[@]} -ge 10 ] && break
    done
    [ ${#list[@]} -eq 0 ] && { log "hidden gpu$gpu: nothing left"; return; }
    CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $QS --out-dir $H >> $S/qwen/hidden_gpu$gpu.out 2>&1
    rc=$?
    for d in "${list[@]}"; do gid=$(basename $d); [ -f $H/$gid.npz ] || { rmdir $H/.claim/$gid 2>/dev/null; log "hidden: $gid missing after rc=$rc (gpu $gpu)"; }; done
    log "hidden gpu$gpu: ${#list[@]} games rc=$rc, total $(ls $H/*.npz 2>/dev/null | wc -l)"
  done
}
w 1 & w 2 & w 4 &
wait
