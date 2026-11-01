#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -u yharada -f "vllm.entrypoints.openai.api_server|VLLM::EngineCore|stop_vllm_port.sh"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*kill_vllm_all*) continue;; esac
  kill -TERM $p && echo "TERM $p"
done
sleep 15
for p in $(pgrep -u yharada -f "vllm.entrypoints.openai.api_server|VLLM::EngineCore"); do kill -KILL $p 2>/dev/null && echo "KILL $p"; done
