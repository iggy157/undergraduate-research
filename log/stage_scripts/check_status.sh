#!/usr/bin/env bash
# hourly health check: real process counts, output growth, final products
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
echo "time $(date +%H:%M)"
echo "procs: probe_hidden2=$(ps -eo args | grep -c '[p]robe_hidden2') goal_swap=$(ps -eo args | grep -c '[g]oal_swap.py') steer=$(ps -eo args | grep -cE '[s]teer_goal2?[.]py') vllm_api=$(ps -eo args | grep -c '[v]llm.entrypoints.openai.api_server')"
for f in $S/swap/*.jsonl; do [ -f "$f" ] && echo "swap $(basename $f): $(wc -l < $f) lines, modified $(date -r $f +%H:%M)"; done
for f in $S/steer/*.jsonl $S/steer2/*.jsonl; do [ -f "$f" ] && echo "steer $(basename $f): $(wc -l < $f) lines, modified $(date -r $f +%H:%M)"; done 2>/dev/null
echo "probe v3: qwen $( [ -f $R/docs/main_qwen38/probe_summary_v3.md ] && echo done || grep -c ' base ' $S/probe3/qwen.out) gemma $( [ -f $R/docs/main_gemma31b/probe_summary_v3.md ] && echo done || grep -c ' base ' $S/probe3/gemma.out)"
grep -l "Traceback" $S/probe3/*.out $S/swap/qwen*.out $S/steer2/*.out 2>/dev/null | sed 's/^/TRACEBACK in /'
tail -n 2 $S/swap/swap.log
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ';'; echo
