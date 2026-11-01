#!/usr/bin/env bash
# Qwen, continued: seat-stepped conditions on the live servers (pinned by setup), then judges + hidden states for all.
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
LOGDIR=$R/log/main_qwen38
A=$S/annot_qwen
H=$R/hidden/main_qwen38
QS=$(ls -d $HOME/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/*/ | head -1)
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
L=$S/qwen/orchestrate.log
cd $R
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
while pgrep -f "main_qwen38_rep|_queue_mps " > /dev/null; do sleep 20; done
log "continuing: seat-stepped conditions (incl. multi-public-stepped) on the live Qwen servers"
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models qwen,qwen_b,qwen_c,qwen_d,qwen_e,qwen_f --per-model 1 --port-base 27300 --pin-by-setup \
  --conditions multi-private-stepped,multi-private-stepped-process,multi-public-stepped --out-dir $LOGDIR/_queue_mps >> $S/qwen/queue.out 2>&1
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models qwen,qwen_b,qwen_c,qwen_d,qwen_e,qwen_f --per-model 1 --port-base 27400 --pin-by-setup \
  --conditions multi-private-stepped,multi-private-stepped-process,multi-public-stepped --out-dir $LOGDIR/_queue_mps2 >> $S/qwen/queue.out 2>&1
log "seat-stepped done: $(ls -d $LOGDIR/*/multi-*-stepped/*/ 2>/dev/null | wc -l) games"
for port in 8000 8010 8020 8030 8040 8050; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
$S/llama/start_vllm_llama.sh >> $L 2>&1
$S/llama/start_vllm_gptoss.sh >> $L 2>&1
mkdir -p $A/games $A/out $A/raw $H $H/.claim
cp $R/scripts/prompts/ANNOTATION_INSTRUCTIONS_v2.md $A/ANNOTATION_INSTRUCTIONS.md
.venv/bin/python scripts/render_annotation.py --log-dir $LOGDIR --out-dir $A/games --stable-names --only-complete >> $S/qwen/render.out 2>&1
log "rendered $(ls $A/games | wc -l) games for annotation"
for i in $(seq 1 90); do curl -s localhost:8040/v1/models | grep -q llama && curl -s localhost:8060/v1/models | grep -q gpt-oss && break; sleep 10; done
log "judges up"
( $S/pilot8/run_annot.sh $A http://localhost:8040/v1 llama-3.3-70b llama 12 12000; log "llama annotated $(ls $A/out | grep -c '^llama__')" ) &
( $S/pilot8/run_annot.sh $A http://localhost:8060/v1 gpt-oss-120b gptoss 12 20000; log "gptoss annotated $(ls $A/out | grep -c '^gptoss__')" ) &
extract_worker() {
  local gpu=$1
  while true; do
    list=()
    for f in $LOGDIR/*/*/*/*.log; do
      d=$(dirname "$f"); gid=$(basename $d)
      [ -f $H/$gid.npz ] && continue
      grep -q ",result," "$f" || continue
      mkdir $H/.claim/$gid 2>/dev/null || continue
      list+=("$d"); [ ${#list[@]} -ge 15 ] && break
    done
    if [ ${#list[@]} -gt 0 ]; then
      t0=$(date +%s)
      CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $QS --out-dir $H >> $S/qwen/hidden_gpu$gpu.out 2>&1
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
log "QWEN ALL DONE: games $(ls -d $LOGDIR/*/*/*/ | wc -l), hidden $(ls $H/*.npz | wc -l), llama $(ls $A/out | grep -c '^llama__'), gptoss $(ls $A/out | grep -c '^gptoss__')"
touch $S/qwen/all.done
