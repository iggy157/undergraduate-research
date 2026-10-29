# Goal swap on identical histories (scripts/goal_swap.py)

The same recorded game state (system prompt + transcript so far + the seat's label) is given to the model under the other generation goal: online = the state as the user message (next line only); batch = the single-batch writing request as the user message and the transcript continued as the model's own output. Greedy, the seat's stop strings. words = whitespace tokens (0 for Skip / Over).

## gemma online→batch (multi-private): 4982 states from 90 games (source multi-private)

| position | n | words online (recorded) | words batch (swapped) | diff | share shorter | share longer | pass online (recorded) | pass batch (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4982 | 33.7 | 31.1 | -2.5 | 0.57 | 0.32 | 0.01 | 0.05 |
| period turn 1 | 1255 | 34.0 | 31.9 | -2.0 | 0.58 | 0.32 | 0.00 | 0.00 |
| later turns | 3727 | 33.6 | 30.8 | -2.7 | 0.56 | 0.33 | 0.01 | 0.06 |
| round 0 | 600 | 31.3 | 26.4 | -4.9 | 0.74 | 0.18 | 0.01 | 0.06 |
| round 1 | 1771 | 32.7 | 28.0 | -4.7 | 0.68 | 0.21 | 0.01 | 0.09 |
| round 2 | 1420 | 35.9 | 35.6 | -0.3 | 0.45 | 0.42 | 0.00 | 0.00 |
| round 3 | 1191 | 33.6 | 32.8 | -0.8 | 0.45 | 0.46 | 0.01 | 0.03 |

Per-setup mean difference (swapped − recorded): median -2.5 words, swapped shorter in 90/90 setups.

## gemma online→batch (multi-private-process): 4967 states from 90 games (source multi-private)

| position | n | words online (recorded) | words batch (swapped) | diff | share shorter | share longer | pass online (recorded) | pass batch (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4967 | 35.2 | 33.7 | -1.6 | 0.54 | 0.35 | 0.00 | 0.02 |
| period turn 1 | 1248 | 35.4 | 33.6 | -1.8 | 0.61 | 0.29 | 0.00 | 0.00 |
| later turns | 3719 | 35.2 | 33.7 | -1.5 | 0.52 | 0.37 | 0.00 | 0.03 |
| round 0 | 600 | 33.7 | 31.4 | -2.3 | 0.65 | 0.25 | 0.00 | 0.00 |
| round 1 | 1800 | 34.8 | 31.6 | -3.2 | 0.65 | 0.26 | 0.00 | 0.04 |
| round 2 | 1392 | 36.7 | 36.6 | -0.1 | 0.46 | 0.43 | 0.00 | 0.00 |
| round 3 | 1175 | 34.9 | 34.4 | -0.5 | 0.43 | 0.44 | 0.01 | 0.02 |

Per-setup mean difference (swapped − recorded): median -1.4 words, swapped shorter in 90/90 setups.

## gemma batch→online (multi-private-stepped): 4998 states from 90 games (source multi-private-stepped)

| position | n | words batch (recorded) | words online (swapped) | diff | share shorter | share longer | pass batch (recorded) | pass online (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4998 | 16.1 | 27.4 | +11.3 | 0.00 | 0.94 | 0.14 | 0.05 |
| period turn 1 | 1252 | 19.9 | 29.6 | +9.8 | 0.01 | 0.98 | 0.00 | 0.00 |
| later turns | 3746 | 14.8 | 26.7 | +11.9 | 0.00 | 0.93 | 0.19 | 0.06 |
| round 0 | 600 | 12.4 | 25.4 | +13.0 | 0.00 | 0.97 | 0.18 | 0.02 |
| round 1 | 1795 | 14.4 | 27.3 | +13.0 | 0.00 | 0.94 | 0.20 | 0.06 |
| round 2 | 1408 | 18.2 | 28.5 | +10.3 | 0.00 | 0.94 | 0.08 | 0.05 |
| round 3 | 1195 | 18.1 | 27.3 | +9.3 | 0.01 | 0.94 | 0.10 | 0.04 |

Per-setup mean difference (swapped − recorded): median +11.8 words, swapped shorter in 0/90 setups.

## gemma batch→online (multi-private-stepped-process): 4992 states from 90 games (source multi-private-stepped)

| position | n | words batch (recorded) | words online (swapped) | diff | share shorter | share longer | pass batch (recorded) | pass online (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4992 | 20.9 | 29.7 | +8.8 | 0.01 | 0.94 | 0.08 | 0.04 |
| period turn 1 | 1248 | 23.7 | 31.8 | +8.0 | 0.01 | 0.98 | 0.00 | 0.00 |
| later turns | 3744 | 19.9 | 29.0 | +9.0 | 0.01 | 0.93 | 0.11 | 0.05 |
| round 0 | 600 | 20.4 | 29.7 | +9.4 | 0.01 | 0.98 | 0.01 | 0.00 |
| round 1 | 1800 | 20.0 | 29.8 | +9.8 | 0.01 | 0.95 | 0.10 | 0.04 |
| round 2 | 1392 | 21.6 | 30.2 | +8.6 | 0.01 | 0.93 | 0.10 | 0.05 |
| round 3 | 1200 | 21.6 | 28.9 | +7.2 | 0.02 | 0.92 | 0.09 | 0.04 |

Per-setup mean difference (swapped − recorded): median +8.9 words, swapped shorter in 0/90 setups.

