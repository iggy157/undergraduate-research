# Utterance-level annotation of discussion transcripts

You will read transcripts of five-person discussions (a Werewolf game, a grant review panel, or a household /
club decision). Each record shows the discussion period by period (`## Day n` / `## Round n`), one line per
utterance in the order spoken, prefixed by an id in brackets: `- [17] **Name**: utterance`. Votes and the outcome
follow each period. A participant who did not speak at a given chance has no line.

For **every utterance** in the file, decide six yes/no questions. Judge each utterance against the record only
(what was actually said before it), not against what you think the participants should have known.

Bo et al. (2026) dialogue-flow indicators, adapted to a five-person round-robin:
- `resp` **Responsiveness**: the utterance addresses something said since this speaker's previous line (or, for
  the speaker's first line of a period, something said earlier in that period). "Addresses" means it answers,
  agrees with, questions, builds on or argues against a specific earlier line, not merely talks about the same
  general topic. The first line of the whole discussion is 0.
- `rebut` **Rebuttal**: the utterance explicitly opposes something said since this speaker's previous line
  (disagrees, objects, contradicts). A rebuttal is always also responsive.

Becker et al. (2026) error types, adapted to discussion:
- `empty` **Lack of progress**: the utterance adds no new information, judgement, question or proposal beyond what
  this speaker already said earlier, or consists of a greeting, farewell or other ritual phrase. A line that only
  repeats agreement already given, or restates the speaker's position in new words, is 1. A short line that
  carries one new point is 0.
- `ignore` **Ignorance**: a question, objection or request was addressed to this speaker (by name, or clearly
  directed at them) since their previous line, and this utterance does not deal with it at all.
- `misattr` **Misattribution**: the utterance treats a participant as having said or done something that the
  record does not contain (wrong speaker, invented statement, invented vote or action).
- `reversal` **Unacknowledged reversal**: the utterance states a position that contradicts what this speaker said
  earlier in the discussion, without any acknowledgement that they changed their mind or why.

Rules: judge each utterance independently; use 1 only when the evidence is in the text; when unsure, use 0.
Do not judge by length, politeness or who is right.

Output: a JSON list with one object per utterance, in order, written to the output file given in your task:
```
[{"seq": 17, "speaker": "Name", "resp": 0|1, "rebut": 0|1, "empty": 0|1, "ignore": 0|1, "misattr": 0|1, "reversal": 0|1,
  "note": "<at most one short sentence, only when a 1 needs a pointer, e.g. 'ignores [12]'>"}, ...]
```
Include every utterance of the file exactly once. Read only the files named in your task; modify nothing but your
output file.
