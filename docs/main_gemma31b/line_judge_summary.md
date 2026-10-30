# Line judge (v2 items), gemma

Each line judged alone in its context (the transcript so far with ids, the line last) with the five items of ANNOTATION_INSTRUCTIONS_v2, blind to how it was produced. Rater Llama 3.3 70B unless noted.

## A. Goal swap: the same state, two goals

| history | goal | n | words | content / line | content / 100 words | padded | responsive | rebuttal | named questions | answered rate |
|---|---|---|---|---|---|---|---|---|---|---|
| short (multi-batch game) | batch (recorded) | 4947 | 16.1 | 0.71 | 4.4 | 0.05 | 0.63 | 0.14 | 144 | 0.51 |
| short (multi-batch game) | online (swapped) | 4947 | 27.4 | 0.85 | 3.1 | 0.09 | 0.77 | 0.18 | 144 | 0.55 |
| long (multi-online game) | batch (swapped) | 4954 | 31.2 | 0.76 | 2.5 | 0.09 | 0.77 | 0.15 | 438 | 0.29 |
| long (multi-online game) | online (recorded) | 4954 | 33.7 | 0.77 | 2.3 | 0.11 | 0.83 | 0.18 | 438 | 0.26 |

- short (multi-batch game): content per 100 words, batch − online per setup: median +1.30, batch higher in 90/90 setups.
- long (multi-online game): content per 100 words, batch − online per setup: median +0.16, batch higher in 74/90 setups.

## B. Agreement

Llama vs gpt-oss on 1928 shared lines: κ content 0.11, padded 0.22, resp 0.68, rebut 0.69.
  - Llama, batch: content / 100 words 3.2, padded 0.08 (n 785)
  - gpt-oss, batch: content / 100 words 6.0, padded 0.36 (n 785)
  - Llama, online: content / 100 words 2.8, padded 0.10 (n 786)
  - gpt-oss, online: content / 100 words 5.1, padded 0.35 (n 786)

Line protocol vs whole-transcript annotation (Llama, the same recorded lines, n 9177): κ content 0.56, padded 0.40, resp 0.53; mean content 0.80 vs 0.86, padded 0.08 vs 0.06.

## C. Steering pilots (gemma)

| layer | variant | n | words | content / line | padded | broken |
|---|---|---|---|---|---|---|
| 20 | batch | 15 | 13.5 | 0.60 | 0.00 | 0.00 |
| 20 | online+0v | 15 | 25.3 | 0.80 | 0.07 | 0.00 |
| 20 | online+1v | 15 | 25.3 | 0.73 | 0.07 | 0.00 |
| 20 | online+2v | 15 | 25.5 | 0.73 | 0.07 | 0.00 |
| 20 | online+4v | 15 | 26.9 | 0.73 | 0.13 | 0.00 |
| 20 | online+rand | 15 | 23.4 | 0.73 | 0.00 | 0.00 |
| 40 | batch | 30 | 14.0 | 0.73 | 0.03 | 0.00 |
| 40 | online+0.5v | 30 | 26.3 | 0.80 | 0.07 | 0.00 |
| 40 | online+0v | 30 | 26.6 | 0.83 | 0.10 | 0.00 |
| 40 | online+1.5v | 30 | 28.0 | 0.77 | 0.10 | 0.00 |
| 40 | online+1v | 30 | 26.7 | 0.73 | 0.17 | 0.00 |
| 40 | online+rand | 30 | 1.0 | 0.00 | 1.00 | 1.00 |
| 52 | batch | 15 | 13.5 | 0.67 | 0.00 | 0.00 |
| 52 | online+0v | 15 | 25.3 | 0.80 | 0.07 | 0.00 |
| 52 | online+1v | 15 | 24.4 | 0.73 | 0.07 | 0.00 |
| 52 | online+2v | 15 | 26.5 | 0.80 | 0.07 | 0.00 |
| 52 | online+4v | 15 | 113.2 | 0.07 | 0.93 | 0.87 |
| 52 | online+rand | 15 | 1.0 | 0.00 | 1.00 | 1.00 |
