#!/usr/bin/env bash
# line judging: Llama on everything, gpt-oss on an agreement subset + the steering lines
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
cd $R; O=log/line_judge; mkdir -p $O
ST="log/steering_2026-10-30/pilot_gemma_s0.jsonl log/steering_2026-10-30/pilot_gemma_s1.jsonl log/steering_2026-10-30/pilot_gemma_L20.jsonl log/steering_2026-10-30/pilot_gemma_L52.jsonl"
.venv/bin/python scripts/line_judge.py --log-dir log/main_gemma31b --swap log/goal_swap/gemma__multi-private.jsonl log/goal_swap/gemma__multi-private-stepped.jsonl --steer $ST --base-url http://localhost:8040/v1 --model llama-3.3-70b --rater llama --out $O/llama__gemma.jsonl --threads 48 > $S/linejudge/judge_llama_gemma.out 2>&1 &
.venv/bin/python scripts/line_judge.py --log-dir log/main_qwen38 --swap log/goal_swap/qwen__multi-private.jsonl log/goal_swap/qwen__multi-private-stepped.jsonl --base-url http://localhost:8040/v1 --model llama-3.3-70b --rater llama --out $O/llama__qwen.jsonl --threads 48 > $S/linejudge/judge_llama_qwen.out 2>&1 &
.venv/bin/python scripts/line_judge.py --log-dir log/main_gemma31b --swap log/goal_swap/gemma__multi-private.jsonl log/goal_swap/gemma__multi-private-stepped.jsonl --steer $ST --only-sample --every 5 --base-url http://localhost:8060/v1 --model gpt-oss-120b --rater gptoss --max-tokens 2000 --out $O/gptoss__gemma.jsonl --threads 24 > $S/linejudge/judge_gptoss_gemma.out 2>&1 &
.venv/bin/python scripts/line_judge.py --log-dir log/main_qwen38 --swap log/goal_swap/qwen__multi-private.jsonl log/goal_swap/qwen__multi-private-stepped.jsonl --only-sample --every 5 --base-url http://localhost:8060/v1 --model gpt-oss-120b --rater gptoss --max-tokens 2000 --out $O/gptoss__qwen.jsonl --threads 24 > $S/linejudge/judge_gptoss_qwen.out 2>&1 &
wait
echo "$(date +%H:%M:%S) JUDGE DONE" >> $S/linejudge/judge.log
