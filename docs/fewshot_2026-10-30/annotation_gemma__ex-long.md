# Utterance-level annotations: /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_fewshot/gemma__ex-long  (raters: gptoss, llama; 180 games; v2 fields)

## Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 49.2 | 6.9 | 3.7 | 8.3 | 60.8 | 14.7 | 2.5 |
| single-batch | 90 | llama | 49.1 | 8.6 | 16.7 | 6.7 | 37.5 | 23.6 | 12.6 |
| multi-private | 90 | gptoss | 68.0 | 13.8 | 8.3 | 11.3 | 72.5 | 29.6 | 7.6 |
| multi-private | 90 | llama | 68.3 | 17.3 | 21.7 | 10.9 | 46.2 | 46.1 | 20.1 |

## Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 63.6 | 12.9 | 5.0 | 10.8 | 56.5 | 13.6 | 3.2 |
| single-batch | 30 | llama | 62.2 | 14.0 | 26.5 | 14.4 | 30.0 | 24.9 | 20.9 |
| multi-private | 30 | gptoss | 77.7 | 16.4 | 5.7 | 8.1 | 70.3 | 26.3 | 4.9 |
| multi-private | 30 | llama | 80.4 | 20.2 | 19.7 | 15.6 | 42.3 | 44.6 | 18.0 |

## Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 38.8 | 2.8 | 2.8 | 8.1 | 58.3 | 15.7 | 2.1 |
| single-batch | 30 | llama | 40.5 | 4.8 | 12.4 | 1.4 | 40.5 | 22.6 | 8.6 |
| multi-private | 30 | gptoss | 60.5 | 10.8 | 13.7 | 17.5 | 64.1 | 34.7 | 12.7 |
| multi-private | 30 | llama | 60.0 | 13.1 | 26.9 | 6.7 | 45.0 | 49.9 | 24.8 |

## Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 45.3 | 4.8 | 3.4 | 6.1 | 67.6 | 14.7 | 2.3 |
| single-batch | 30 | llama | 44.5 | 6.9 | 11.2 | 4.3 | 42.1 | 23.2 | 8.5 |
| multi-private | 30 | gptoss | 65.8 | 14.3 | 5.6 | 8.3 | 83.1 | 27.8 | 5.2 |
| multi-private | 30 | llama | 64.6 | 18.6 | 18.6 | 10.3 | 51.3 | 43.7 | 17.3 |

## Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 868 | 42.9 | 60.8 | 14.3 | 7.00 |
| single-batch | llama | 868 | 42.9 | 37.5 | 23.1 | 4.32 |
| multi-private | gptoss | 2011 | 55.3 | 72.5 | 27.7 | 3.61 |
| multi-private | llama | 2011 | 55.3 | 46.2 | 43.5 | 2.30 |

## Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 4 | 66 | 14 | 17 |
| single-batch | llama | 1 | 41 | 23 | 35 |
| multi-private | gptoss | 2 | 53 | 20 | 26 |
| multi-private | llama | 0 | 37 | 29 | 34 |

## Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 8840 | 0.83 | 0.64 | 59.3 | 59.3 |
| gptoss vs llama | rebut | 8840 | 0.92 | 0.60 | 10.6 | 13.3 |
| gptoss vs llama | empty | 8840 | 0.83 | 0.29 | 6.4 | 19.6 |
| gptoss vs llama | padded | 8840 | 0.88 | 0.32 | 10.2 | 8.8 |
| gptoss vs llama | content (0/1/2) | 8840 | 0.48 | - | mean 1.36 | mean 0.85 |


