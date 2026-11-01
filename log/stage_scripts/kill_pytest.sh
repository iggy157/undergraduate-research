#!/bin/bash
# kill the hung pytest (and the bash wrapper that started it), never ourselves
me=$$; parent=$PPID
for pid in $(pgrep -u yharada -f "python -m pytest -q"); do
  [ "$pid" = "$me" ] && continue; [ "$pid" = "$parent" ] && continue
  cmd=$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null)
  case "$cmd" in *shell-snapshots*|*"bash -c "*) continue;; esac
  echo "killing $pid: ${cmd:0:60}"; kill -TERM "$pid"; sleep 1; kill -KILL "$pid" 2>/dev/null
done
