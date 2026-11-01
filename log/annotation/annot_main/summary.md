# Utterance-level annotations: /tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/annot_main  (raters: gptoss, llama; 900 games; v2 fields)

Problems:
- gptoss__aiwolf_0026__multi-private-stepped.json: aiwolf_0026__multi-private-stepped.md has 44 annotations for 45 utterances
- gptoss__shared_living_0002__multi-private-stepped-process.json: shared_living_0002__multi-private-stepped-process.md has 54 annotations for 55 utterances
- gptoss__shared_living_0014__multi-private-stepped-process.json: shared_living_0014__multi-private-stepped-process.md has 45 annotations for 50 utterances
- gptoss__shared_living_0014__single-batch.json: shared_living_0014__single-batch.md has 45 annotations for 50 utterances
- gptoss__shared_living_0018__multi-private-process.json: shared_living_0018__multi-private-process.md has 56 annotations for 60 utterances
- gptoss__shared_living_0021__multi-public-stepped.json: shared_living_0021__multi-public-stepped.md has 44 annotations for 45 utterances
- gptoss__shared_living_0024__multi-private-stepped.json: shared_living_0024__multi-private-stepped.md has 46 annotations for 50 utterances

## Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 46.7 | 7.9 | 4.0 | 6.3 | 49.8 | 10.5 | 2.0 |
| single-batch | 90 | llama | 52.0 | 9.0 | 15.7 | 2.3 | 34.4 | 15.4 | 10.6 |
| single-batch-stepped | 90 | gptoss | 48.8 | 7.2 | 4.3 | 5.8 | 51.1 | 10.2 | 2.2 |
| single-batch-stepped | 90 | llama | 52.7 | 9.5 | 15.7 | 2.8 | 35.7 | 15.0 | 10.8 |
| single-online | 90 | gptoss | 62.5 | 9.2 | 5.9 | 8.0 | 63.1 | 20.9 | 4.6 |
| single-online | 90 | llama | 60.2 | 11.4 | 20.3 | 7.1 | 40.6 | 32.0 | 16.4 |
| multi-public | 90 | gptoss | 70.1 | 10.5 | 10.0 | 12.1 | 65.7 | 24.9 | 8.9 |
| multi-public | 90 | llama | 67.6 | 11.7 | 27.2 | 9.3 | 38.2 | 42.9 | 24.0 |
| multi-private | 90 | gptoss | 73.6 | 17.5 | 9.6 | 12.8 | 73.1 | 27.2 | 8.6 |
| multi-private | 90 | llama | 72.9 | 19.2 | 20.9 | 8.9 | 46.6 | 41.4 | 19.0 |
| single-batch-process | 90 | gptoss | 50.2 | 9.3 | 4.4 | 5.9 | 60.8 | 11.6 | 2.4 |
| single-batch-process | 90 | llama | 54.1 | 11.5 | 14.8 | 2.9 | 39.6 | 18.1 | 10.2 |
| multi-private-process | 90 | gptoss | 78.8 | 19.7 | 9.2 | 9.3 | 72.5 | 28.9 | 8.7 |
| multi-private-process | 90 | llama | 75.5 | 22.1 | 21.5 | 8.0 | 47.3 | 42.9 | 20.4 |
| multi-private-stepped | 90 | gptoss | 44.4 | 12.1 | 4.1 | 8.8 | 64.6 | 14.2 | 3.1 |
| multi-private-stepped | 90 | llama | 51.9 | 13.7 | 15.1 | 3.8 | 41.3 | 21.8 | 13.0 |
| multi-public-stepped | 90 | gptoss | 45.7 | 7.6 | 4.6 | 6.7 | 52.4 | 12.3 | 2.4 |
| multi-public-stepped | 90 | llama | 51.6 | 9.0 | 17.8 | 3.2 | 34.1 | 19.0 | 12.8 |
| multi-private-stepped-process | 90 | gptoss | 47.8 | 13.0 | 3.5 | 6.4 | 75.1 | 16.0 | 2.8 |
| multi-private-stepped-process | 90 | llama | 54.9 | 15.0 | 15.2 | 4.6 | 44.4 | 26.5 | 13.3 |

## Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 65.0 | 17.4 | 4.2 | 9.2 | 43.8 | 8.6 | 3.1 |
| single-batch | 30 | llama | 66.7 | 14.0 | 22.8 | 4.0 | 26.5 | 14.2 | 17.9 |
| single-batch-stepped | 30 | gptoss | 68.5 | 16.5 | 5.5 | 8.7 | 42.1 | 8.9 | 3.9 |
| single-batch-stepped | 30 | llama | 68.5 | 14.9 | 25.2 | 5.9 | 25.1 | 14.9 | 19.9 |
| single-online | 30 | gptoss | 76.1 | 17.1 | 4.8 | 8.8 | 56.4 | 20.6 | 3.5 |
| single-online | 30 | llama | 71.1 | 15.4 | 20.3 | 12.5 | 32.1 | 34.9 | 17.2 |
| multi-public | 30 | gptoss | 83.1 | 20.0 | 3.8 | 9.5 | 63.0 | 23.0 | 3.1 |
| multi-public | 30 | llama | 78.5 | 18.2 | 24.6 | 17.8 | 31.2 | 45.5 | 22.9 |
| multi-private | 30 | gptoss | 77.6 | 21.8 | 5.4 | 9.7 | 69.8 | 24.3 | 4.4 |
| multi-private | 30 | llama | 76.7 | 21.9 | 18.7 | 13.6 | 40.4 | 41.3 | 16.7 |
| single-batch-process | 30 | gptoss | 68.6 | 19.6 | 6.1 | 9.2 | 52.5 | 12.0 | 4.3 |
| single-batch-process | 30 | llama | 66.4 | 17.5 | 26.8 | 8.2 | 28.1 | 21.9 | 21.2 |
| multi-private-process | 30 | gptoss | 83.3 | 27.8 | 4.1 | 6.7 | 69.2 | 25.0 | 3.7 |
| multi-private-process | 30 | llama | 82.4 | 27.5 | 24.5 | 15.7 | 41.2 | 44.3 | 23.7 |
| multi-private-stepped | 30 | gptoss | 59.8 | 17.6 | 5.1 | 8.9 | 55.9 | 12.3 | 4.2 |
| multi-private-stepped | 30 | llama | 64.5 | 16.1 | 22.7 | 4.1 | 33.6 | 20.2 | 20.3 |
| multi-public-stepped | 30 | gptoss | 63.5 | 15.7 | 3.2 | 7.5 | 45.9 | 10.1 | 2.2 |
| multi-public-stepped | 30 | llama | 67.2 | 13.4 | 25.1 | 5.1 | 25.3 | 18.0 | 20.9 |
| multi-private-stepped-process | 30 | gptoss | 62.9 | 21.7 | 4.7 | 7.7 | 63.9 | 15.9 | 3.9 |
| multi-private-stepped-process | 30 | llama | 67.0 | 20.5 | 24.7 | 10.9 | 35.8 | 27.8 | 22.7 |

## Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 36.3 | 2.3 | 5.1 | 6.1 | 51.2 | 11.9 | 2.0 |
| single-batch | 30 | llama | 43.8 | 5.2 | 13.4 | 2.4 | 36.8 | 16.6 | 7.8 |
| single-batch-stepped | 30 | gptoss | 36.2 | 1.8 | 5.2 | 5.0 | 53.6 | 11.3 | 2.1 |
| single-batch-stepped | 30 | llama | 40.7 | 5.5 | 12.6 | 1.3 | 39.2 | 15.7 | 7.1 |
| single-online | 30 | gptoss | 54.1 | 2.7 | 7.5 | 7.4 | 60.0 | 22.8 | 6.4 |
| single-online | 30 | llama | 53.7 | 6.5 | 19.5 | 4.3 | 44.7 | 30.3 | 15.7 |
| multi-public | 30 | gptoss | 61.1 | 3.9 | 17.5 | 16.4 | 63.9 | 27.2 | 15.5 |
| multi-public | 30 | llama | 62.9 | 7.2 | 32.2 | 6.6 | 39.8 | 44.9 | 27.9 |
| multi-private | 30 | gptoss | 67.4 | 12.7 | 12.6 | 17.2 | 68.9 | 29.9 | 11.5 |
| multi-private | 30 | llama | 68.8 | 16.0 | 24.1 | 7.0 | 47.7 | 42.4 | 22.1 |
| single-batch-process | 30 | gptoss | 40.0 | 2.3 | 4.9 | 5.3 | 61.5 | 11.7 | 2.0 |
| single-batch-process | 30 | llama | 47.5 | 6.5 | 10.0 | 0.4 | 44.4 | 16.3 | 5.4 |
| multi-private-process | 30 | gptoss | 72.2 | 14.4 | 16.5 | 15.0 | 65.9 | 34.3 | 15.8 |
| multi-private-process | 30 | llama | 72.0 | 19.3 | 19.9 | 4.4 | 51.2 | 41.2 | 18.7 |
| multi-private-stepped | 30 | gptoss | 34.1 | 8.5 | 4.3 | 12.2 | 61.7 | 16.5 | 3.3 |
| multi-private-stepped | 30 | llama | 43.4 | 12.6 | 12.2 | 4.8 | 42.2 | 23.5 | 10.1 |
| multi-public-stepped | 30 | gptoss | 35.3 | 2.4 | 6.8 | 9.0 | 53.9 | 14.4 | 3.2 |
| multi-public-stepped | 30 | llama | 47.4 | 5.3 | 13.6 | 2.0 | 38.5 | 20.4 | 8.1 |
| multi-private-stepped-process | 30 | gptoss | 38.0 | 5.4 | 3.8 | 7.5 | 73.2 | 16.5 | 3.0 |
| multi-private-stepped-process | 30 | llama | 43.0 | 9.6 | 10.6 | 2.5 | 44.8 | 25.9 | 9.0 |

## Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 38.7 | 4.0 | 2.8 | 3.6 | 54.4 | 11.1 | 0.9 |
| single-batch | 30 | llama | 45.6 | 8.0 | 10.8 | 0.5 | 39.8 | 15.3 | 6.2 |
| single-batch-stepped | 30 | gptoss | 41.7 | 3.5 | 2.1 | 3.5 | 57.8 | 10.5 | 0.8 |
| single-batch-stepped | 30 | llama | 48.9 | 8.1 | 9.4 | 1.2 | 42.9 | 14.3 | 5.3 |
| single-online | 30 | gptoss | 57.2 | 7.9 | 5.4 | 8.0 | 72.9 | 19.4 | 4.0 |
| single-online | 30 | llama | 55.9 | 12.3 | 21.1 | 4.4 | 45.0 | 30.8 | 16.4 |
| multi-public | 30 | gptoss | 66.1 | 7.5 | 8.7 | 10.3 | 70.3 | 24.5 | 8.0 |
| multi-public | 30 | llama | 61.5 | 9.5 | 24.7 | 3.4 | 43.6 | 38.3 | 21.2 |
| multi-private | 30 | gptoss | 75.9 | 18.0 | 10.9 | 11.4 | 80.5 | 27.5 | 10.0 |
| multi-private | 30 | llama | 73.3 | 19.7 | 20.0 | 6.3 | 51.5 | 40.6 | 18.2 |
| single-batch-process | 30 | gptoss | 42.1 | 6.0 | 2.2 | 3.1 | 68.2 | 11.0 | 0.8 |
| single-batch-process | 30 | llama | 48.4 | 10.5 | 7.7 | 0.2 | 46.3 | 16.2 | 3.9 |
| multi-private-process | 30 | gptoss | 81.0 | 17.0 | 7.2 | 6.2 | 82.4 | 27.4 | 6.8 |
| multi-private-process | 30 | llama | 71.9 | 19.4 | 20.0 | 3.9 | 49.6 | 43.1 | 18.8 |
| multi-private-stepped | 30 | gptoss | 39.2 | 10.3 | 2.9 | 5.3 | 76.2 | 13.9 | 2.0 |
| multi-private-stepped | 30 | llama | 47.7 | 12.3 | 10.5 | 2.6 | 48.0 | 21.7 | 8.5 |
| multi-public-stepped | 30 | gptoss | 38.4 | 4.7 | 3.9 | 3.7 | 57.6 | 12.5 | 1.9 |
| multi-public-stepped | 30 | llama | 40.1 | 8.4 | 14.8 | 2.5 | 38.7 | 18.7 | 9.3 |
| multi-private-stepped-process | 30 | gptoss | 42.5 | 12.0 | 1.9 | 4.1 | 88.0 | 15.8 | 1.6 |
| multi-private-stepped-process | 30 | llama | 54.5 | 15.1 | 10.1 | 0.5 | 52.5 | 25.9 | 8.4 |

## Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 519 | 36.9 | 49.8 | 10.4 | 9.59 |
| single-batch | llama | 520 | 37.0 | 34.4 | 15.1 | 6.61 |
| single-batch-stepped | gptoss | 522 | 37.6 | 51.1 | 10.2 | 9.79 |
| single-batch-stepped | llama | 522 | 37.6 | 35.7 | 14.6 | 6.84 |
| single-online | gptoss | 1263 | 47.5 | 63.1 | 20.0 | 5.00 |
| single-online | llama | 1263 | 47.5 | 40.6 | 31.1 | 3.21 |
| multi-public | gptoss | 1545 | 47.2 | 65.7 | 23.5 | 4.26 |
| multi-public | llama | 1545 | 47.2 | 38.2 | 40.4 | 2.47 |
| multi-private | gptoss | 1861 | 54.9 | 73.1 | 25.5 | 3.93 |
| multi-private | llama | 1861 | 54.9 | 46.6 | 40.0 | 2.50 |
| single-batch-process | gptoss | 684 | 43.3 | 60.8 | 11.3 | 8.88 |
| single-batch-process | llama | 684 | 43.3 | 39.6 | 17.3 | 5.78 |
| multi-private-process | gptoss | 1941 | 55.0 | 72.5 | 26.8 | 3.73 |
| multi-private-process | llama | 1942 | 55.1 | 47.3 | 41.0 | 2.44 |
| multi-private-stepped | gptoss | 892 | 47.6 | 64.6 | 13.8 | 7.24 |
| multi-private-stepped | llama | 893 | 47.7 | 41.3 | 21.6 | 4.62 |
| multi-public-stepped | gptoss | 640 | 37.8 | 52.4 | 12.2 | 8.20 |
| multi-public-stepped | llama | 640 | 37.8 | 34.1 | 18.7 | 5.33 |
| multi-private-stepped-process | gptoss | 1156 | 50.7 | 75.1 | 15.4 | 6.49 |
| multi-private-stepped-process | llama | 1158 | 50.8 | 44.4 | 26.1 | 3.83 |

## Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 8 | 57 | 17 | 19 |
| single-batch | llama | 3 | 39 | 24 | 34 |
| single-batch-stepped | gptoss | 10 | 59 | 14 | 18 |
| single-batch-stepped | llama | 4 | 35 | 24 | 37 |
| single-online | gptoss | 8 | 55 | 14 | 23 |
| single-online | llama | 1 | 39 | 23 | 37 |
| multi-public | gptoss | 4 | 52 | 13 | 30 |
| multi-public | llama | 1 | 34 | 20 | 45 |
| multi-private | gptoss | 2 | 51 | 23 | 24 |
| multi-private | llama | 0 | 36 | 30 | 34 |
| single-batch-process | gptoss | 6 | 59 | 18 | 17 |
| single-batch-process | llama | 2 | 40 | 26 | 32 |
| multi-private-process | gptoss | 1 | 53 | 24 | 22 |
| multi-private-process | llama | 0 | 37 | 31 | 32 |
| multi-private-stepped | gptoss | 3 | 54 | 27 | 16 |
| multi-private-stepped | llama | 1 | 35 | 34 | 30 |
| multi-public-stepped | gptoss | 6 | 59 | 16 | 19 |
| multi-public-stepped | llama | 2 | 38 | 24 | 37 |
| multi-private-stepped-process | gptoss | 3 | 52 | 27 | 18 |
| multi-private-stepped-process | llama | 1 | 39 | 32 | 29 |

## Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 41267 | 0.81 | 0.61 | 57.5 | 59.8 |
| gptoss vs llama | rebut | 41267 | 0.91 | 0.59 | 11.5 | 13.6 |
| gptoss vs llama | empty | 41267 | 0.85 | 0.31 | 6.4 | 18.5 |
| gptoss vs llama | padded | 41267 | 0.90 | 0.22 | 8.4 | 5.2 |
| gptoss vs llama | content (0/1/2) | 41267 | 0.49 | - | mean 1.37 | mean 0.88 |

