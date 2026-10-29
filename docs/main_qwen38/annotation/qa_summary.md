# Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.6 | 0.52 | 0.29 | 0.40 | 0.61 |
| single-batch | llama | 3.6 | 0.52 | 0.21 | 0.35 | 0.65 |
| single-batch-stepped | gptoss | 4.3 | 0.52 | 0.32 | 0.43 | 0.54 |
| single-batch-stepped | llama | 4.3 | 0.52 | 0.20 | 0.34 | 0.58 |
| single-online | gptoss | 4.8 | 0.53 | 0.25 | 0.19 | 0.44 |
| single-online | llama | 4.8 | 0.53 | 0.08 | 0.13 | 0.42 |
| multi-public | gptoss | 5.6 | 0.55 | 0.11 | 0.06 | 0.36 |
| multi-public | llama | 5.6 | 0.55 | 0.04 | 0.03 | 0.36 |
| multi-private | gptoss | 6.4 | 0.47 | 0.07 | 0.04 | 0.37 |
| multi-private | llama | 6.4 | 0.47 | 0.02 | 0.01 | 0.34 |
| multi-private-stepped | gptoss | 3.4 | 0.35 | 0.25 | 0.39 | 0.61 |
| multi-private-stepped | llama | 3.4 | 0.35 | 0.15 | 0.31 | 0.63 |
| multi-public-stepped | gptoss | 4.0 | 0.46 | 0.24 | 0.32 | 0.49 |
| multi-public-stepped | llama | 4.0 | 0.46 | 0.15 | 0.24 | 0.53 |
| multi-private-stepped-process | gptoss | 4.3 | 0.35 | 0.19 | 0.24 | 0.50 |
| multi-private-stepped-process | llama | 4.3 | 0.35 | 0.11 | 0.21 | 0.53 |

# Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 0.95 (n=300) | 0.97 (n=300) | 1.16 (n=300) | 1.22 (n=300) | 1.23 (n=300) |  |  | 1.05 (n=300) | 1.05 (n=300) | 1.34 (n=300) |
| 0 | 2 | 1.06 (n=300) | 1.05 (n=300) | 1.17 (n=300) | 1.30 (n=300) | 1.31 (n=300) |  |  | 1.09 (n=300) | 1.08 (n=300) | 1.28 (n=300) |
| 0 | 3 | 0.96 (n=290) | 0.98 (n=288) | 1.08 (n=300) | 1.21 (n=300) | 1.26 (n=300) |  |  | 1.04 (n=300) | 1.01 (n=296) | 1.23 (n=300) |
| 0 | 4 | 0.17 (n=222) | 0.33 (n=224) | 0.69 (n=290) | 0.89 (n=300) | 0.87 (n=292) |  |  | 0.52 (n=266) | 0.52 (n=232) | 0.81 (n=300) |
| 1 | 1 | 1.18 (n=898) | 1.18 (n=900) | 1.21 (n=900) | 1.33 (n=900) | 1.40 (n=900) |  |  | 1.19 (n=900) | 1.24 (n=898) | 1.30 (n=900) |
| 1 | 2 | 1.06 (n=898) | 1.05 (n=900) | 1.04 (n=900) | 1.18 (n=900) | 1.23 (n=900) |  |  | 1.11 (n=900) | 1.09 (n=898) | 1.21 (n=900) |
| 1 | 3 | 1.06 (n=898) | 1.09 (n=900) | 0.99 (n=890) | 0.95 (n=892) | 1.03 (n=886) |  |  | 1.09 (n=900) | 1.12 (n=898) | 1.19 (n=900) |
| 1 | 4 | 0.72 (n=614) | 0.84 (n=660) | 0.75 (n=878) | 0.70 (n=890) | 0.73 (n=870) |  |  | 0.87 (n=796) | 0.83 (n=724) | 0.93 (n=820) |
| 2 | 1 | 1.32 (n=642) | 1.29 (n=630) | 0.96 (n=636) | 1.45 (n=618) | 1.47 (n=698) |  |  | 1.29 (n=700) | 1.38 (n=624) | 1.38 (n=724) |
| 2 | 2 | 1.06 (n=642) | 1.08 (n=630) | 1.00 (n=636) | 1.16 (n=618) | 1.27 (n=698) |  |  | 1.15 (n=700) | 1.14 (n=624) | 1.21 (n=724) |
| 2 | 3 | 1.15 (n=642) | 1.19 (n=630) | 1.00 (n=636) | 1.03 (n=618) | 1.17 (n=698) |  |  | 1.12 (n=700) | 1.23 (n=624) | 1.26 (n=724) |
| 2 | 4 | 1.00 (n=445) | 1.07 (n=454) | 0.94 (n=632) | 0.85 (n=618) | 1.02 (n=694) |  |  | 0.95 (n=604) | 1.08 (n=554) | 1.05 (n=643) |
| 3 | 1 | 1.24 (n=590) | 1.24 (n=600) | 1.02 (n=600) | 1.05 (n=600) | 1.31 (n=600) |  |  | 1.25 (n=606) | 1.28 (n=600) | 1.39 (n=636) |
| 3 | 2 | 1.04 (n=590) | 1.09 (n=600) | 0.99 (n=600) | 0.99 (n=600) | 1.07 (n=600) |  |  | 1.06 (n=606) | 1.13 (n=598) | 1.13 (n=636) |
| 3 | 3 | 1.09 (n=590) | 1.10 (n=600) | 0.85 (n=600) | 0.77 (n=600) | 0.90 (n=600) |  |  | 0.96 (n=606) | 1.02 (n=570) | 1.19 (n=636) |
| 3 | 4 | 0.66 (n=352) | 0.70 (n=422) | 0.93 (n=600) | 0.79 (n=600) | 0.84 (n=600) |  |  | 0.83 (n=506) | 0.68 (n=480) | 1.01 (n=556) |
