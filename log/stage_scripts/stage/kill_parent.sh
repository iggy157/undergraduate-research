#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "stage/run_qwen_then_mistral.sh"); do [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue; kill -TERM $p && echo "TERM $p"; done
