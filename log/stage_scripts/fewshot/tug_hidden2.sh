#!/usr/bin/env bash
# when the tug judging is done: stop the Llama judges and the slow one-GPU extraction of tug_run3.sh, then extract the
# hidden states of the four (model, framing) files in 7 shards each over GPUs 0-6; then mark the tug run done.
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
F=$S/fewshot; L=$F/tug.log; cd $R; O=log/goal_swap_ex
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
GM=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
QM=/home/yharada/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
while ps -eo args | grep -q "[.]venv/bin/python scripts/line_judge.py"; do sleep 60; done
log "tug judging done: $(cat log/line_judge/llama__*_ex.p*.jsonl | wc -l) lines"
for p in $(ps -eo pid=,args= | awk '/bash .*tug_run3.sh/ && !/awk/ {print $1}'); do
  for c in $(ps -o pid= --ppid $p); do kill -TERM $c 2>/dev/null; done; kill -TERM $p
done
for p in $(ps -eo pid=,args= | awk '/[.]venv\/bin\/python scripts\/swap_hidden.py/ {print $1}'); do kill -KILL $p; done
for port in 8045 8040 8047; do $S/stop_vllm_port.sh $port >> $L 2>&1; done
sleep 30
rm -rf hidden/goal_swap_ex
log "parallel extraction: 4 files x 7 shards on GPUs 0-6"
jobs=()
for spec in "gemma batch" "gemma online" "qwen batch" "qwen online"; do for i in 0 1 2 3 4 5 6; do jobs+=("$spec $i"); done; done
for g in 0 1 2 3 4 5 6; do
  ( k=0; for j in "${jobs[@]}"; do
      if [ $((k % 7)) = $g ]; then set -- $j; m=$1; t=$2; i=$3
        mp=$GM; ld=main_gemma31b; lay=20,40,48,56; [ $m = qwen ] && { mp=$QM; ld=main_qwen38; lay=20,32,48,52; }
        CUDA_VISIBLE_DEVICES=$g $VPY scripts/swap_hidden.py --log-dir log/$ld --swap $O/${m}__${t}_exshort.jsonl --model-path $mp --layers $lay --out-dir hidden/goal_swap_ex/${m}__${t}_exshort --shard $i/7 > $F/tug_hidden2_${m}_${t}_$i.out 2>&1
      fi; k=$((k+1)); done ) &
done
wait
log "hidden: $(ls hidden/goal_swap_ex/*/*.npz | wc -l)/28 shards"
log "TUG DONE"
touch $F/tug.done
