# Probes v3 (hidden/fewshot/gemma__ex-long; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/gemma__ex-long, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 1861 | words | 1861 | 0.432 | 0.708 (r 0.84) | 36 | +0.276 |
| multi-online | 4600 | words | 4600 | 0.180 | 0.416 (r 0.65) | 48 | +0.237 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.59 | 0.61 | 0.62 | 0.64 | 0.64 | 0.66 | 0.68 | 0.70 | 0.71 | 0.71 | 0.69 | 0.68 | 0.67 | 0.66 | 0.62 |
| multi-online | -0.00 | 0.32 | 0.30 | 0.31 | 0.32 | 0.32 | 0.32 | 0.36 | 0.37 | 0.39 | 0.41 | 0.42 | 0.42 | 0.41 | 0.40 | 0.37 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
