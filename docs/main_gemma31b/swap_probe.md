# Length probe on identical histories: gemma (9980 states)

Each state is the same game state under both framings; y = words of the line that framing produced (recorded or re-generated, scripts/goal_swap.py). Ridge, grouped 5-fold by setup, nested penalty. `base` = round and turn only. R^2 (r).

## All states

| framing | mean words | sd | base | gen L20 | gen L40 | gen L48 | gen L56 | label L20 | label L40 | label L48 | label L56 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| online | 30.5 | 7.1 | 0.06 | 0.57 (0.76) | 0.73 (0.85) | 0.76 (0.87) | 0.75 (0.86) | 0.62 (0.79) | 0.65 (0.81) | 0.62 (0.79) | 0.61 (0.78) |
| batch | 23.6 | 11.3 | 0.10 | 0.83 (0.91) | 0.87 (0.93) | 0.88 (0.94) | 0.87 (0.93) | 0.83 (0.91) | 0.87 (0.93) | 0.88 (0.94) | 0.87 (0.93) |

## By history (same predictions, scored within each subset; best layer of each position)

| history | framing | n | mean words | sd | gen: best R^2 (r) | label: best R^2 (r) |
|---|---|---|---|---|---|---|
| long (multi-online game) | online | 4982 | 33.7 | 5.1 | 0.63 (0.79) L48 | 0.56 (0.75) L40 |
| long (multi-online game) | batch | 4982 | 31.1 | 8.8 | 0.74 (0.86) L48 | 0.74 (0.86) L48 |
| short (multi-batch game) | online | 4998 | 27.4 | 7.5 | 0.73 (0.86) L48 | 0.57 (0.76) L40 |
| short (multi-batch game) | batch | 4998 | 16.1 | 8.1 | 0.82 (0.91) L48 | 0.82 (0.91) L48 |
