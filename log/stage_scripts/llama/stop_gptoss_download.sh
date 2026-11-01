#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "download_gptoss.py|wait_and_start_gptoss.sh"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*stop_gptoss*) continue;; esac
  echo "TERM $p"; kill -TERM $p
done
