#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "gemma_xinst/run.sh"); do [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue; kill -TERM $p && echo "TERM $p"; done
