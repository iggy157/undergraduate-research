# Utterance-level annotations: /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/gemma__ex-short  (raters: gptoss, llama; 180 games; v2 fields)

## Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 47.0 | 7.1 | 2.3 | 6.3 | 49.3 | 11.5 | 1.8 |
| single-batch | 90 | llama | 50.1 | 9.4 | 14.2 | 2.0 | 34.8 | 16.9 | 10.9 |
| multi-private | 90 | gptoss | 55.6 | 11.5 | 5.7 | 7.3 | 64.8 | 25.9 | 4.9 |
| multi-private | 90 | llama | 58.7 | 16.1 | 15.8 | 5.6 | 43.3 | 38.8 | 14.1 |

## Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 66.8 | 16.8 | 3.3 | 11.0 | 41.4 | 9.4 | 2.9 |
| single-batch | 30 | llama | 68.2 | 15.7 | 25.2 | 4.9 | 23.5 | 17.1 | 21.7 |
| multi-private | 30 | gptoss | 79.5 | 17.1 | 5.9 | 5.3 | 60.1 | 28.0 | 4.5 |
| multi-private | 30 | llama | 75.4 | 19.4 | 20.6 | 10.7 | 39.2 | 43.9 | 17.9 |

## Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 40.5 | 1.1 | 1.9 | 4.7 | 53.1 | 12.5 | 1.6 |
| single-batch | 30 | llama | 46.2 | 3.3 | 9.9 | 0.5 | 39.9 | 16.8 | 6.5 |
| multi-private | 30 | gptoss | 44.8 | 6.4 | 9.2 | 12.9 | 58.1 | 27.8 | 8.6 |
| multi-private | 30 | llama | 48.7 | 10.2 | 18.3 | 4.1 | 40.7 | 39.2 | 17.1 |

## Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 33.8 | 3.4 | 1.5 | 3.2 | 53.5 | 12.7 | 0.9 |
| single-batch | 30 | llama | 36.0 | 9.0 | 7.4 | 0.6 | 41.0 | 16.7 | 4.6 |
| multi-private | 30 | gptoss | 42.6 | 11.0 | 2.0 | 3.7 | 76.2 | 21.9 | 1.7 |
| multi-private | 30 | llama | 51.9 | 18.7 | 8.5 | 2.2 | 50.1 | 33.3 | 7.5 |

## Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 567 | 35.7 | 49.3 | 11.5 | 8.69 |
| single-batch | llama | 567 | 35.7 | 34.8 | 16.3 | 6.13 |
| multi-private | gptoss | 1582 | 47.1 | 64.8 | 24.4 | 4.10 |
| multi-private | llama | 1582 | 47.1 | 43.3 | 36.5 | 2.74 |

## Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 9 | 64 | 14 | 13 |
| single-batch | llama | 4 | 37 | 27 | 32 |
| multi-private | gptoss | 3 | 59 | 20 | 18 |
| multi-private | llama | 1 | 32 | 30 | 37 |

## Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 7458 | 0.87 | 0.74 | 51.5 | 54.6 |
| gptoss vs llama | rebut | 7458 | 0.91 | 0.56 | 9.4 | 13.2 |
| gptoss vs llama | empty | 7458 | 0.87 | 0.26 | 4.2 | 14.6 |
| gptoss vs llama | padded | 7458 | 0.91 | 0.13 | 6.7 | 3.9 |
| gptoss vs llama | content (0/1/2) | 7458 | 0.53 | - | mean 1.38 | mean 0.94 |


