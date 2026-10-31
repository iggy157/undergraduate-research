# Probes v3 (hidden/fewshot/gemma__ex-long; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/gemma__ex-long, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 2395 | words | 2395 | 0.541 | 0.899 (r 0.95) | 60 | +0.358 |
| single-batch | 2395 | content | 1861 | 0.185 | 0.343 (r 0.59) | 40 | +0.159 |
| single-batch | 2395 | has_content | 1861 | 0.796 | 0.903 | 36 | +0.107 |
| single-batch | 2395 | answers | 85 | – | – | – | – |
| multi-online | 4925 | words | 4925 | 0.498 | 0.813 (r 0.90) | 40 | +0.316 |
| multi-online | 4925 | content | 4600 | 0.114 | 0.351 (r 0.59) | 44 | +0.237 |
| multi-online | 4925 | has_content | 4600 | 0.732 | 0.906 | 40 | +0.174 |
| multi-online | 4925 | answers | 344 | 0.664 | 0.793 | 40 | +0.129 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.81 | 0.84 | 0.84 | 0.86 | 0.87 | 0.87 | 0.88 | 0.89 | 0.89 | 0.90 | 0.89 | 0.89 | 0.89 | 0.89 | 0.90 |
| multi-online | -0.00 | 0.74 | 0.73 | 0.74 | 0.75 | 0.77 | 0.74 | 0.78 | 0.77 | 0.79 | 0.81 | 0.81 | 0.80 | 0.78 | 0.76 | 0.71 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
| single-batch (layer 60) | 0.95 | 0.27 |
| multi-online (layer 40) | 0.49 | 0.90 |
