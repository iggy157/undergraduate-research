#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "scripts/run_queue.py|scripts/run_multi.py|scripts/run_single.py|server/__main__|agent/__main__"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*kill_queue2*) continue;; esac
  echo "TERM $p ${c:0:80}"; kill -TERM $p
done
