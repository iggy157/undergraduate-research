# Question -> answer rate (derived from resp_to / resp_type)

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee |
|---|---|---|---|---|---|
| single-batch | gptoss | 3.8 | 0.50 | 0.29 | 0.24 |
| single-batch | llama | 3.8 | 0.50 | 0.18 | 0.18 |
| single-batch | opus | 3.8 | 0.50 | 0.53 | 0.53 |
| single-batch | sonnet | 3.8 | 0.50 | 0.56 | 0.65 |
| single-batch-stepped | gptoss | 3.7 | 0.42 | 0.24 | 0.36 |
| single-batch-stepped | llama | 3.7 | 0.42 | 0.21 | 0.21 |
| single-batch-stepped | opus | 3.7 | 0.42 | 0.45 | 0.57 |
| single-batch-stepped | sonnet | 3.7 | 0.42 | 0.45 | 0.57 |
| single-online | gptoss | 6.9 | 0.37 | 0.29 | 0.35 |
| single-online | llama | 6.9 | 0.37 | 0.08 | 0.09 |
| single-online | opus | 6.9 | 0.37 | 0.56 | 0.61 |
| single-online | sonnet | 6.9 | 0.37 | 0.53 | 0.57 |
| multi-public | gptoss | 6.2 | 0.46 | 0.11 | 0.00 |
| multi-public | llama | 6.2 | 0.46 | 0.00 | 0.00 |
| multi-public | opus | 6.2 | 0.46 | 0.50 | 0.15 |
| multi-public | sonnet | 6.2 | 0.46 | 0.46 | 0.15 |
| multi-private | gptoss | 9.4 | 0.65 | 0.08 | 0.04 |
| multi-private | llama | 9.4 | 0.65 | 0.02 | 0.04 |
| multi-private | opus | 9.4 | 0.65 | 0.26 | 0.13 |
| multi-private | sonnet | 9.4 | 0.65 | 0.28 | 0.07 |
| single-batch-process | gptoss | 5.2 | 0.64 | 0.26 | 0.23 |
| single-batch-process | llama | 5.2 | 0.64 | 0.17 | 0.23 |
| single-batch-process | opus | 5.2 | 0.64 | 0.51 | 0.63 |
| single-batch-process | sonnet | 5.2 | 0.64 | 0.57 | 0.70 |
| multi-private-process | gptoss | 7.1 | 0.72 | 0.03 | 0.00 |
| multi-private-process | llama | 7.1 | 0.72 | 0.00 | 0.00 |
| multi-private-process | opus | 7.1 | 0.72 | 0.27 | 0.04 |
| multi-private-process | sonnet | 7.1 | 0.72 | 0.28 | 0.04 |

# Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process |
|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 0.72 (n=60) | 0.65 (n=60) | 1.08 (n=60) | 1.22 (n=60) | 0.87 (n=60) | 1.07 (n=60) | 1.13 (n=60) |
| 0 | 2 | 0.98 (n=52) | 0.98 (n=48) | 1.07 (n=60) | 1.22 (n=60) | 0.97 (n=60) | 0.83 (n=60) | 1.10 (n=60) |
| 0 | 3 | 0.78 (n=36) | 0.91 (n=32) | 0.80 (n=60) | 0.93 (n=60) | 0.78 (n=60) | 0.60 (n=60) | 0.92 (n=60) |
| 0 | 4 |  | 0.62 (n=8) | 0.23 (n=60) | 0.22 (n=60) | 0.20 (n=60) | 0.25 (n=28) | 0.48 (n=60) |
| 1 | 1 | 1.29 (n=180) | 1.37 (n=180) | 1.36 (n=180) | 1.34 (n=180) | 1.04 (n=180) | 1.22 (n=180) | 1.19 (n=180) |
| 1 | 2 | 1.00 (n=80) | 0.96 (n=80) | 0.80 (n=176) | 0.99 (n=176) | 0.98 (n=180) | 0.95 (n=160) | 0.98 (n=180) |
| 1 | 3 | 0.97 (n=80) | 0.97 (n=80) | 0.76 (n=156) | 0.66 (n=176) | 0.89 (n=180) | 0.99 (n=100) | 0.73 (n=180) |
| 1 | 4 | 0.60 (n=48) | 0.62 (n=40) | 0.55 (n=128) | 0.41 (n=160) | 0.58 (n=160) | 0.75 (n=60) | 0.50 (n=180) |
| 2 | 1 | 1.74 (n=120) | 1.86 (n=120) | 1.80 (n=120) | 1.78 (n=120) | 1.45 (n=160) | 1.62 (n=120) | 1.40 (n=144) |
| 2 | 2 | 0.94 (n=120) | 0.97 (n=120) | 1.04 (n=120) | 0.97 (n=120) | 1.09 (n=160) | 1.00 (n=120) | 0.90 (n=144) |
| 2 | 3 | 0.82 (n=120) | 0.97 (n=100) | 0.98 (n=120) | 0.81 (n=120) | 0.95 (n=160) | 0.83 (n=120) | 0.89 (n=144) |
| 2 | 4 | 0.42 (n=36) | 0.58 (n=76) | 0.77 (n=120) | 0.60 (n=120) | 0.72 (n=160) | 0.15 (n=20) | 0.67 (n=144) |
| 3 | 1 | 1.26 (n=120) | 1.37 (n=120) | 1.18 (n=120) | 0.97 (n=120) | 1.28 (n=120) | 1.39 (n=120) | 1.39 (n=120) |
| 3 | 2 | 0.88 (n=120) | 1.01 (n=100) | 0.82 (n=100) | 0.53 (n=96) | 0.68 (n=120) | 1.09 (n=120) | 0.79 (n=120) |
| 3 | 3 | 0.82 (n=92) | 0.72 (n=100) | 0.60 (n=100) | 0.28 (n=64) | 0.67 (n=120) | 0.75 (n=120) | 0.65 (n=120) |
| 3 | 4 | 0.17 (n=36) | 0.10 (n=20) | 0.57 (n=100) | 0.03 (n=40) | 0.27 (n=120) | 0.48 (n=48) | 0.67 (n=120) |
