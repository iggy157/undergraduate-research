# Utterance-level annotations: /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/qwen__ex-long  (raters: gptoss, llama; 180 games; v2 fields)

## Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 48.3 | 5.3 | 5.9 | 11.0 | 77.4 | 10.4 | 5.3 |
| single-batch | 90 | llama | 50.5 | 9.5 | 21.0 | 5.6 | 41.9 | 19.5 | 19.2 |
| multi-private | 90 | gptoss | 73.5 | 12.7 | 15.9 | 16.7 | 73.3 | 19.2 | 15.5 |
| multi-private | 90 | llama | 71.6 | 18.3 | 30.6 | 5.2 | 42.0 | 34.3 | 29.0 |

## Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 53.3 | 10.5 | 3.3 | 17.8 | 66.9 | 7.7 | 2.7 |
| single-batch | 30 | llama | 55.7 | 10.6 | 29.6 | 10.4 | 29.6 | 18.2 | 27.4 |
| multi-private | 30 | gptoss | 70.8 | 20.4 | 10.9 | 17.6 | 70.3 | 14.1 | 10.1 |
| multi-private | 30 | llama | 65.9 | 18.2 | 36.2 | 9.7 | 32.3 | 31.7 | 33.2 |

## Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 43.9 | 1.9 | 9.7 | 8.5 | 82.1 | 12.1 | 8.9 |
| single-batch | 30 | llama | 47.2 | 7.0 | 21.5 | 4.0 | 47.8 | 21.2 | 19.5 |
| multi-private | 30 | gptoss | 75.8 | 7.6 | 15.8 | 13.4 | 75.8 | 21.3 | 15.6 |
| multi-private | 30 | llama | 75.3 | 15.9 | 29.3 | 3.1 | 45.3 | 37.2 | 28.2 |

## Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 47.7 | 3.3 | 4.9 | 6.5 | 83.2 | 11.3 | 4.2 |
| single-batch | 30 | llama | 48.7 | 10.9 | 11.8 | 2.3 | 48.4 | 19.0 | 10.6 |
| multi-private | 30 | gptoss | 73.9 | 10.3 | 21.0 | 19.1 | 73.9 | 22.1 | 20.7 |
| multi-private | 30 | llama | 73.7 | 20.7 | 26.2 | 2.8 | 48.4 | 33.8 | 25.6 |

## Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 781 | 50.9 | 77.4 | 10.1 | 9.91 |
| single-batch | llama | 781 | 50.9 | 41.9 | 18.6 | 5.37 |
| multi-private | gptoss | 1345 | 55.7 | 73.3 | 18.3 | 5.45 |
| multi-private | llama | 1345 | 55.7 | 42.0 | 32.0 | 3.12 |

## Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 3 | 72 | 9 | 15 |
| single-batch | llama | 1 | 40 | 23 | 37 |
| multi-private | gptoss | 2 | 62 | 15 | 21 |
| multi-private | llama | 0 | 32 | 30 | 37 |

## Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 9595 | 0.95 | 0.89 | 61.6 | 61.6 |
| gptoss vs llama | rebut | 9595 | 0.89 | 0.46 | 8.6 | 14.0 |
| gptoss vs llama | empty | 9595 | 0.81 | 0.38 | 11.4 | 25.2 |
| gptoss vs llama | padded | 9595 | 0.87 | 0.21 | 13.6 | 4.8 |
| gptoss vs llama | content (0/1/2) | 9595 | 0.37 | - | mean 1.41 | mean 0.79 |


