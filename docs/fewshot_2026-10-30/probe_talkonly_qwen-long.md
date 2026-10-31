# Probes v3 (hidden/fewshot/qwen__ex-long; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/qwen__ex-long, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3365 | words | 3365 | 0.348 | 0.669 (r 0.82) | 20 | +0.321 |
| multi-online | 4811 | words | 4811 | 0.445 | 0.545 (r 0.74) | 48 | +0.100 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.03 | 0.64 | 0.65 | 0.64 | 0.66 | 0.67 | 0.66 | 0.64 | 0.63 | 0.62 | 0.61 | 0.61 | 0.61 | 0.56 | 0.48 | 0.44 | 0.40 |
| multi-online | -0.01 | 0.46 | 0.47 | 0.49 | 0.49 | 0.49 | 0.48 | 0.49 | 0.50 | 0.51 | 0.51 | 0.52 | 0.54 | 0.53 | 0.52 | 0.50 | 0.48 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
