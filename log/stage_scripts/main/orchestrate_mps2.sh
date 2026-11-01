#!/usr/bin/env bash
# gemma-4-31B multi-private-stepped: 90 games on 6 gemma servers (4 per server), then judges + hidden states.
# Runs after the Qwen orchestrator has written $S/qwen/all.done.
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
LOGDIR=$R/log/main_gemma31b
A=$S/annot_main
H=$R/hidden/main_gemma31b
SNAP=$HOME/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
L=$S/main/orchestrate_mps.log
cd $R
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
until [ -f $S/qwen/all.done ]; do sleep 120; done
log "qwen done; starting gemma servers for multi-private-stepped"
for port in 8000 8010 8020 8030 8040 8050 8060 8070; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
$S/main/start_gemma_5.sh >> $L 2>&1   # GPUs 0,1,2,4,5 -> 8000 8010 8020 8040 8050
( cd /diskthalys/ssd14ta/yharada/vllm-server; VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-31B-it NAME=gemma-4-31b GPUS=3 PORT=8030 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > logs/ugr_gemma4_31b_$(date +%Y%m%d_%H%M)_gpu3.log 2>&1 < /dev/null & )
for i in $(seq 1 120); do n=0; for p in 8000 8010 8020 8030 8040 8050; do curl -s localhost:$p/v1/models | grep -q gemma-4-31b && n=$((n+1)); done; [ $n = 6 ] && break; sleep 10; done
log "gemma servers up: $n/6"
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models default,default_b,default_c,default_d,default_e,default_f --per-model 4 --port-base 28000 --conditions multi-private-stepped,multi-private-stepped-process --out-dir $LOGDIR/_queue_mps >> $S/main/queue_mps.out 2>&1
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models default,default_b,default_c,default_d,default_e,default_f --per-model 4 --port-base 28100 --conditions multi-private-stepped,multi-private-stepped-process --out-dir $LOGDIR/_queue_mps2 >> $S/main/queue_mps.out 2>&1
log "mps generation done: $(ls -d $LOGDIR/*/multi-private-stepped*/*/ 2>/dev/null | wc -l) games"
for port in 8000 8010 8020 8030 8040 8050; do $S/stop_vllm_port.sh $port > /dev/null 2>&1; done
$S/llama/start_vllm_llama.sh >> $L 2>&1
$S/llama/start_vllm_gptoss.sh >> $L 2>&1
.venv/bin/python scripts/render_annotation.py --log-dir $LOGDIR --out-dir $A/games --stable-names --only-complete >> $S/main/render.out 2>&1
log "rendered: $(ls $A/games | wc -l) games"
for i in $(seq 1 90); do curl -s localhost:8040/v1/models | grep -q llama && curl -s localhost:8060/v1/models | grep -q gpt-oss && break; sleep 10; done
( $S/pilot8/run_annot.sh $A http://localhost:8040/v1 llama-3.3-70b llama 12 12000; log "llama annotated $(ls $A/out | grep -c '^llama__')" ) &
( $S/pilot8/run_annot.sh $A http://localhost:8060/v1 gpt-oss-120b gptoss 12 20000; log "gptoss annotated $(ls $A/out | grep -c '^gptoss__')" ) &
extract_worker() {
  local gpu=$1
  while true; do
    list=()
    for f in $LOGDIR/*/multi-private-stepped*/*/*.log; do
      d=$(dirname "$f"); gid=$(basename $d)
      [ -f $H/$gid.npz ] && continue
      grep -q ",result," "$f" || continue
      mkdir $H/.claim/$gid 2>/dev/null || continue
      list+=("$d"); [ ${#list[@]} -ge 15 ] && break
    done
    if [ ${#list[@]} -gt 0 ]; then
      t0=$(date +%s)
      CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $SNAP --out-dir $H >> $S/main/hidden_mps_gpu$gpu.out 2>&1
      rc=$?
      for d in "${list[@]}"; do gid=$(basename $d); [ -f $H/$gid.npz ] || { rmdir $H/.claim/$gid 2>/dev/null; log "hidden: $gid missing after rc=$rc (gpu $gpu)"; }; done
      log "hidden gpu$gpu: ${#list[@]} games in $(( $(date +%s) - t0 ))s rc=$rc"
    else
      log "hidden gpu$gpu: nothing left"; return
    fi
  done
}
extract_worker 0 & extract_worker 3 & extract_worker 5 &
wait
log "MPS ALL DONE: games $(ls -d $LOGDIR/*/multi-private-stepped*/*/ | wc -l), hidden $(ls $H/*multi-private-stepped*.npz | wc -l), llama $(ls $A/out | grep -c '^llama__.*multi-private-stepped'), gptoss $(ls $A/out | grep -c '^gptoss__.*multi-private-stepped')"
touch $S/main/mps.done
