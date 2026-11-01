#!/usr/bin/env bash
# When the plan-job queue writes queue.done, hide it, run one more pass over every (setup, condition) that has no
# log (jobs that failed, e.g. the games whose directories were removed by mistake at 22:20), then restore queue.done
# so that the orchestrator's phase 3 starts only after the repair pass.
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
Q=log/main_gemma31b/_queue
until [ -f $Q/queue.done ]; do sleep 5; done
mv $Q/queue.done $Q/queue.done.main
echo "$(date +%H:%M:%S) main queue done; repair pass" >> $S/main/repair.log
while pgrep -f "scripts/run_(single|multi).py" > /dev/null; do sleep 20; done
.venv/bin/python scripts/run_queue.py --log-dir log/main_gemma31b --models default,default_d --per-model 4 --port-base 23000 --out-dir $Q/../_queue_repair2 >> $S/main/repair.log 2>&1
n=$(.venv/bin/python scripts/run_queue.py --log-dir log/main_gemma31b --models default --dry-run | head -1)
echo "$(date +%H:%M:%S) after repair: $n" >> $S/main/repair.log
touch $Q/queue.done
