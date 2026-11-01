#!/usr/bin/env bash
# stop the pilot 7 runner and everything it spawned (not the vLLM servers)
me=$$; par=$PPID
pids=$(pgrep -f "run_pilot7.sh|log/_pilot7|--port 110|--port 111|--port 112|--port 113" | grep -vx "$me" | grep -vx "$par")
for p in $pids; do
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null)
  case "$c" in *shell-snapshots*|*"bash -c "*|*kill_pilot7*) continue;; esac
  echo "TERM $p $(echo "$c" | cut -c1-90)"; kill -TERM $p 2>/dev/null
done
sleep 3
for p in $pids; do kill -0 $p 2>/dev/null && { echo "KILL $p"; kill -KILL $p 2>/dev/null; }; done
