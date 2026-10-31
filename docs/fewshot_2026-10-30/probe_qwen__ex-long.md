# Probes v3 (hidden/fewshot/qwen__ex-long; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/qwen__ex-long, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3552 | words | 3552 | 0.296 | 0.759 (r 0.87) | 20 | +0.463 |
| single-batch | 3552 | content | 3365 | 0.144 | 0.462 (r 0.68) | 52 | +0.318 |
| single-batch | 3552 | has_content | 3365 | 0.791 | 0.925 | 36 | +0.133 |
| single-batch | 3552 | answers | 90 | – | – | – | – |
| multi-online | 4820 | words | 4820 | 0.418 | 0.534 (r 0.73) | 48 | +0.116 |
| multi-online | 4820 | content | 4811 | 0.249 | 0.415 (r 0.64) | 52 | +0.167 |
| multi-online | 4820 | has_content | 4811 | 0.814 | 0.887 | 52 | +0.073 |
| multi-online | 4820 | answers | 201 | 0.449 | 0.772 | 56 | +0.323 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.02 | 0.73 | 0.73 | 0.73 | 0.75 | 0.76 | 0.76 | 0.76 | 0.75 | 0.75 | 0.74 | 0.75 | 0.75 | 0.73 | 0.69 | 0.67 | 0.65 |
| multi-online | -0.01 | 0.43 | 0.45 | 0.46 | 0.47 | 0.47 | 0.47 | 0.47 | 0.48 | 0.50 | 0.50 | 0.51 | 0.53 | 0.51 | 0.50 | 0.49 | 0.46 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
| single-batch (layer 20) | 0.88 | 0.40 |
| multi-online (layer 48) | 0.40 | 0.73 |
