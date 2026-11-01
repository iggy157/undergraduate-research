#!/usr/bin/env bash
# stop every hidden-state extraction (helper, extra workers, fewshot_run's xw subshells, the python processes), not the judges
me=$$; parent=$PPID
for p in $(ps -eo pid=,args= | awk '/hidden_helper.sh|xw2.sh/ && !/awk/ && !/stop_hidden/ {print $1}'); do [ "$p" = "$me" ] || [ "$p" = "$parent" ] && continue; kill -TERM $p 2>/dev/null; done
# fewshot_run.sh xw subshells: children of fewshot_run whose own children run extract_hidden.py
for p in $(ps -eo pid=,args= | awk '/[.]venv\/bin\/python scripts\/extract_hidden.py/ {print $1}'); do
  pp=$(ps -o ppid= -p $p | tr -d ' '); kill -TERM $pp 2>/dev/null; kill -TERM $p 2>/dev/null
done
sleep 10
for p in $(ps -eo pid=,args= | awk '/[.]venv\/bin\/python scripts\/extract_hidden.py/ {print $1}'); do kill -KILL $p 2>/dev/null; done
