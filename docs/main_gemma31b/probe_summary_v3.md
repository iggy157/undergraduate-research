# Probes v3 (hidden/main_gemma31b; annotations /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_main, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

## A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3455 | words | 3455 | 0.385 | 0.866 (r 0.93) | 40 | +0.481 |
| single-batch | 3455 | content | 2656 | 0.189 | 0.390 (r 0.62) | 36 | +0.201 |
| single-batch | 3455 | has_content | 2656 | 0.733 | 0.881 | 44 | +0.147 |
| single-batch | 3455 | answers | 135 | 0.638 | 0.841 | 32 | +0.203 |
| single-batch-stepped | 4118 | words | 4118 | 0.396 | 0.869 (r 0.93) | 40 | +0.473 |
| single-batch-stepped | 4118 | content | 3152 | 0.233 | 0.418 (r 0.65) | 32 | +0.185 |
| single-batch-stepped | 4118 | has_content | 3152 | 0.776 | 0.902 | 40 | +0.125 |
| single-batch-stepped | 4118 | answers | 166 | 0.612 | 0.823 | 40 | +0.211 |
| single-online | 4670 | words | 4670 | 0.313 | 0.800 (r 0.89) | 44 | +0.487 |
| single-online | 4670 | content | 4219 | 0.229 | 0.476 (r 0.69) | 48 | +0.247 |
| single-online | 4670 | has_content | 4219 | 0.783 | 0.924 | 48 | +0.141 |
| single-online | 4670 | answers | 153 | 0.738 | 0.911 | 52 | +0.172 |
| multi-batch | 4998 | words | 4998 | 0.349 | 0.819 (r 0.91) | 48 | +0.471 |
| multi-batch | 4998 | content | 4270 | 0.068 | 0.297 (r 0.55) | 40 | +0.229 |
| multi-batch | 4998 | has_content | 4270 | 0.693 | 0.880 | 40 | +0.186 |
| multi-batch | 4998 | answers | 131 | 0.721 | 0.851 | 40 | +0.130 |
| multi-online | 4982 | words | 4982 | 0.296 | 0.729 (r 0.85) | 40 | +0.433 |
| multi-online | 4982 | content | 4719 | 0.167 | 0.403 (r 0.63) | 40 | +0.236 |
| multi-online | 4982 | has_content | 4719 | 0.770 | 0.920 | 40 | +0.150 |
| multi-online | 4982 | answers | 374 | 0.694 | 0.840 | 44 | +0.146 |

## B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.77 | 0.78 | 0.78 | 0.80 | 0.81 | 0.82 | 0.84 | 0.85 | 0.86 | 0.87 | 0.86 | 0.86 | 0.85 | 0.85 | 0.84 |
| single-batch-stepped | -0.00 | 0.79 | 0.79 | 0.80 | 0.81 | 0.82 | 0.83 | 0.85 | 0.86 | 0.86 | 0.87 | 0.87 | 0.86 | 0.86 | 0.86 | 0.85 |
| single-online | -0.01 | 0.70 | 0.67 | 0.67 | 0.69 | 0.70 | 0.69 | 0.72 | 0.74 | 0.76 | 0.80 | 0.80 | 0.80 | 0.79 | 0.79 | 0.78 |
| multi-batch | -0.01 | 0.71 | 0.72 | 0.73 | 0.73 | 0.75 | 0.77 | 0.78 | 0.79 | 0.80 | 0.82 | 0.82 | 0.82 | 0.81 | 0.81 | 0.80 |
| multi-online | -0.00 | 0.68 | 0.65 | 0.64 | 0.67 | 0.69 | 0.67 | 0.70 | 0.70 | 0.70 | 0.73 | 0.73 | 0.71 | 0.70 | 0.67 | 0.63 |

## C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | single-batch-stepped | single-online | multi-batch | multi-online |
|---|---|---|---|---|---|
| single-batch (layer 40) | 0.93 | 0.93 | 0.54 | 0.86 | 0.34 |
| single-batch-stepped (layer 40) | 0.93 | 0.93 | 0.62 | 0.87 | 0.38 |
| single-online (layer 44) | 0.55 | 0.53 | 0.89 | 0.54 | 0.72 |
| multi-batch (layer 48) | 0.88 | 0.88 | 0.79 | 0.91 | 0.58 |
| multi-online (layer 40) | 0.57 | 0.58 | 0.79 | 0.61 | 0.85 |
