#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "orchestrate_mps3.sh|orchestrate_g12.sh"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*kill_old*) continue;; esac
  echo "TERM $p"; kill -TERM $p
done
