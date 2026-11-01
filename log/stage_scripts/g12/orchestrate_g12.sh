#!/usr/bin/env bash
# gemma-4-12B-it: 5 core + 3 seat-stepped conditions x 90 setups (720 games) on 6 servers, then judges + hidden states.
# Waits for the gemma-31B stepped stage ($S/main/mps.done) and for the reservation check marker ($S/g12/go).
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
LOGDIR=$R/log/main_gemma12b
A=$S/annot_g12
H=$R/hidden/main_gemma12b
SNAP=$HOME/.cache/huggingface/hub/models--google--gemma-4-12B-it/snapshots/707f0a3b8a3c7ad586ed01e27eafbad8a27dd0f7
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
L=$S/g12/orchestrate.log
cd $R
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
until [ -f $S/main/mps.done ] && [ -f $S/g12/go ]; do sleep 120; done
log "starting gemma-4-12B stage"
for port in 8000 8010 8020 8030 8040 8050 8060 8070; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
$S/g12/start_gemma12_6.sh >> $L 2>&1
for i in $(seq 1 120); do n=0; for p in 8000 8010 8020 8030 8040 8050; do curl -s localhost:$p/v1/models | grep -q gemma-4-12b && n=$((n+1)); done; [ $n = 6 ] && break; sleep 10; done
log "gemma-12b servers up: $n/6"
mkdir -p $LOGDIR
COND=single-batch,single-batch-stepped,single-online,multi-public,multi-private,multi-private-stepped,multi-private-stepped-process,multi-public-stepped
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models g12,g12_b,g12_c,g12_d,g12_e,g12_f --per-model 4 --port-base 30000 --conditions $COND >> $S/g12/queue.out 2>&1
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models g12,g12_b,g12_c,g12_d,g12_e,g12_f --per-model 4 --port-base 30100 --conditions $COND --out-dir $LOGDIR/_queue_repair >> $S/g12/queue.out 2>&1
log "generation done: $(ls -d $LOGDIR/*/*/*/ | wc -l) games, failed $(grep ' rc=' $LOGDIR/_queue/progress.txt | grep -vc 'rc=0')"
for port in 8000 8010 8020 8030 8040 8050; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
$S/llama/start_vllm_llama.sh >> $L 2>&1
$S/llama/start_vllm_gptoss.sh >> $L 2>&1
mkdir -p $A/games $A/out $A/raw $H $H/.claim
cp $R/scripts/prompts/ANNOTATION_INSTRUCTIONS_v2.md $A/ANNOTATION_INSTRUCTIONS.md
.venv/bin/python scripts/render_annotation.py --log-dir $LOGDIR --out-dir $A/games --stable-names --only-complete >> $S/g12/render.out 2>&1
log "rendered $(ls $A/games | wc -l) games"
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
      CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $SNAP --out-dir $H >> $S/g12/hidden_gpu$gpu.out 2>&1
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
log "G12 ALL DONE: games $(ls -d $LOGDIR/*/*/*/ | wc -l), hidden $(ls $H/*.npz | wc -l), llama $(ls $A/out | grep -c '^llama__'), gptoss $(ls $A/out | grep -c '^gptoss__')"
touch $S/g12/all.done
