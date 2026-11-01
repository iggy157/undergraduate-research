# Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.6 | 0.59 | 0.29 | 0.37 | 0.58 |
| single-batch | llama | 3.6 | 0.59 | 0.16 | 0.23 | 0.63 |
| multi-private | gptoss | 3.2 | 0.80 | 0.14 | 0.10 | 0.40 |
| multi-private | llama | 3.2 | 0.80 | 0.03 | 0.04 | 0.38 |

# Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.07 (n=300) |  |  |  | 1.25 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 2 | 1.21 (n=300) |  |  |  | 1.26 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 3 | 0.94 (n=300) |  |  |  | 1.06 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 4 | 0.25 (n=270) |  |  |  | 0.59 (n=290) |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1.22 (n=900) |  |  |  | 1.26 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 1.11 (n=900) |  |  |  | 1.25 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 3 | 1.15 (n=900) |  |  |  | 1.21 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 4 | 0.99 (n=736) |  |  |  | 0.91 (n=816) |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 1.25 (n=642) |  |  |  | 1.49 (n=674) |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 1.10 (n=642) |  |  |  | 1.25 (n=674) |  |  |  |  |  |  |  |  |  |
| 2 | 3 | 1.18 (n=642) |  |  |  | 1.19 (n=674) |  |  |  |  |  |  |  |  |  |
| 2 | 4 | 1.08 (n=416) |  |  |  | 1.05 (n=616) |  |  |  |  |  |  |  |  |  |
| 3 | 1 | 1.34 (n=590) |  |  |  | 1.33 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 2 | 1.13 (n=590) |  |  |  | 1.20 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 3 | 1.17 (n=590) |  |  |  | 1.13 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 4 | 1.07 (n=470) |  |  |  | 1.01 (n=600) |  |  |  |  |  |  |  |  |  |
