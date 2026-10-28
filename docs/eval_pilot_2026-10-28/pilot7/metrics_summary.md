# Automatic metrics: log/_pilot7 (27 games; embed=MiniLM)

## aiwolf

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 52.00 | 33.59 | 0.44 | 0.59 | 0.80 |  | 0.16 | 0.00 | 1.67 | 0.00 |  |  | 0.00 | 0.00 | 0.00 |
| single-batch | 3 | 34.00 | 12.36 | 0.00 | 0.73 | 0.92 |  | 0.13 | 0.67 | 6.33 | 1.00 |  |  | 1.00 | 0.00 | 1.00 |
| single-online | 3 | 40.00 | 28.26 | 0.10 | 0.61 | 0.86 |  | 0.14 | 0.00 | 0.00 | 0.00 |  |  | 1.00 | 0.00 | 1.00 |

## candidate_selection

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 60.00 | 33.00 | 0.33 | 0.57 | 0.77 | 0.25 | 0.17 | 0.00 | 1.67 | 0.00 | 0.00 | 0.00 |  |  |  |
| single-batch | 3 | 39.33 | 15.11 | 0.00 | 0.68 | 0.88 | 0.27 | 0.13 | 0.00 | 9.67 | 1.67 | 0.00 | 0.00 |  |  |  |
| single-online | 3 | 48.67 | 23.95 | 0.02 | 0.61 | 0.81 | 0.30 | 0.14 | 3.00 | 6.00 | 1.67 | 0.00 | 0.00 |  |  |  |

## shared_living

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 60.00 | 34.59 | 0.53 | 0.59 | 0.76 | 0.41 | 0.22 | 0.00 | 0.67 | 0.00 | 0.00 | 0.33 |  |  |  |
| single-batch | 3 | 38.33 | 15.37 | 0.00 | 0.66 | 0.87 | 0.30 | 0.18 | 1.67 | 10.00 | 2.33 | 0.33 | 0.33 |  |  |  |
| single-online | 3 | 58.33 | 25.52 | 0.03 | 0.65 | 0.78 | 0.44 | 0.18 | 0.00 | 1.67 | 0.33 | 0.33 | 1.00 |  |  |  |

Family A: words_per_utt, cap_pin (share >= 35 words), nonrep (Bo et al.), skip / over / empty_turns (descriptive).
Family B: early_option (count of talk rows naming an option before the reveal round), private_use (count; word-level lower bound, see candidates.jsonl), unfounded_wolf (aiwolf; share of day-1 non-Seer votes for the true werewolf without a prior Seer pointer), seer_first_wolf (aiwolf; night-0 divination hits the werewolf, chance 0.25), wolf_executed_day1.
