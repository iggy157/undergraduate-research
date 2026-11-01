#!/usr/bin/env bash
for p in $(ps -eo pid=,args= | awk '/run_swap.sh/ && !/awk/ && !/stop_swap/ {print $1}'); do
  [ "$p" = "$$" ] || [ "$p" = "$PPID" ] && continue
  kids=$(ps -o pid= --ppid $p); kill -TERM $p $kids 2>/dev/null; echo "stopped $p $kids"
done
