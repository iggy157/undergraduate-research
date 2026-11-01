# Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.8 | 0.54 | 0.33 | 0.36 | 0.60 |
| single-batch | llama | 3.8 | 0.54 | 0.18 | 0.25 | 0.66 |
| multi-private | gptoss | 5.8 | 0.54 | 0.11 | 0.08 | 0.32 |
| multi-private | llama | 5.8 | 0.54 | 0.04 | 0.04 | 0.31 |

# Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.02 (n=300) |  |  |  | 1.05 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 2 | 1.04 (n=274) |  |  |  | 1.09 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 3 | 0.90 (n=134) |  |  |  | 0.87 (n=296) |  |  |  |  |  |  |  |  |  |
| 0 | 4 | 0.50 (n=2) |  |  |  | 0.52 (n=268) |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1.38 (n=900) |  |  |  | 1.38 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 1.12 (n=360) |  |  |  | 1.07 (n=416) |  |  |  |  |  |  |  |  |  |
| 1 | 3 | 1.08 (n=300) |  |  |  | 1.10 (n=408) |  |  |  |  |  |  |  |  |  |
| 1 | 4 | 0.93 (n=248) |  |  |  | 1.04 (n=382) |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 1.64 (n=600) |  |  |  | 1.50 (n=728) |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 0.99 (n=598) |  |  |  | 1.15 (n=728) |  |  |  |  |  |  |  |  |  |
| 2 | 3 | 1.02 (n=598) |  |  |  | 1.16 (n=728) |  |  |  |  |  |  |  |  |  |
| 2 | 4 | 0.91 (n=88) |  |  |  | 1.05 (n=716) |  |  |  |  |  |  |  |  |  |
| 3 | 1 | 1.52 (n=600) |  |  |  | 1.39 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 2 | 1.11 (n=598) |  |  |  | 1.16 (n=592) |  |  |  |  |  |  |  |  |  |
| 3 | 3 | 1.05 (n=584) |  |  |  | 1.05 (n=590) |  |  |  |  |  |  |  |  |  |
| 3 | 4 | 0.83 (n=250) |  |  |  | 0.95 (n=530) |  |  |  |  |  |  |  |  |  |
