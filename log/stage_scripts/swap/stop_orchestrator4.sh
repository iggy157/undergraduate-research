#!/usr/bin/env bash
# stop only the run_swap4.sh bash (its goal_swap children keep running)
for p in $(ps -eo pid=,args= | awk '/run_swap4.sh/ && !/awk/ && !/stop_orch/ {print $1}'); do
  [ "$p" = "$$" ] || [ "$p" = "$PPID" ] && continue; kill -TERM $p && echo "stopped $p"; done
