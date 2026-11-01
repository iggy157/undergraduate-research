#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "scripts/probe_hidden.py --log-dir"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*kill_probe*) continue;; esac
  kill -TERM $p && echo "TERM $p"
done
