# Automatic metrics: log/_pilot8 (18 games; embed=MiniLM)

## aiwolf

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 53.33 | 34.98 | 0.57 | 0.61 | 0.81 |  | 0.16 | 0.00 | 3.33 | 0.00 |  |  | 0.00 | 0.00 | 0.00 |
| single-batch | 3 | 31.33 | 10.74 | 0.00 | 0.76 | 0.91 |  | 0.13 | 2.67 | 6.00 | 1.33 |  |  | 1.00 | 0.00 | 1.00 |

## candidate_selection

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 58.33 | 32.64 | 0.33 | 0.59 | 0.77 | 0.25 | 0.17 | 1.33 | 3.33 | 0.33 | 0.00 | 0.00 |  |  |  |
| single-batch | 3 | 36.00 | 15.68 | 0.00 | 0.73 | 0.92 | 0.23 | 0.12 | 1.67 | 10.67 | 2.33 | 0.00 | 0.00 |  |  |  |

## shared_living

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 3 | 60.00 | 34.01 | 0.50 | 0.59 | 0.77 | 0.28 | 0.21 | 0.00 | 1.67 | 0.00 | 0.00 | 0.67 |  |  |  |
| single-batch | 3 | 41.00 | 14.23 | 0.00 | 0.67 | 0.87 | 0.23 | 0.16 | 3.33 | 10.00 | 2.67 | 0.33 | 0.33 |  |  |  |

Family A: words_per_utt, cap_pin (share >= 35 words), nonrep (Bo et al.), skip / over / empty_turns (descriptive).
Family B: early_option (count of talk rows naming an option before the reveal round), private_use (count; word-level lower bound, see candidates.jsonl), unfounded_wolf (aiwolf; share of day-1 non-Seer votes for the true werewolf without a prior Seer pointer), seer_first_wolf (aiwolf; night-0 divination hits the werewolf, chance 0.25), wolf_executed_day1.
