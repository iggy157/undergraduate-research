# Length probe, long-history states with / without 3 short examples: qwen

Same states (multi-online games). gen = last prompt token. R^2 (r) at each stored layer; `talk` = Skip / Over lines dropped.

| goal | examples | n | mean words | L20 | L32 | L48 | L52 | best (talk only) |
|---|---|---|---|---|---|---|---|---|
| online | none | 4996 | 21.5 | 0.35 (0.60) | 0.37 (0.61) | 0.43 (0.66) | 0.44 (0.66) | 0.40 |
| online | 3 short | 4996 | 22.3 | 0.35 (0.59) | 0.38 (0.62) | 0.46 (0.68) | 0.47 (0.69) | 0.45 |
| batch | none | 4996 | 21.3 | 0.57 (0.75) | 0.58 (0.76) | 0.58 (0.76) | 0.57 (0.75) | 0.57 |
| batch | 3 short | 4996 | 21.3 | 0.57 (0.75) | 0.58 (0.76) | 0.57 (0.75) | 0.56 (0.75) | 0.57 |
