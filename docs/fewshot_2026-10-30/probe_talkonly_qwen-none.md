# Probes v3 (hidden/main_qwen38; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_qwen, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 2767 | words | 2767 | 0.310 | 0.667 (r 0.82) | 20 | +0.357 |
| multi-online | 4970 | words | 4970 | 0.253 | 0.404 (r 0.64) | 48 | +0.151 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.02 | 0.62 | 0.63 | 0.63 | 0.66 | 0.67 | 0.67 | 0.65 | 0.65 | 0.61 | 0.61 | 0.62 | 0.63 | 0.61 | 0.51 | 0.42 | 0.35 |
| multi-online | -0.01 | 0.25 | 0.29 | 0.31 | 0.33 | 0.34 | 0.34 | 0.34 | 0.34 | 0.38 | 0.38 | 0.38 | 0.40 | 0.39 | 0.38 | 0.37 | 0.36 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
