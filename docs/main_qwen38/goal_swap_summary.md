# Goal swap on identical histories (scripts/goal_swap.py)

The same recorded game state (system prompt + transcript so far + the seat's label) is given to the model under the other generation goal: online = the state as the user message (next line only); batch = the single-batch writing request as the user message and the transcript continued as the model's own output. Greedy, the seat's stop strings. words = whitespace tokens (0 for Skip / Over).

## qwen online→batch (multi-private): 4996 states from 90 games (source multi-private)

| position | n | words online (recorded) | words batch (swapped) | diff | share shorter | share longer | pass online (recorded) | pass batch (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4996 | 21.5 | 21.3 | -0.2 | 0.45 | 0.42 | 0.01 | 0.01 |
| period turn 1 | 1249 | 21.3 | 21.2 | -0.1 | 0.46 | 0.44 | 0.00 | 0.00 |
| later turns | 3747 | 21.6 | 21.4 | -0.2 | 0.44 | 0.41 | 0.01 | 0.01 |
| round 0 | 600 | 18.0 | 16.6 | -1.4 | 0.57 | 0.30 | 0.01 | 0.01 |
| round 1 | 1800 | 20.7 | 20.0 | -0.7 | 0.47 | 0.38 | 0.01 | 0.01 |
| round 2 | 1396 | 22.9 | 23.5 | +0.6 | 0.39 | 0.49 | 0.00 | 0.00 |
| round 3 | 1200 | 23.0 | 23.2 | +0.2 | 0.41 | 0.43 | 0.00 | 0.00 |

Per-setup mean difference (swapped − recorded): median -0.3 words, swapped shorter in 61/90 setups.

## qwen batch→online (multi-private-stepped): 5012 states from 90 games (source multi-private-stepped)

| position | n | words batch (recorded) | words online (swapped) | diff | share shorter | share longer | pass batch (recorded) | pass online (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 5012 | 12.0 | 15.6 | +3.6 | 0.10 | 0.79 | 0.03 | 0.03 |
| period turn 1 | 1253 | 13.0 | 17.2 | +4.2 | 0.10 | 0.83 | 0.00 | 0.00 |
| later turns | 3759 | 11.6 | 15.0 | +3.4 | 0.10 | 0.77 | 0.04 | 0.04 |
| round 0 | 600 | 9.2 | 13.3 | +4.1 | 0.06 | 0.87 | 0.03 | 0.02 |
| round 1 | 1800 | 11.2 | 15.4 | +4.2 | 0.08 | 0.83 | 0.03 | 0.02 |
| round 2 | 1400 | 13.0 | 16.4 | +3.5 | 0.10 | 0.79 | 0.03 | 0.03 |
| round 3 | 1212 | 13.4 | 16.0 | +2.6 | 0.16 | 0.67 | 0.04 | 0.03 |

Per-setup mean difference (swapped − recorded): median +3.6 words, swapped shorter in 0/90 setups.

