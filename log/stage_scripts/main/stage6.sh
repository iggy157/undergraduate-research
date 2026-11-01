#!/usr/bin/env bash
# one 6-GPU stage: generation on 6 instances, then judges (Llama 1,2; gpt-oss 4) + hidden states (GPUs 0, 3, 5)
# usage: stage8.sh <label> <hf model> <served name> <model prefix: default|g12> <log dir> <conditions> <annot dir> <hidden dir> <snapshot> <per-model>
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
LABEL=$1; HF=$2; NAME=$3; PFX=$4; LOGDIR=$5; COND=$6; A=$7; H=$8; SNAP=$9; PER=${10:-4}
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
L=$S/main/stage8.log  # shared log (6-GPU variant)
cd $R
log() { echo "$(date +%m-%d\ %H:%M:%S) [$LABEL] $*" >> $L; }
MODELS=$PFX,${PFX}_b,${PFX}_c,${PFX}_d,${PFX}_e,${PFX}_f
for port in 8000 8010 8020 8030 8040 8045 8050 8060 8065 8070 8075; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
$S/main/start_gen6.sh $HF $NAME >> $L 2>&1
for i in $(seq 1 120); do n=0; for p in 8000 8010 8020 8030 8040 8050; do curl -s localhost:$p/v1/models | grep -q "\"$NAME\"" && n=$((n+1)); done; [ $n = 6 ] && break; sleep 10; done
log "generation servers up: $n/6"
mkdir -p $LOGDIR
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models $MODELS --per-model $PER --port-base 31000 --conditions $COND --out-dir $LOGDIR/_queue_$LABEL >> $S/main/stage8_$LABEL.out 2>&1
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models $MODELS --per-model $PER --port-base 31200 --conditions $COND --out-dir $LOGDIR/_queue_${LABEL}_repair >> $S/main/stage8_$LABEL.out 2>&1
log "generation done: $(grep ' rc=' $LOGDIR/_queue_$LABEL/progress.txt | grep -c 'rc=0') ok, $(grep ' rc=' $LOGDIR/_queue_$LABEL/progress.txt | grep -vc 'rc=0') failed (repair pass run)"
for port in 8000 8010 8020 8030 8040 8050; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
$S/llama/start_vllm_llama.sh >> $L 2>&1; $S/llama/start_vllm_gptoss.sh >> $L 2>&1
mkdir -p $A/games $A/out $A/raw $H $H/.claim
cp $R/scripts/prompts/ANNOTATION_INSTRUCTIONS_v2.md $A/ANNOTATION_INSTRUCTIONS.md
.venv/bin/python scripts/render_annotation.py --log-dir $LOGDIR --out-dir $A/games --stable-names --only-complete >> $S/main/stage8_render.out 2>&1
log "rendered $(ls $A/games | wc -l) games"
for i in $(seq 1 90); do n=0; for p in 8040 8060; do curl -s localhost:$p/v1/models | grep -q '"id"' && n=$((n+1)); done; [ $n = 2 ] && break; sleep 10; done
log "judges up: $n/2"
( $S/pilot8/run_annot2.sh $A http://localhost:8040/v1 llama-3.3-70b llama 12 12000; log "llama annotated $(ls $A/out | grep -c '^llama__')" ) &
( $S/pilot8/run_annot2.sh $A http://localhost:8060/v1 gpt-oss-120b gptoss 12 20000; log "gptoss annotated $(ls $A/out | grep -c '^gptoss__')" ) &
extract_worker() {
  local gpu=$1
  while true; do
    list=()
    for f in $LOGDIR/*/*/*/*.log; do
      d=$(dirname "$f"); gid=$(basename $d)
      [ -f $H/$gid.npz ] && continue
      grep -q ",result," "$f" || continue
      mkdir $H/.claim/$gid 2>/dev/null || continue
      list+=("$d"); [ ${#list[@]} -ge 20 ] && break
    done
    if [ ${#list[@]} -gt 0 ]; then
      t0=$(date +%s)
      CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $SNAP --out-dir $H >> $S/main/stage8_hidden_${LABEL}_gpu$gpu.out 2>&1
      rc=$?
      for d in "${list[@]}"; do gid=$(basename $d); [ -f $H/$gid.npz ] || { rmdir $H/.claim/$gid 2>/dev/null; log "hidden: $gid missing after rc=$rc (gpu $gpu)"; }; done
      log "hidden gpu$gpu: ${#list[@]} games in $(( $(date +%s) - t0 ))s rc=$rc, total $(ls $H/*.npz 2>/dev/null | wc -l)"
    else
      log "hidden gpu$gpu: nothing left"; return
    fi
  done
}
extract_worker 0 & extract_worker 3 & extract_worker 5 &
wait
log "STAGE DONE: games $(ls -d $LOGDIR/*/*/*/ | wc -l), hidden $(ls $H/*.npz | wc -l), llama $(ls $A/out | grep -c '^llama__'), gptoss $(ls $A/out | grep -c '^gptoss__')"
