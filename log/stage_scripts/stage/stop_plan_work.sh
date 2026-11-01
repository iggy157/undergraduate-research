#!/usr/bin/env bash
# stop the Qwen plan stage and the queued grid by explicit PID (checked by command line), then the Qwen servers
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
for p in 1973906 1858435; do
  [ -d /proc/$p ] || continue
  grep -qE "run_grid.sh|model_stage.sh" /proc/$p/cmdline || continue
  kids=$(ps -o pid= --ppid $p)
  kill -TERM $p $kids 2>/dev/null; sleep 3; kill -KILL $p $kids 2>/dev/null
  echo "stopped $p (+ $kids)"
done
$S/main/kill_vllm_all.sh
echo "$(date +%m-%d\ %H:%M:%S) [qwenplan] stopped by decision: plan conditions are not needed (Qwen plans 56/90 kept in scenarios_qwen38)" >> $S/stage/stage.log
