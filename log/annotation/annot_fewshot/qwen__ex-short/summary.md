# Utterance-level annotations: /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/qwen__ex-short  (raters: gptoss, llama; 180 games; v2 fields)

## Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 35.8 | 3.9 | 5.0 | 5.5 | 67.6 | 8.2 | 3.2 |
| single-batch | 90 | llama | 41.4 | 6.6 | 11.1 | 3.4 | 46.3 | 11.9 | 8.8 |
| multi-private | 90 | gptoss | 65.6 | 8.2 | 5.0 | 8.3 | 81.0 | 15.0 | 4.7 |
| multi-private | 90 | llama | 64.7 | 14.1 | 19.5 | 5.7 | 45.9 | 26.7 | 17.7 |

## Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 48.0 | 8.0 | 10.2 | 13.6 | 55.8 | 6.2 | 5.7 |
| single-batch | 30 | llama | 55.9 | 9.1 | 23.7 | 7.0 | 32.3 | 10.6 | 18.6 |
| multi-private | 30 | gptoss | 62.9 | 13.6 | 5.4 | 11.6 | 71.8 | 12.5 | 5.0 |
| multi-private | 30 | llama | 61.5 | 16.0 | 31.4 | 13.1 | 31.5 | 28.1 | 28.1 |

## Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 26.3 | 1.2 | 3.7 | 2.3 | 75.6 | 9.5 | 3.4 |
| single-batch | 30 | llama | 32.0 | 4.8 | 8.2 | 3.1 | 49.4 | 14.0 | 6.9 |
| multi-private | 30 | gptoss | 63.4 | 4.0 | 4.1 | 5.8 | 86.1 | 16.0 | 3.9 |
| multi-private | 30 | llama | 62.2 | 12.0 | 15.1 | 3.4 | 50.1 | 26.9 | 14.6 |

## Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 33.1 | 2.5 | 1.1 | 0.6 | 71.5 | 8.8 | 0.6 |
| single-batch | 30 | llama | 36.2 | 5.8 | 1.4 | 0.1 | 57.2 | 10.9 | 0.8 |
| multi-private | 30 | gptoss | 70.6 | 7.1 | 5.6 | 7.6 | 85.2 | 16.5 | 5.1 |
| multi-private | 30 | llama | 70.6 | 14.3 | 12.1 | 0.6 | 55.9 | 25.1 | 10.5 |

## Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 540 | 51.0 | 67.6 | 8.0 | 12.52 |
| single-batch | llama | 540 | 51.0 | 46.3 | 11.7 | 8.57 |
| multi-private | gptoss | 1182 | 54.1 | 81.0 | 14.6 | 6.86 |
| multi-private | llama | 1182 | 54.1 | 45.9 | 25.8 | 3.88 |

## Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 8 | 69 | 11 | 12 |
| single-batch | llama | 3 | 46 | 21 | 31 |
| multi-private | gptoss | 3 | 74 | 11 | 13 |
| multi-private | llama | 1 | 43 | 26 | 31 |

## Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 9466 | 0.93 | 0.87 | 51.0 | 53.1 |
| gptoss vs llama | rebut | 9466 | 0.93 | 0.51 | 5.8 | 10.3 |
| gptoss vs llama | empty | 9466 | 0.88 | 0.32 | 4.8 | 14.3 |
| gptoss vs llama | padded | 9466 | 0.92 | 0.23 | 6.4 | 4.1 |
| gptoss vs llama | content (0/1/2) | 9466 | 0.48 | - | mean 1.41 | mean 0.88 |

