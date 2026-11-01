#!/usr/bin/env bash
me=$$; par=$PPID
for p in $(pgrep -f "orchestrate_qwen.sh|orchestrate_mps.sh|run_annot.sh|annotate_llm.py|extract_hidden.py"); do
  [ "$p" = "$me" ] || [ "$p" = "$par" ] && continue
  c=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null); case "$c" in *shell-snapshots*|*"bash -c "*|*kill_phase2*) continue;; esac
  echo "TERM $p ${c:0:60}"; kill -TERM $p
done
