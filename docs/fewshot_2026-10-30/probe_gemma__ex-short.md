# Probes v3 (hidden/fewshot/gemma__ex-short; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/gemma__ex-short, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3791 | words | 3791 | 0.482 | 0.897 (r 0.95) | 40 | +0.415 |
| single-batch | 3791 | content | 2818 | 0.207 | 0.378 (r 0.62) | 32 | +0.171 |
| single-batch | 3791 | has_content | 2818 | 0.761 | 0.889 | 48 | +0.129 |
| single-batch | 3791 | answers | 159 | 0.658 | 0.871 | 60 | +0.213 |
| multi-online | 4830 | words | 4830 | 0.422 | 0.867 (r 0.93) | 44 | +0.444 |
| multi-online | 4830 | content | 3892 | 0.093 | 0.310 (r 0.56) | 40 | +0.217 |
| multi-online | 4830 | has_content | 3892 | 0.662 | 0.885 | 44 | +0.222 |
| multi-online | 4830 | answers | 220 | 0.613 | 0.745 | 44 | +0.132 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.82 | 0.83 | 0.83 | 0.85 | 0.86 | 0.87 | 0.88 | 0.88 | 0.89 | 0.90 | 0.89 | 0.90 | 0.89 | 0.90 | 0.89 |
| multi-online | -0.00 | 0.82 | 0.80 | 0.80 | 0.81 | 0.83 | 0.82 | 0.84 | 0.84 | 0.85 | 0.87 | 0.87 | 0.87 | 0.86 | 0.85 | 0.83 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
| single-batch (layer 40) | 0.95 | 0.62 |
| multi-online (layer 44) | 0.47 | 0.93 |
