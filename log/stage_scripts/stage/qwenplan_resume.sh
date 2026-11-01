#!/usr/bin/env bash
# 1) parallel retry (10 attempts) of the Qwen plans still missing; 2) stop the stalled sequential stage (explicit PIDs);
# 3) resume the same stage label from generation with the servers already up (setups without a plan are dropped by run_queue).
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
OLD=1858435
cd $R; P=scenarios_qwen38; mkdir -p $S/stage/gen_qwenplan_retry2
i=0
for d in aiwolf candidate_selection shared_living; do for f in setups/$d/*.json; do sid=$(basename $f .json)
  [ -f $P/$d/$sid.json ] && continue; [ $sid = candidate_selection_0003 ] && continue
  m=$(echo qwen,qwen_b,qwen_c,qwen_d,qwen_e,qwen_f | cut -d, -f$(( i % 6 + 1 ))); i=$((i+1)); echo "$sid $m"
done; done | xargs -P 12 -L 1 bash -c '.venv/bin/python scripts/gen_scenarios.py --setups $0 --model $1 --out-dir scenarios_qwen38 --attempts 10 --force > '"$S"'/stage/gen_qwenplan_retry2/$0.out 2>&1; echo "$0 rc=$? $(date +%H:%M:%S)" >> '"$S"'/stage/gen_qwenplan_retry2/progress.txt'
echo "$(date +%m-%d\ %H:%M:%S) [qwenplan] parallel retry done: plans $(ls $P/*/ | grep -v attempts | grep -v failed | grep -c json)/90" >> $S/stage/stage.log
# stop the stalled stage: the bash script and its children, by PID
if [ -d /proc/$OLD ] && grep -q "model_stage.sh" /proc/$OLD/cmdline; then
  kids=$(ps -o pid= --ppid $OLD); kill -TERM $OLD $kids 2>/dev/null; sleep 5; kill -KILL $OLD $kids 2>/dev/null
fi
echo "$(date +%m-%d\ %H:%M:%S) [qwenplan] stalled stage stopped; resuming from generation" >> $S/stage/stage.log
$S/stage/model_stage3.sh qwenplan $S/qwen/start_vllm_qwen.sh qwen3.8-27b qwen $R/log/main_qwen38 single-batch-process,multi-private-process,multi-private-stepped-process $R/scenarios_qwen38 /home/yharada/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/ $S/annot_qwen $R/hidden/main_qwen38 1
