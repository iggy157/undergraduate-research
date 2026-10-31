# Probes v3 (hidden/fewshot/qwen__ex-short; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/qwen__ex-short, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3205 | words | 3205 | 0.268 | 0.597 (r 0.77) | 20 | +0.329 |
| multi-online | 4820 | words | 4820 | 0.245 | 0.528 (r 0.73) | 48 | +0.283 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.01 | 0.57 | 0.57 | 0.57 | 0.59 | 0.60 | 0.59 | 0.58 | 0.59 | 0.58 | 0.57 | 0.57 | 0.60 | 0.57 | 0.52 | 0.47 | 0.41 |
| multi-online | -0.01 | 0.38 | 0.40 | 0.42 | 0.43 | 0.43 | 0.42 | 0.43 | 0.46 | 0.50 | 0.50 | 0.50 | 0.53 | 0.51 | 0.50 | 0.48 | 0.45 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
