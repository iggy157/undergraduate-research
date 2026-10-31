# Probes v3 (hidden/fewshot/qwen__ex-short; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/qwen__ex-short, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3432 | words | 3432 | 0.259 | 0.767 (r 0.88) | 52 | +0.508 |
| single-batch | 3432 | content | 3205 | 0.058 | 0.275 (r 0.52) | 52 | +0.216 |
| single-batch | 3432 | has_content | 3205 | 0.710 | 0.865 | 52 | +0.155 |
| single-batch | 3432 | answers | 126 | 0.682 | 0.865 | 8 | +0.184 |
| multi-online | 4896 | words | 4896 | 0.198 | 0.594 (r 0.77) | 52 | +0.396 |
| multi-online | 4896 | content | 4820 | 0.156 | 0.336 (r 0.58) | 52 | +0.181 |
| multi-online | 4896 | has_content | 4820 | 0.802 | 0.884 | 48 | +0.081 |
| multi-online | 4896 | answers | 204 | 0.532 | 0.721 | 52 | +0.189 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.71 | 0.72 | 0.72 | 0.74 | 0.75 | 0.74 | 0.74 | 0.75 | 0.75 | 0.75 | 0.76 | 0.77 | 0.77 | 0.74 | 0.73 | 0.70 |
| multi-online | -0.00 | 0.36 | 0.41 | 0.46 | 0.47 | 0.48 | 0.49 | 0.47 | 0.50 | 0.55 | 0.54 | 0.55 | 0.58 | 0.59 | 0.58 | 0.57 | 0.53 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
| single-batch (layer 52) | 0.88 | 0.56 |
| multi-online (layer 52) | 0.55 | 0.77 |
