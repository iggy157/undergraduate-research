# Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.3 | 0.35 | 0.10 | 0.08 | 0.28 |
| single-batch | llama | 3.3 | 0.35 | 0.02 | 0.03 | 0.30 |
| multi-private | gptoss | 4.9 | 0.55 | 0.12 | 0.10 | 0.40 |
| multi-private | llama | 4.9 | 0.55 | 0.02 | 0.02 | 0.39 |

# Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.42 (n=300) |  |  |  | 1.19 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 2 | 1.35 (n=300) |  |  |  | 1.17 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 3 | 1.09 (n=300) |  |  |  | 0.87 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 4 | 0.52 (n=230) |  |  |  | 0.53 (n=298) |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1.40 (n=900) |  |  |  | 1.41 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 1.24 (n=890) |  |  |  | 1.16 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 3 | 1.14 (n=890) |  |  |  | 0.86 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 4 | 0.76 (n=696) |  |  |  | 0.49 (n=890) |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 1.46 (n=624) |  |  |  | 1.53 (n=710) |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 1.19 (n=624) |  |  |  | 1.23 (n=710) |  |  |  |  |  |  |  |  |  |
| 2 | 3 | 1.21 (n=624) |  |  |  | 1.12 (n=710) |  |  |  |  |  |  |  |  |  |
| 2 | 4 | 1.06 (n=594) |  |  |  | 0.79 (n=710) |  |  |  |  |  |  |  |  |  |
| 3 | 1 | 1.38 (n=590) |  |  |  | 1.30 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 2 | 1.14 (n=590) |  |  |  | 1.06 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 3 | 1.06 (n=580) |  |  |  | 0.91 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 4 | 0.98 (n=430) |  |  |  | 0.75 (n=600) |  |  |  |  |  |  |  |  |  |

