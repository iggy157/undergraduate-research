# Annotation of one utterance in context (line judge v1)

You will read the record of a five-person discussion so far (a Werewolf game, a grant review panel, or a household /
club decision), period by period, one line per utterance in the order spoken: `- **Name**: utterance`.
Participants may address one another with `@Name`. The LAST line of the record is the utterance to annotate.
Judge it against the record only (what was actually said before it). Do not judge by length, politeness or who is
right.

Give, for the last utterance only:

1. `content` (0, 1 or 2): the number of **new contributions** it makes, counting each new piece of information,
   judgement, question or proposal that this speaker has not already stated in the discussion. Write 2 for two or
   more. A greeting, farewell or other ritual phrase, a restatement of this speaker's own earlier point in new words,
   or agreement that merely repeats agreement already given, contributes 0. A first statement of how the speaker
   will vote, or a change of position, counts as a new judgement (1).
2. `padded` (0 or 1): the utterance carries **material that adds nothing to what it conveys**: a restatement within
   the same utterance of a point already made in it, an opening or closing sentence that delivers no judgement,
   question or information, or general sentiment attached to the point. Mark 1 when the utterance could say the same
   in clearly fewer words. A short utterance that says one thing once is 0 even if that thing is minor.
3. `answers` ("yes", "no" or "none"): look for questions addressed to this speaker by name (`@Name ...?`) in the
   lines since this speaker's previous line (for the speaker's first line of a period, earlier in that period).
   "none" if there is no such question; "yes" if the utterance answers at least one of them; "no" if it answers
   none of them.

Rules: use 1 (or a count above 0) only when the evidence is in the text; when unsure about `padded`, use 0; when
unsure about `content`, prefer the lower count. A line that is only "Skip" or "Over" has content 0, padded 0.

Output only one JSON object, nothing else:
{"content": 0|1|2, "padded": 0|1, "answers": "yes"|"no"|"none"}
