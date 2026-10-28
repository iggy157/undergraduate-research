# Automatic metrics: log/_pilot6 (72 games; embed=MiniLM)

## aiwolf

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 52.00 | 33.21 | 0.47 | 0.62 | 0.00 | 3.00 | 0.00 |  |  | 0.00 | 0.00 | 0.00 |
| multi-private-process | 3 | 44.00 | 34.21 | 0.49 | 0.63 | 0.00 | 2.67 | 0.00 |  |  | 0.33 | 0.25 | 0.67 |
| multi-public | 3 | 40.00 | 32.23 | 0.33 | 0.60 | 0.00 | 1.67 | 0.00 |  |  | 1.00 | 0.00 | 1.00 |
| single-batch | 6 | 29.67 | 11.67 | 0.00 | 0.74 | 3.33 | 7.00 | 1.67 |  |  | 1.00 | 0.00 | 1.00 |
| single-batch-process | 3 | 36.67 | 16.01 | 0.00 | 0.71 | 0.00 | 6.67 | 0.67 |  |  | 1.00 | 0.00 | 1.00 |
| single-batch-stepped | 3 | 29.33 | 10.75 | 0.00 | 0.74 | 4.00 | 6.67 | 1.67 |  |  | 1.00 | 0.00 | 1.00 |
| single-online | 3 | 40.00 | 27.45 | 0.07 | 0.66 | 0.00 | 0.00 | 0.00 |  |  | 1.00 | 0.33 | 1.00 |

## candidate_selection

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 51.00 | 31.97 | 0.23 | 0.56 | 0.33 | 5.00 | 0.00 | 0.00 | 0.00 |  |  |  |
| multi-private-process | 3 | 56.33 | 32.23 | 0.25 | 0.53 | 0.67 | 6.67 | 0.00 | 0.00 | 0.00 |  |  |  |
| multi-public | 3 | 48.00 | 29.52 | 0.15 | 0.54 | 3.67 | 8.33 | 0.33 | 0.00 | 0.00 |  |  |  |
| single-batch | 6 | 28.33 | 17.27 | 0.00 | 0.61 | 5.00 | 15.00 | 4.00 | 0.00 | 0.33 |  |  |  |
| single-batch-process | 3 | 30.00 | 17.56 | 0.00 | 0.63 | 6.67 | 15.00 | 4.33 | 0.00 | 0.00 |  |  |  |
| single-batch-stepped | 3 | 30.00 | 15.11 | 0.00 | 0.67 | 5.00 | 13.33 | 3.67 | 0.00 | 0.00 |  |  |  |
| single-online | 3 | 44.00 | 23.35 | 0.00 | 0.56 | 4.00 | 5.00 | 1.67 | 0.00 | 0.00 |  |  |  |

## shared_living

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 59.33 | 33.67 | 0.43 | 0.60 | 0.33 | 1.33 | 0.00 | 0.00 | 0.33 |  |  |  |
| multi-private-process | 3 | 60.00 | 33.38 | 0.38 | 0.54 | 0.00 | 3.33 | 0.00 | 0.00 | 0.33 |  |  |  |
| multi-public | 3 | 58.33 | 29.87 | 0.11 | 0.55 | 0.33 | 1.00 | 0.00 | 0.00 | 0.33 |  |  |  |
| single-batch | 6 | 28.67 | 15.16 | 0.00 | 0.64 | 5.33 | 13.00 | 3.67 | 0.00 | 0.33 |  |  |  |
| single-batch-process | 3 | 37.00 | 16.26 | 0.00 | 0.67 | 5.00 | 13.00 | 3.33 | 0.00 | 0.67 |  |  |  |
| single-batch-stepped | 3 | 28.00 | 15.09 | 0.00 | 0.63 | 4.00 | 14.67 | 3.67 | 0.00 | 0.33 |  |  |  |
| single-online | 3 | 52.00 | 22.77 | 0.01 | 0.62 | 2.00 | 4.33 | 1.00 | 0.33 | 0.00 |  |  |  |

Family A: words_per_utt, cap_pin (share >= 35 words), nonrep (Bo et al.), skip / over / empty_turns (descriptive).
Family B: early_option (count of talk rows naming an option before the reveal round), private_use (count; word-level lower bound, see candidates.jsonl), unfounded_wolf (aiwolf; share of day-1 non-Seer votes for the true werewolf without a prior Seer pointer), seer_first_wolf (aiwolf; night-0 divination hits the werewolf, chance 0.25), wolf_executed_day1.
