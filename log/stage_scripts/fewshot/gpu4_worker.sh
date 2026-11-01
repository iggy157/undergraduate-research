#!/usr/bin/env bash
# when fewshot_run.sh has finished (judges done, its servers stopped): one more extraction worker on GPU 4
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
F=$S/fewshot
until [ -f $F/done ]; do sleep 60; done
sleep 60
echo "$(date +%m-%d\ %H:%M:%S) extra hidden worker on GPU 4" >> $F/run.log
$F/xw2.sh 4
