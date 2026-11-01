#!/usr/bin/env bash
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
F=$S/fewshot
echo "time $(date +%H:%M)"
echo "procs: run_queue=$(ps -eo args | grep -c '[.]venv/bin/python scripts/run_queue.py') games=$(ps -eo args | grep -c '[.]venv/bin/python scripts/run_multi.py\|[s]ingle/base\|-m single') annot=$(ps -eo args | grep -c '[a]nnotate_llm.py') hidden=$(ps -eo args | grep -c '[e]xtract_hidden.py') vllm_api=$(ps -eo args | grep -c '[v]llm.entrypoints.openai.api_server')"
for q in $R/log/fewshot/*/_queue/progress.txt; do [ -f $q ] && echo "$(echo $q | awk -F/ '{print $(NF-2)}'): ok $(grep -c 'rc=0' $q), failed $(grep ' rc=' $q | grep -vc 'rc=0'), last $(tail -n 1 $q | cut -c1-60)"; done
tail -n 4 $F/run.log
for d in $S/annot_fewshot/*/; do [ -d $d ] && echo "annot $(basename $d): games $(ls $d/games | wc -l) llama $(ls $d/out | grep -c '^llama__') gptoss $(ls $d/out | grep -c '^gptoss__')"; done 2>/dev/null
echo "hidden: $(ls $R/hidden/fewshot/*/*.npz 2>/dev/null | wc -l)"
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tr '\n' ';'; echo
