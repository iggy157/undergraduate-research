#!/usr/bin/env bash
cd /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
CUDA_VISIBLE_DEVICES=0 $VPY scripts/probe_hidden2.py --log-dir log/main_qwen38 --hidden-dir hidden/main_qwen38 --annot-dir $S/annot_qwen --out docs/main_qwen38/probe_summary_v3.md > $S/probe3/qwen.out 2>&1 &
CUDA_VISIBLE_DEVICES=1 $VPY scripts/probe_hidden2.py --log-dir log/main_gemma31b --hidden-dir hidden/main_gemma31b --annot-dir $S/annot_main --out docs/main_gemma31b/probe_summary_v3.md > $S/probe3/gemma.out 2>&1 &
wait
touch $S/probe3/done
