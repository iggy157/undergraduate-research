#!/usr/bin/env bash
# Stop the vLLM api_server started for the pilot (process group), excluding this shell.
me=$$; parent=$PPID
pids=$(pgrep -u yharada -f "vllm.entrypoints.openai.api_server" | grep -vE "^($me|$parent)$")
for p in $pids; do
  cmd=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null)
  case "$cmd" in *"bash -c "*|*shell-snapshots*) continue;; esac
  pg=$(ps -o pgid= -p $p | tr -d ' ')
  [ -n "$pg" ] && [ "$pg" != "$(ps -o pgid= -p $$ | tr -d ' ')" ] && kill -TERM -- -$pg 2>/dev/null && echo "TERM pgid $pg (pid $p)"
done
sleep 15
left=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | tr '\n' ' ')
if [ -n "$left" ]; then for p in $left; do owner=$(ps -o user= -p $p); [ "$owner" = yharada ] && kill -KILL $p && echo "KILL $p"; done; fi
sleep 3; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | tr '\n' ' '; echo
