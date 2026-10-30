# Length probe on identical histories: qwen (10008 states)

Each state is the same game state under both framings; y = words of the line that framing produced (recorded or re-generated, scripts/goal_swap.py). Ridge, grouped 5-fold by setup, nested penalty. `base` = round and turn only. R^2 (r).

## All states

| framing | mean words | sd | base | gen L20 | gen L32 | gen L48 | gen L52 | label L20 | label L32 | label L48 | label L52 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| online | 18.5 | 5.3 | 0.07 | 0.60 (0.78) | 0.64 (0.80) | 0.68 (0.82) | 0.68 (0.83) | 0.66 (0.81) | 0.65 (0.81) | 0.62 (0.79) | 0.59 (0.77) |
| batch | 16.6 | 6.5 | 0.08 | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) |

## By history (same predictions, scored within each subset; best layer of each position)

| history | framing | n | mean words | sd | gen: best R^2 (r) | label: best R^2 (r) |
|---|---|---|---|---|---|---|
| long (multi-online game) | online | 4996 | 21.5 | 4.2 | 0.45 (0.67) L52 | 0.41 (0.64) L20 |
| long (multi-online game) | batch | 4996 | 21.3 | 4.9 | 0.60 (0.77) L48 | 0.60 (0.77) L48 |
| short (multi-batch game) | online | 5012 | 15.6 | 4.7 | 0.61 (0.78) L52 | 0.58 (0.76) L20 |
| short (multi-batch game) | batch | 5012 | 12.0 | 4.2 | 0.74 (0.86) L20 | 0.74 (0.86) L20 |
