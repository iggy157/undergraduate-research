#!/usr/bin/env bash
# Stop only the vLLM api_server listening on the given port (and its engine), excluding this shell.
port=$1; me=$$; parent=$PPID
for p in $(pgrep -u yharada -f "vllm.entrypoints.openai.api_server"); do
  [ "$p" = "$me" ] || [ "$p" = "$parent" ] && continue
  cmd=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$cmd" in *"bash -c "*|*shell-snapshots*) continue;; esac
  case "$cmd" in *"--port $port"*) pg=$(ps -o pgid= -p $p | tr -d ' '); [ "$pg" != "$(ps -o pgid= -p $$ | tr -d ' ')" ] && kill -TERM -- -$pg && echo "TERM pgid $pg (port $port)";; esac
done
sleep 20; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader | sed -n 7,8p | tr '\n' ' '; echo
