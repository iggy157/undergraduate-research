# Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 4.1 | 0.56 | 0.16 | 0.17 | 0.44 |
| single-batch | llama | 4.1 | 0.56 | 0.05 | 0.08 | 0.48 |
| multi-private | gptoss | 7.5 | 0.72 | 0.06 | 0.03 | 0.21 |
| multi-private | llama | 7.5 | 0.72 | 0.01 | 0.01 | 0.19 |

# Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.21 (n=300) |  |  |  | 1.33 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 2 | 1.24 (n=298) |  |  |  | 1.25 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 3 | 1.12 (n=298) |  |  |  | 1.22 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 4 | 0.44 (n=300) |  |  |  | 0.45 (n=300) |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1.29 (n=900) |  |  |  | 1.20 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 1.18 (n=734) |  |  |  | 1.10 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 3 | 1.05 (n=476) |  |  |  | 0.98 (n=886) |  |  |  |  |  |  |  |  |  |
| 1 | 4 | 0.95 (n=340) |  |  |  | 0.73 (n=816) |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 1.52 (n=600) |  |  |  | 1.40 (n=714) |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 1.14 (n=600) |  |  |  | 1.13 (n=714) |  |  |  |  |  |  |  |  |  |
| 2 | 3 | 1.10 (n=600) |  |  |  | 1.12 (n=714) |  |  |  |  |  |  |  |  |  |
| 2 | 4 | 0.88 (n=138) |  |  |  | 1.04 (n=714) |  |  |  |  |  |  |  |  |  |
| 3 | 1 | 1.41 (n=600) |  |  |  | 1.23 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 2 | 1.16 (n=600) |  |  |  | 1.09 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 3 | 1.03 (n=586) |  |  |  | 1.02 (n=598) |  |  |  |  |  |  |  |  |  |
| 3 | 4 | 0.79 (n=354) |  |  |  | 0.86 (n=600) |  |  |  |  |  |  |  |  |  |
