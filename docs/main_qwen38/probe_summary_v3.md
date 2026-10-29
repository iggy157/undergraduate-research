# Probes v3 (hidden/main_qwen38; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_qwen, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3100 | words | 3100 | 0.376 | 0.802 (r 0.90) | 20 | +0.426 |
| single-batch | 3100 | content | 2767 | 0.091 | 0.318 (r 0.56) | 48 | +0.227 |
| single-batch | 3100 | has_content | 2767 | 0.763 | 0.861 | 48 | +0.099 |
| single-batch | 3100 | answers | 103 | 0.860 | 0.899 | 52 | +0.039 |
| single-batch-stepped | 4854 | words | 4854 | 0.325 | 0.785 (r 0.89) | 20 | +0.460 |
| single-batch-stepped | 4854 | content | 4519 | 0.104 | 0.401 (r 0.63) | 52 | +0.297 |
| single-batch-stepped | 4854 | has_content | 4519 | 0.760 | 0.896 | 52 | +0.136 |
| single-batch-stepped | 4854 | answers | 196 | 0.820 | 0.912 | 52 | +0.092 |
| single-online | 4872 | words | 4872 | 0.193 | 0.436 (r 0.66) | 48 | +0.242 |
| single-online | 4872 | content | 4850 | 0.031 | 0.223 (r 0.47) | 52 | +0.192 |
| single-online | 4872 | has_content | 4850 | 0.609 | 0.811 | 52 | +0.202 |
| single-online | 4872 | answers | 195 | 0.714 | 0.751 | 52 | +0.037 |
| multi-batch | 5012 | words | 5012 | 0.307 | 0.741 (r 0.86) | 20 | +0.434 |
| multi-batch | 5012 | content | 4845 | 0.079 | 0.357 (r 0.60) | 48 | +0.277 |
| multi-batch | 5012 | has_content | 4845 | 0.705 | 0.876 | 48 | +0.170 |
| multi-batch | 5012 | answers | 106 | 0.702 | 0.880 | 48 | +0.177 |
| multi-online | 4996 | words | 4996 | 0.243 | 0.437 (r 0.66) | 52 | +0.194 |
| multi-online | 4996 | content | 4970 | 0.130 | 0.316 (r 0.56) | 52 | +0.186 |
| multi-online | 4996 | has_content | 4970 | 0.735 | 0.848 | 48 | +0.114 |
| multi-online | 4996 | answers | 235 | 0.504 | 0.707 | 60 | +0.203 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.01 | 0.74 | 0.77 | 0.78 | 0.80 | 0.80 | 0.80 | 0.79 | 0.79 | 0.77 | 0.78 | 0.79 | 0.80 | 0.79 | 0.74 | 0.71 | 0.68 |
| single-batch-stepped | -0.01 | 0.73 | 0.74 | 0.74 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.76 | 0.73 | 0.71 |
| single-online | -0.01 | 0.27 | 0.30 | 0.33 | 0.33 | 0.35 | 0.33 | 0.35 | 0.37 | 0.42 | 0.41 | 0.42 | 0.44 | 0.43 | 0.42 | 0.42 | 0.43 |
| multi-batch | -0.02 | 0.71 | 0.71 | 0.73 | 0.74 | 0.74 | 0.73 | 0.73 | 0.73 | 0.73 | 0.72 | 0.72 | 0.74 | 0.73 | 0.68 | 0.65 | 0.60 |
| multi-online | -0.01 | 0.23 | 0.29 | 0.32 | 0.34 | 0.35 | 0.35 | 0.35 | 0.37 | 0.40 | 0.39 | 0.40 | 0.43 | 0.44 | 0.42 | 0.41 | 0.39 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | single-batch-stepped | single-online | multi-batch | multi-online |
|---|---|---|---|---|---|
| single-batch (layer 20) | 0.89 | 0.87 | -0.19 | 0.78 | -0.12 |
| single-batch-stepped (layer 20) | 0.90 | 0.89 | -0.08 | 0.81 | -0.09 |
| single-online (layer 48) | 0.61 | 0.61 | 0.66 | 0.55 | 0.57 |
| multi-batch (layer 20) | 0.88 | 0.87 | -0.04 | 0.86 | -0.08 |
| multi-online (layer 52) | 0.67 | 0.67 | 0.52 | 0.60 | 0.66 |
