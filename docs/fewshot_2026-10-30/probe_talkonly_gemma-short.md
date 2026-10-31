# Probes v3 (hidden/fewshot/gemma__ex-short; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/gemma__ex-short, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 2818 | words | 2818 | 0.452 | 0.736 (r 0.86) | 36 | +0.284 |
| multi-online | 3892 | words | 3892 | 0.277 | 0.568 (r 0.75) | 40 | +0.291 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.01 | 0.64 | 0.63 | 0.65 | 0.67 | 0.69 | 0.69 | 0.72 | 0.73 | 0.74 | 0.73 | 0.72 | 0.72 | 0.71 | 0.71 | 0.68 |
| multi-online | -0.00 | 0.45 | 0.43 | 0.44 | 0.45 | 0.46 | 0.47 | 0.50 | 0.52 | 0.55 | 0.57 | 0.56 | 0.55 | 0.54 | 0.53 | 0.49 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
