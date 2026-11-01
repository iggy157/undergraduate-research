#!/usr/bin/env bash
# One model stage on GPUs 0-5: servers -> plans (own model) -> generation (pinned by setup) -> judges + hidden states.
# usage: model_stage.sh <label> <start script taking GPU PORT> <served name> <model prefix> <log dir> <conditions> <plan dir> <snapshot> <annot dir> <hidden dir>
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
LABEL=$1; START=$2; NAME=$3; PFX=$4; LOGDIR=$5; COND=$6; PLANS=$7; SNAP=$8; A=$9; H=${10}; PER=${11:-2}
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
L=$S/stage/stage.log
cd $R
log() { echo "$(date +%m-%d\ %H:%M:%S) [$LABEL] $*" >> $L; }
MODELS=$PFX,${PFX}_b,${PFX}_c,${PFX}_d,${PFX}_e,${PFX}_f
PORTS=(8000 8010 8020 8030 8040 8050)
$S/main/kill_vllm_all.sh > /dev/null 2>&1
for g in 0 1 2 3 4 5; do $START $g ${PORTS[$g]} >> $L 2>&1; done
for i in $(seq 1 120); do n=0; for p in ${PORTS[@]}; do curl -s localhost:$p/v1/models | grep -q "\"$NAME\"" && n=$((n+1)); done; [ $n = 6 ] && break; sleep 10; done
log "servers up: $n/6"
# ---- plans with this model (one process per setup, 12 at a time over the 6 servers)
mkdir -p $PLANS $S/stage/gen_$LABEL
i=0
for d in aiwolf candidate_selection shared_living; do for f in setups/$d/*.json; do sid=$(basename $f .json)
  [ -f $PLANS/$d/$sid.json ] && continue
  m=$(echo $MODELS | cut -d, -f$(( i % 6 + 1 ))); i=$((i+1)); echo "$sid $m"
done; done | xargs -P 12 -L 1 bash -c ".venv/bin/python scripts/gen_scenarios.py --setups \$0 --model \$1 --out-dir $PLANS > $S/stage/gen_$LABEL/\$0.out 2>&1"
for d in aiwolf candidate_selection shared_living; do for f in setups/$d/*.json; do sid=$(basename $f .json)
  [ -f $PLANS/$d/$sid.json ] || .venv/bin/python scripts/gen_scenarios.py --setups $sid --model $PFX --out-dir $PLANS --attempts 8 --force > $S/stage/gen_$LABEL/${sid}_retry.out 2>&1
done; done
log "plans: $(ls $PLANS/*/ | grep -v attempts | grep -v failed | grep -c json)/90"
# ---- generation, pinned by setup
mkdir -p $LOGDIR
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models $MODELS --per-model $PER --port-base 35000 --pin-by-setup --scenario-root $PLANS --conditions $COND --out-dir $LOGDIR/_queue_$LABEL >> $S/stage/q_$LABEL.out 2>&1
.venv/bin/python scripts/run_queue.py --log-dir $LOGDIR --models $MODELS --per-model $PER --port-base 35200 --pin-by-setup --scenario-root $PLANS --conditions $COND --out-dir $LOGDIR/_queue_${LABEL}_repair >> $S/stage/q_$LABEL.out 2>&1
log "generation: $(grep ' rc=' $LOGDIR/_queue_$LABEL/progress.txt | grep -c 'rc=0') ok, $(grep ' rc=' $LOGDIR/_queue_$LABEL/progress.txt | grep -vc 'rc=0') failed in the first pass"
$S/main/kill_vllm_all.sh > /dev/null 2>&1
# ---- judges (Llama 1,2; gpt-oss 4) + hidden states (0,3,5), then the judge GPUs join the extraction
$S/llama/start_vllm_llama.sh >> $L 2>&1; $S/llama/start_vllm_gptoss.sh >> $L 2>&1
mkdir -p $A/games $A/out $A/raw $H $H/.claim
cp $R/scripts/prompts/ANNOTATION_INSTRUCTIONS_v2.md $A/ANNOTATION_INSTRUCTIONS.md
.venv/bin/python scripts/render_annotation.py --log-dir $LOGDIR --out-dir $A/games --stable-names --only-complete >> $S/stage/render.out 2>&1
log "rendered $(ls $A/games | wc -l)"
for i in $(seq 1 90); do curl -s localhost:8040/v1/models | grep -q llama && curl -s localhost:8060/v1/models | grep -q gpt-oss && break; sleep 10; done
xw() {
  local gpu=$1
  while true; do
    list=()
    for f in $LOGDIR/*/*/*/*.log; do d=$(dirname "$f"); gid=$(basename $d)
      [ -f $H/$gid.npz ] && continue; grep -q ",result," "$f" || continue
      mkdir $H/.claim/$gid 2>/dev/null || continue; list+=("$d"); [ ${#list[@]} -ge 10 ] && break
    done
    [ ${#list[@]} -eq 0 ] && { log "hidden gpu$gpu: nothing left"; return; }
    CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $SNAP --out-dir $H >> $S/stage/hidden_${LABEL}_gpu$gpu.out 2>&1
    rc=$?
    for d in "${list[@]}"; do gid=$(basename $d); [ -f $H/$gid.npz ] || { rmdir $H/.claim/$gid 2>/dev/null; log "hidden: $gid missing after rc=$rc"; }; done
  done
}
( $S/pilot8/run_annot2.sh $A http://localhost:8040/v1 llama-3.3-70b llama 12 12000; log "llama annotated $(ls $A/out | grep -c '^llama__')" ) &
PA=$!
( $S/pilot8/run_annot2.sh $A http://localhost:8060/v1 gpt-oss-120b gptoss 12 20000; log "gptoss annotated $(ls $A/out | grep -c '^gptoss__')" ) &
PB=$!
xw 0 & xw 3 & xw 5 &
wait $PA $PB
$S/main/kill_vllm_all.sh > /dev/null 2>&1
xw 1 & xw 2 & xw 4 &
wait
log "STAGE DONE: games $(ls -d $LOGDIR/*/*/*/ | wc -l), hidden $(ls $H/*.npz | wc -l), llama $(ls $A/out | grep -c '^llama__'), gptoss $(ls $A/out | grep -c '^gptoss__')"
