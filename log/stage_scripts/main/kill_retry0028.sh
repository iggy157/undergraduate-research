#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "gen_scenarios.py --setups aiwolf_0028"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*kill_retry*) continue;; esac
  echo "TERM $p"; kill -TERM $p
done
