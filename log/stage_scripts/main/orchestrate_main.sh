#!/usr/bin/env bash
# Main run (gemma-4-31B), phases after the core conditions: judges + remaining plan jobs + hidden states.
# Runs detached (setsid nohup). Log: $S/main/orchestrate.log
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
VS=/diskthalys/ssd14ta/yharada/vllm-server
LOGDIR=$R/log/main_gemma31b
P=$LOGDIR/_queue/progress.txt
A=$S/annot_main                      # annotation dir (games/, games.json, out/, raw/)
H=$R/hidden/main_gemma31b            # hidden states
SNAP=$HOME/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
VPY=$VS/.venv/bin/python
L=$S/main/orchestrate.log
cd $R
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
n_done_cond() { grep -E " ($1) " $P 2>/dev/null | grep -c "rc=0"; }
complete_games() { # game dirs with a result row
  for f in $LOGDIR/*/*/*/*.log; do grep -q ",result," "$f" && dirname "$f"; done
}

log "orchestrator started; waiting for the core conditions (online/public/private = 243)"
until [ "$(n_done_cond 'single-online|multi-public|multi-private')" -ge 243 ]; do sleep 120; done
log "core conditions done ($(grep -c ' rc=' $P) jobs). stopping the queue runner and 4 gemma servers"

# ---- phase 2a: stop the runner (its running games finish on their own), then free GPUs 1,2,4,5
me=$$
for p in $(pgrep -f "scripts/run_queue.py"); do [ "$p" = "$me" ] && continue; kill -TERM $p; done
sleep 5
while pgrep -f "scripts/run_(single|multi).py" > /dev/null; do sleep 30; done
log "no games running; stopping gemma on 8010 8020 8040 8050"
for port in 8010 8020 8040 8050; do $S/stop_vllm_port.sh $port >> $L 2>&1; done
sleep 10
$S/llama/start_vllm_llama.sh >> $L 2>&1      # GPUs 1,2 -> :8040
$S/llama/start_vllm_gptoss.sh >> $L 2>&1     # GPU 4   -> :8060
# remaining plan jobs on the two gemma servers that stay up (:8000 default, :8030 default_d)
(setsid nohup .venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models default,default_d --per-model 4 --port-base 21000 > $LOGDIR/_queue_launch2.out 2>&1 < /dev/null &)
log "restarted the queue on default,default_d for the plan jobs"
for i in $(seq 1 90); do
  sleep 10
  curl -s localhost:8040/v1/models | grep -q llama && curl -s localhost:8060/v1/models | grep -q gpt-oss && break
done
curl -s localhost:8040/v1/models | grep -q llama || log "WARNING: llama not ready"
curl -s localhost:8060/v1/models | grep -q gpt-oss || log "WARNING: gpt-oss not ready"
log "judges up: llama :8040 (GPU 1,2), gpt-oss :8060 (GPU 4)"

# ---- phase 2b: annotation loop (new complete games every round)
mkdir -p $A/games $A/out $A/raw
cp $R/scripts/prompts/ANNOTATION_INSTRUCTIONS_v2.md $A/ANNOTATION_INSTRUCTIONS.md
(
  while true; do
    .venv/bin/python scripts/render_annotation.py --log-dir $LOGDIR --out-dir $A/games --stable-names --only-complete >> $S/main/render.out 2>&1
    ng=$(ls $A/games | wc -l)
    $S/pilot8/run_annot.sh $A http://localhost:8040/v1 llama-3.3-70b llama 6 12000 &
    $S/pilot8/run_annot.sh $A http://localhost:8060/v1 gpt-oss-120b gptoss 6 20000 &
    wait
    nl=$(ls $A/out | grep -c '^llama_'); ngp=$(ls $A/out | grep -c '^gptoss_')
    log "annotation round: games $ng, llama $nl, gptoss $ngp"
    if [ -f $LOGDIR/_queue/queue.done ] && [ "$ng" -ge 630 ] && [ "$nl" -ge 630 ] && [ "$ngp" -ge 630 ]; then log "ANNOTATION DONE"; touch $S/main/annot.done; break; fi
    sleep 600
  done
) &

# ---- phase 3: hidden states (GPU 5 now; GPUs 0 and 3 after the queue is done)
mkdir -p $H $H/.claim
extract_worker() { # $1 = gpu
  local gpu=$1
  while true; do
    list=()
    for d in $(complete_games); do
      gid=$(basename $d)
      [ -f $H/$gid.npz ] && continue
      mkdir $H/.claim/$gid 2>/dev/null || continue
      list+=("$d"); [ ${#list[@]} -ge 20 ] && break
    done
    if [ ${#list[@]} -gt 0 ]; then
      t0=$(date +%s)
      CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $SNAP --out-dir $H >> $S/main/hidden_gpu$gpu.out 2>&1
      rc=$?
      for d in "${list[@]}"; do gid=$(basename $d); [ -f $H/$gid.npz ] || { rmdir $H/.claim/$gid 2>/dev/null; log "hidden: $gid missing after rc=$rc (gpu $gpu)"; }; done
      log "hidden gpu$gpu: ${#list[@]} games in $(( $(date +%s) - t0 ))s rc=$rc, total $(ls $H/*.npz 2>/dev/null | wc -l)"
    else
      if [ -f $LOGDIR/_queue/queue.done ] && [ "$(ls $H/*.npz 2>/dev/null | wc -l)" -ge 630 ]; then log "hidden gpu$gpu: nothing left"; return; fi
      sleep 300
    fi
  done
}
extract_worker 5 &
# when the plan jobs finish, free GPUs 0 and 3 and add two extractors
(
  until [ -f $LOGDIR/_queue/queue.done ]; do sleep 120; done
  while pgrep -f "scripts/run_(single|multi).py" > /dev/null; do sleep 30; done
  log "queue done ($(grep -c ' rc=' $P) jobs, $(grep ' rc=' $P | grep -vc 'rc=0') failed); stopping gemma on 8000 8030"
  for port in 8000 8030; do $S/stop_vllm_port.sh $port >> $L 2>&1; done
  extract_worker 0 &
  extract_worker 3 &
  wait
) &
wait
log "ALL PHASES DONE: games $(ls -d $LOGDIR/*/*/*/ | wc -l), hidden $(ls $H/*.npz | wc -l), annotations llama $(ls $A/out | grep -c '^llama_') gptoss $(ls $A/out | grep -c '^gptoss_')"
touch $S/main/all.done
