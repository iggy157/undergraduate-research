#!/usr/bin/env bash
for p in $(ps -eo pid=,args= | awk '/run_swap2.sh|goal_swap.py/ && !/awk/ && !/stop_swap/ {print $1}'); do
  [ "$p" = "$$" ] || [ "$p" = "$PPID" ] && continue
  kill -TERM $p 2>/dev/null; echo "stopped $p"
done
