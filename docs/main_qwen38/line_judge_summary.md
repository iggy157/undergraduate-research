# Line judge (v2 items), qwen

Each line judged alone in its context (the transcript so far with ids, the line last) with the five items of ANNOTATION_INSTRUCTIONS_v2, blind to how it was produced. Rater Llama 3.3 70B unless noted.

## A. Goal swap: the same state, two goals

| history | goal | n | words | content / line | content / 100 words | padded | responsive | rebuttal | named questions | answered rate |
|---|---|---|---|---|---|---|---|---|---|---|
| short (multi-batch game) | batch (recorded) | 4929 | 12.0 | 0.71 | 5.9 | 0.02 | 0.60 | 0.07 | 107 | 0.71 |
| short (multi-batch game) | online (swapped) | 4929 | 15.6 | 0.79 | 5.1 | 0.04 | 0.72 | 0.14 | 107 | 0.84 |
| long (multi-online game) | batch (swapped) | 4930 | 21.3 | 0.68 | 3.2 | 0.05 | 0.80 | 0.18 | 255 | 0.32 |
| long (multi-online game) | online (recorded) | 4930 | 21.5 | 0.72 | 3.3 | 0.05 | 0.83 | 0.23 | 255 | 0.37 |

- short (multi-batch game): content per 100 words, batch − online per setup: median +1.01, batch higher in 76/90 setups.
- long (multi-online game): content per 100 words, batch − online per setup: median -0.16, batch higher in 20/90 setups.

## B. Agreement

Llama vs gpt-oss on 1531 shared lines: κ content 0.14, padded 0.10, resp 0.69, rebut 0.65.
  - Llama, batch: content / 100 words 4.8, padded 0.03 (n 766)
  - gpt-oss, batch: content / 100 words 8.6, padded 0.29 (n 766)
  - Llama, online: content / 100 words 4.6, padded 0.05 (n 765)
  - gpt-oss, online: content / 100 words 8.3, padded 0.31 (n 765)

Line protocol vs whole-transcript annotation (Llama, the same recorded lines, n 9704): κ content 0.58, padded 0.26, resp 0.64; mean content 0.73 vs 0.81, padded 0.04 vs 0.04.
