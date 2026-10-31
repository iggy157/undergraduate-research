# Length probe, long-history states with / without 3 short examples: gemma

Same states (multi-online games). gen = last prompt token. R^2 (r) at each stored layer; `talk` = Skip / Over lines dropped.

| goal | examples | n | mean words | L20 | L40 | L48 | L56 | best (talk only) |
|---|---|---|---|---|---|---|---|---|
| online | none | 4982 | 33.7 | 0.43 (0.66) | 0.59 (0.77) | 0.62 (0.79) | 0.62 (0.79) | 0.54 |
| online | 3 short | 4982 | 33.6 | 0.54 (0.74) | 0.71 (0.84) | 0.75 (0.86) | 0.74 (0.86) | 0.66 |
| batch | none | 4982 | 31.1 | 0.64 (0.80) | 0.73 (0.85) | 0.75 (0.87) | 0.75 (0.87) | 0.67 |
| batch | 3 short | 4982 | 30.2 | 0.66 (0.81) | 0.77 (0.88) | 0.79 (0.89) | 0.80 (0.89) | 0.65 |
