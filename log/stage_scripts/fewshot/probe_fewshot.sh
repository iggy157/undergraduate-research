#!/usr/bin/env bash
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
for d in gemma__ex-short gemma__ex-long qwen__ex-short qwen__ex-long; do
  CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=16 nice -n 15 $VPY scripts/probe_hidden2.py --log-dir log/fewshot/$d --hidden-dir hidden/fewshot/$d --annot-dir $S/annot_fewshot/$d --conditions single-batch,multi-private --out docs/fewshot_2026-10-30/probe_$d.md > $S/fewshot/probe_$d.out 2>&1 &
done
wait
touch $S/fewshot/probe.done
