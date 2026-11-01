# Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.9 | 0.47 | 0.25 | 0.34 | 0.57 |
| single-batch | llama | 3.9 | 0.47 | 0.16 | 0.23 | 0.63 |
| single-batch-stepped | gptoss | 4.1 | 0.49 | 0.32 | 0.40 | 0.59 |
| single-batch-stepped | llama | 4.1 | 0.49 | 0.18 | 0.28 | 0.64 |
| single-online | gptoss | 5.6 | 0.32 | 0.27 | 0.28 | 0.43 |
| single-online | llama | 5.6 | 0.32 | 0.05 | 0.12 | 0.44 |
| multi-public | gptoss | 6.1 | 0.63 | 0.17 | 0.12 | 0.24 |
| multi-public | llama | 6.1 | 0.63 | 0.04 | 0.04 | 0.23 |
| multi-private | gptoss | 8.1 | 0.64 | 0.07 | 0.05 | 0.25 |
| multi-private | llama | 8.1 | 0.64 | 0.01 | 0.01 | 0.22 |
| single-batch-process | gptoss | 4.8 | 0.51 | 0.23 | 0.29 | 0.47 |
| single-batch-process | llama | 4.8 | 0.51 | 0.11 | 0.18 | 0.48 |
| multi-private-process | gptoss | 7.3 | 0.66 | 0.06 | 0.01 | 0.19 |
| multi-private-process | llama | 7.3 | 0.66 | 0.01 | 0.00 | 0.16 |
| multi-private-stepped | gptoss | 4.6 | 0.36 | 0.11 | 0.18 | 0.40 |
| multi-private-stepped | llama | 4.6 | 0.36 | 0.04 | 0.10 | 0.46 |
| multi-public-stepped | gptoss | 3.8 | 0.36 | 0.19 | 0.23 | 0.49 |
| multi-public-stepped | llama | 3.8 | 0.36 | 0.08 | 0.14 | 0.56 |
| multi-private-stepped-process | gptoss | 5.2 | 0.39 | 0.08 | 0.12 | 0.39 |
| multi-private-stepped-process | llama | 5.2 | 0.39 | 0.04 | 0.11 | 0.42 |

# Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.03 (n=298) | 1.04 (n=300) | 1.20 (n=296) | 1.28 (n=300) | 1.16 (n=300) | 1.22 (n=300) | 1.37 (n=300) | 0.98 (n=296) | 1.04 (n=300) | 1.16 (n=300) |  |  |  |  |
| 0 | 2 | 1.06 (n=260) | 1.02 (n=256) | 1.22 (n=300) | 1.30 (n=300) | 1.22 (n=300) | 1.13 (n=298) | 1.28 (n=300) | 1.14 (n=264) | 1.08 (n=252) | 1.19 (n=298) |  |  |  |  |
| 0 | 3 | 0.95 (n=238) | 0.91 (n=224) | 1.11 (n=300) | 1.25 (n=300) | 1.13 (n=300) | 1.00 (n=296) | 1.20 (n=300) | 1.04 (n=270) | 0.95 (n=226) | 1.09 (n=298) |  |  |  |  |
| 0 | 4 | 0.80 (n=40) | 0.50 (n=32) | 0.51 (n=290) | 0.61 (n=300) | 0.55 (n=292) | 0.51 (n=202) | 0.71 (n=300) | 0.57 (n=158) | 0.56 (n=68) | 0.70 (n=292) |  |  |  |  |
| 1 | 1 | 1.40 (n=900) | 1.42 (n=900) | 1.38 (n=900) | 1.48 (n=900) | 1.32 (n=900) | 1.39 (n=900) | 1.32 (n=900) | 1.22 (n=900) | 1.37 (n=900) | 1.27 (n=898) |  |  |  |  |
| 1 | 2 | 1.14 (n=428) | 1.12 (n=432) | 1.03 (n=794) | 1.03 (n=866) | 1.12 (n=896) | 1.14 (n=802) | 1.17 (n=900) | 1.11 (n=878) | 1.10 (n=514) | 1.19 (n=900) |  |  |  |  |
| 1 | 3 | 1.08 (n=372) | 1.03 (n=366) | 0.95 (n=704) | 0.89 (n=802) | 0.97 (n=876) | 1.07 (n=564) | 0.99 (n=900) | 1.12 (n=690) | 1.15 (n=332) | 1.16 (n=894) |  |  |  |  |
| 1 | 4 | 0.88 (n=278) | 0.82 (n=276) | 0.78 (n=600) | 0.81 (n=630) | 0.73 (n=826) | 0.94 (n=298) | 0.69 (n=900) | 0.92 (n=397) | 0.94 (n=264) | 0.97 (n=552) |  |  |  |  |
| 2 | 1 | 1.63 (n=600) | 1.67 (n=600) | 1.59 (n=600) | 1.73 (n=600) | 1.48 (n=710) | 1.58 (n=600) | 1.44 (n=696) | 1.27 (n=704) | 1.60 (n=600) | 1.33 (n=696) |  |  |  |  |
| 2 | 2 | 1.05 (n=600) | 1.09 (n=600) | 1.14 (n=600) | 1.23 (n=600) | 1.18 (n=710) | 1.12 (n=600) | 1.15 (n=696) | 1.13 (n=704) | 1.10 (n=600) | 1.20 (n=696) |  |  |  |  |
| 2 | 3 | 1.07 (n=594) | 1.11 (n=588) | 1.13 (n=600) | 1.15 (n=600) | 1.16 (n=710) | 1.12 (n=600) | 1.14 (n=696) | 1.11 (n=704) | 1.11 (n=590) | 1.21 (n=696) |  |  |  |  |
| 2 | 4 | 0.89 (n=305) | 0.86 (n=380) | 0.98 (n=600) | 0.91 (n=600) | 1.02 (n=710) | 0.93 (n=272) | 0.99 (n=692) | 0.97 (n=468) | 0.94 (n=480) | 1.14 (n=424) |  |  |  |  |
| 3 | 1 | 1.35 (n=600) | 1.44 (n=600) | 1.26 (n=600) | 1.28 (n=600) | 1.28 (n=600) | 1.42 (n=600) | 1.25 (n=600) | 1.35 (n=600) | 1.43 (n=600) | 1.39 (n=600) |  |  |  |  |
| 3 | 2 | 1.01 (n=536) | 1.09 (n=570) | 1.01 (n=540) | 0.82 (n=512) | 1.08 (n=600) | 1.18 (n=600) | 1.07 (n=600) | 1.17 (n=600) | 0.98 (n=516) | 1.26 (n=600) |  |  |  |  |
| 3 | 3 | 0.87 (n=446) | 0.94 (n=482) | 0.96 (n=490) | 0.69 (n=378) | 0.99 (n=588) | 1.06 (n=586) | 0.98 (n=582) | 1.07 (n=580) | 0.85 (n=368) | 1.14 (n=600) |  |  |  |  |
| 3 | 4 | 0.57 (n=152) | 0.56 (n=156) | 0.72 (n=338) | 0.58 (n=204) | 0.82 (n=562) | 0.53 (n=280) | 0.76 (n=548) | 0.86 (n=360) | 0.57 (n=199) | 0.97 (n=388) |  |  |  |  |
