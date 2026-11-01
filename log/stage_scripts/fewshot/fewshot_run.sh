#!/usr/bin/env bash
# Few-shot conditions (DESIGN §16): single-batch and multi-online (multi-private) with 3 discussion examples of the
# model's own, short (single-batch games) or long (multi-online games), other setups of the same domain.
# 8 GPUs: gemma generation -> Qwen generation -> judges (Llama x2, gpt-oss) + hidden states.
R=/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research
S=/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad
F=$S/fewshot; L=$F/run.log; cd $R
VPY=/diskthalys/ssd14ta/yharada/vllm-server/.venv/bin/python
GM=/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475
QM=/home/yharada/.cache/huggingface/hub/models--Qwen--Qwen3.8-27B/snapshots/1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0/
log() { echo "$(date +%m-%d\ %H:%M:%S) $*" >> $L; }
GPUS=(0 1 2 3 4 5 6 7); PORTS=(8000 8010 8020 8030 8040 8050 8070 8075)
up() { local name=$1; for i in $(seq 1 120); do n=0; for p in ${PORTS[@]}; do curl -s localhost:$p/v1/models | grep -q "\"$name\"" && n=$((n+1)); done; [ $n = 8 ] && break; sleep 10; done; log "$name servers up: $n/8"; }
stopall() { $S/main/kill_vllm_all.sh >> $L 2>&1; sleep 30; }
refresh() { for gd in log/fewshot/*/*/*/*/; do touch "$gd/.r" 2>/dev/null && rm -f "$gd/.r"; done; }   # NFS directory cache
exenv() { echo "{\"src\":\"log/main_$1\",\"cond\":\"$2\",\"n\":3}"; }   # model dir, source condition

# ---- gemma
stopall
for i in 0 1 2 3 4 5 6 7; do $F/gemma_one_32k.sh ${GPUS[$i]} ${PORTS[$i]} >> $L 2>&1; done
up gemma-4-31b
M=default,default_b,default_c,default_d,default_e,default_f,default_g,default_h
UGR_EXAMPLES=$(exenv gemma31b single-batch) .venv/bin/python scripts/run_queue.py --log-dir log/fewshot/gemma__ex-short --models $M --per-model 2 --port-base 40000 --conditions single-batch,multi-private --out-dir log/fewshot/gemma__ex-short/_queue > $F/q_gemma_short.out 2>&1 &
UGR_EXAMPLES=$(exenv gemma31b multi-private) .venv/bin/python scripts/run_queue.py --log-dir log/fewshot/gemma__ex-long --models $M --per-model 2 --port-base 40400 --conditions single-batch,multi-private --out-dir log/fewshot/gemma__ex-long/_queue > $F/q_gemma_long.out 2>&1 &
wait
log "gemma generation: short $(grep -c 'rc=0' log/fewshot/gemma__ex-short/_queue/progress.txt) ok, long $(grep -c 'rc=0' log/fewshot/gemma__ex-long/_queue/progress.txt) ok"
stopall
# ---- Qwen (pinned by setup: the same instance for every condition of a setup)
for i in 0 1 2 3 4 5 6 7; do $F/qwen_32k.sh ${GPUS[$i]} ${PORTS[$i]} >> $L 2>&1; done
up qwen3.8-27b
M=qwen,qwen_b,qwen_c,qwen_d,qwen_e,qwen_f,qwen_g,qwen_h
UGR_EXAMPLES=$(exenv qwen38 single-batch) .venv/bin/python scripts/run_queue.py --log-dir log/fewshot/qwen__ex-short --models $M --per-model 1 --port-base 41000 --pin-by-setup --conditions single-batch,multi-private --out-dir log/fewshot/qwen__ex-short/_queue > $F/q_qwen_short.out 2>&1 &
UGR_EXAMPLES=$(exenv qwen38 multi-private) .venv/bin/python scripts/run_queue.py --log-dir log/fewshot/qwen__ex-long --models $M --per-model 1 --port-base 41400 --pin-by-setup --conditions single-batch,multi-private --out-dir log/fewshot/qwen__ex-long/_queue > $F/q_qwen_long.out 2>&1 &
wait
log "qwen generation: short $(grep -c 'rc=0' log/fewshot/qwen__ex-short/_queue/progress.txt) ok, long $(grep -c 'rc=0' log/fewshot/qwen__ex-long/_queue/progress.txt) ok"
stopall
# ---- judges: Llama on GPUs 2,3 (8040) and 0,1 (8045), gpt-oss on GPU 4 (8060); hidden states on GPUs 5,6,7
$F/start_llama_23.sh >> $L 2>&1; $S/linejudge/start_llama_01.sh >> $L 2>&1; $S/llama/start_vllm_gptoss.sh >> $L 2>&1
DIRS="gemma__ex-short gemma__ex-long qwen__ex-short qwen__ex-long"
refresh
for d in $DIRS; do
  A=$S/annot_fewshot/$d; mkdir -p $A/games $A/out $A/raw
  cp $R/scripts/prompts/ANNOTATION_INSTRUCTIONS_v2.md $A/ANNOTATION_INSTRUCTIONS.md
  .venv/bin/python scripts/render_annotation.py --log-dir log/fewshot/$d --out-dir $A/games --stable-names --only-complete >> $F/render.out 2>&1
  log "rendered $d: $(ls $A/games | wc -l)"
done
for i in $(seq 1 90); do n=0; for p in 8040 8045; do curl -s localhost:$p/v1/models | grep -q llama && n=$((n+1)); done; curl -s localhost:8060/v1/models | grep -q gpt-oss && n=$((n+1)); [ $n = 3 ] && break; sleep 10; done
log "judges up: $n/3"
( for d in gemma__ex-short gemma__ex-long; do $S/pilot8/run_annot2.sh $S/annot_fewshot/$d http://localhost:8040/v1 llama-3.3-70b llama 12 12000; log "llama $d: $(ls $S/annot_fewshot/$d/out | grep -c '^llama__')"; done ) &
( for d in qwen__ex-short qwen__ex-long; do $S/pilot8/run_annot2.sh $S/annot_fewshot/$d http://localhost:8045/v1 llama-3.3-70b llama 12 12000; log "llama $d: $(ls $S/annot_fewshot/$d/out | grep -c '^llama__')"; done ) &
( for d in $DIRS; do $S/pilot8/run_annot2.sh $S/annot_fewshot/$d http://localhost:8060/v1 gpt-oss-120b gptoss 12 20000; log "gptoss $d: $(ls $S/annot_fewshot/$d/out | grep -c '^gptoss__')"; done ) &
xw() {  # hidden-state extraction worker on one GPU over every few-shot game
  local gpu=$1
  while true; do
    list=(); mp=""
    for d in $DIRS; do
      H=$R/hidden/fewshot/$d; mkdir -p $H/.claim
      for f in log/fewshot/$d/*/*/*/*.log; do gd=$(dirname "$f"); gid=$(basename $gd)
        [ -f $H/$gid.npz ] && continue; grep -q ",result," "$f" || continue
        mkdir $H/.claim/$gid 2>/dev/null || continue; list+=("$gd"); [ ${#list[@]} -ge 10 ] && break
      done
      if [ ${#list[@]} -gt 0 ]; then mp=$GM; [[ $d == qwen* ]] && mp=$QM; break; fi
    done
    [ ${#list[@]} -eq 0 ] && { log "hidden gpu$gpu: nothing left"; return; }
    CUDA_VISIBLE_DEVICES=$gpu $VPY scripts/extract_hidden.py --game-dir "${list[@]}" --model-path $mp --out-dir $H >> $F/hidden_gpu$gpu.out 2>&1
    for gd in "${list[@]}"; do gid=$(basename $gd); [ -f $H/$gid.npz ] || { rmdir $H/.claim/$gid 2>/dev/null; log "hidden: $gid missing"; }; done
  done
}
xw 5 & xw 6 & xw 7 &
wait
log "FEWSHOT DONE: games $(ls -d log/fewshot/*/*/*/*/ | wc -l), hidden $(ls hidden/fewshot/*/*.npz | wc -l)"
stopall
touch $F/done
