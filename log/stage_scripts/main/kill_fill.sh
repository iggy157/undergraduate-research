#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "annot_fill.sh|run_annot.sh|annotate_llm.py"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*kill_fill*) continue;; esac
  echo "TERM $p"; kill -TERM $p
done
