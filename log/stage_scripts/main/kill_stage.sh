#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "orchestrate_rest.sh|stage8.sh|stage6.sh|scripts/run_queue.py|scripts/run_multi.py|scripts/run_single.py|-m server --setup|-m agent --"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*kill_stage*) continue;; esac
  kill -TERM $p && echo "TERM $p"
done
