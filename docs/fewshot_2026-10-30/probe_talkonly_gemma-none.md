# Probes v3 (hidden/main_gemma31b; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_main, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 2656 | words | 2656 | 0.430 | 0.734 (r 0.86) | 40 | +0.304 |
| multi-online | 4719 | words | 4719 | 0.218 | 0.489 (r 0.70) | 40 | +0.271 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.61 | 0.63 | 0.65 | 0.66 | 0.66 | 0.68 | 0.70 | 0.71 | 0.73 | 0.73 | 0.71 | 0.70 | 0.69 | 0.68 | 0.64 |
| multi-online | -0.00 | 0.36 | 0.36 | 0.37 | 0.38 | 0.39 | 0.40 | 0.44 | 0.46 | 0.48 | 0.49 | 0.49 | 0.49 | 0.48 | 0.47 | 0.46 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
