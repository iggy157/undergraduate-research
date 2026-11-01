#!/usr/bin/env bash
# after the tug run: the few-shot probes on GPUs 0-3 (the reservation still holds them)
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
until [ -f $S/fewshot/tug.done ]; do sleep 60; done
sleep 30
$S/fewshot/probe_fewshot_gpu.sh
