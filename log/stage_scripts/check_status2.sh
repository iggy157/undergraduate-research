#!/usr/bin/env bash
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
echo "time $(date +%H:%M)"
echo "procs: swap_hidden=$(ps -eo args | grep -c '[.]venv/bin/python scripts/swap_hidden.py') line_judge=$(ps -eo args | grep -c '[.]venv/bin/python scripts/line_judge.py') vllm_api=$(ps -eo args | grep -c '[v]llm.entrypoints.openai.api_server')"
for f in $R/log/line_judge/*.jsonl; do echo "judge $(basename $f): $(wc -l < $f) lines, modified $(date -r $f +%H:%M)"; done
echo "hidden shards: $(ls $R/hidden/goal_swap/*/*.npz 2>/dev/null | wc -l)/12"; tail -n 3 $S/linejudge/hidden.log 2>/dev/null
for f in $S/linejudge/hidden_*.out; do tail -n 1 $f | grep -E "^[0-9]+/|done|Error" | sed "s|^|$(basename $f): |"; done
grep -l "Traceback" $S/linejudge/*.out 2>/dev/null | sed 's/^/TRACEBACK in /'
grep -h "unparsed" $S/linejudge/judge_*.out | tail -n 4
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | sed -n 1,6p | tr '\n' ';'; echo
