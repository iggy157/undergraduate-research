#!/usr/bin/env bash
# Stop the pilot 5 script and any run_multi / run_single / server / agent it started (not vLLM), excluding this shell.
me=$$; parent=$PPID
for pat in "run_pilot5.sh" "scripts/run_multi.py" "scripts/run_single.py" "scripts/gen_scenarios.py" "-m server" "-m agent"; do
  for p in $(pgrep -u yharada -f -- "$pat"); do
    [ "$p" = "$me" ] || [ "$p" = "$parent" ] || { cmd=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$cmd" in *"bash -c "*|*shell-snapshots*|*kill_pilot5*) continue;; esac; kill -TERM $p 2>/dev/null && echo "TERM $p $pat"; }
  done
done
sleep 2
for pat in "run_pilot5.sh" "scripts/run_multi.py" "-m server" "-m agent"; do
  for p in $(pgrep -u yharada -f -- "$pat"); do
    [ "$p" = "$me" ] || [ "$p" = "$parent" ] || { cmd=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$cmd" in *"bash -c "*|*shell-snapshots*|*kill_pilot5*) continue;; esac; kill -KILL $p 2>/dev/null && echo "KILL $p"; }
  done
done
echo done
