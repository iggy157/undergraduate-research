# Steering pilots (gemma-4-31B, scripts/steer_goal2.py)

States: recorded multi-batch talk calls (held-out setups), framed online; the goal direction v = mean over 240 training states of h(batch framing, label colon) − h(online framing, label colon) at the given layer, added from the label position on. rand = a random direction with |v|. batch = the batch framing without steering (reference). broken = glued words, repetition or non-letter text.

## layer 40: 27 states

| variant | words | broken |
|---|---|---|
| online+0v | 26.6 | 0.00 |
| online+0.5v | 26.1 | 0.00 |
| online+1v | 26.3 | 0.00 |
| online+1.5v | 27.5 | 0.00 |
| online+rand | 1.0 | 1.00 |
| batch | 13.7 | 0.00 |

## layer 20: 13 states

| variant | words | broken |
|---|---|---|
| online+0v | 25.1 | 0.00 |
| online+1v | 25.1 | 0.00 |
| online+2v | 25.2 | 0.00 |
| online+4v | 26.9 | 0.00 |
| online+rand | 23.7 | 0.00 |
| batch | 12.7 | 0.00 |

## layer 52: 13 states

| variant | words | broken |
|---|---|---|
| online+0v | 25.1 | 0.00 |
| online+1v | 23.9 | 0.00 |
| online+2v | 25.6 | 0.00 |
| online+4v | 112.0 | 0.85 |
| online+rand | 1.0 | 1.00 |
| batch | 12.7 | 0.00 |

Version 1 (scripts/steer_goal.py, contrast at the last prompt token) is discarded: the last token differs between the framings, so the direction was a token-identity difference (it prepended a space at alpha 1 and broke the text at alpha 2 / −1).
