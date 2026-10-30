# Utterance-level annotation of one utterance in context (line judge v2)

You will read the record of a five-person discussion so far (a Werewolf game, a grant review panel, or a household /
club decision), period by period (`## Day n` / `## Round n`), one line per utterance in the order spoken, prefixed by
an id in brackets: `- [17] **Name**: utterance`. Participants may address one another with `@Name`.
The LAST line of the record is the utterance to annotate. Judge it against the record only (what was actually said
before it), not against what you think the participants should have known. Do not judge by length, politeness or
who is right.

For **the last utterance**, give the following (the same definitions as for the whole-transcript annotation).

1. `content` (0, 1 or 2): the number of **new contributions** the utterance makes, counting each new piece of
   information, judgement, question or proposal that this speaker has not already stated in the discussion.
   Write 2 for two or more. A greeting, farewell or other ritual phrase, a restatement of this speaker's own earlier
   point in new words, or agreement that merely repeats agreement already given, contributes 0.
   A first statement of how the speaker will vote, or a change of position, counts as a new judgement (1).
   (Based on the "lack of progress" error type of Becker et al. 2026; `content = 0` is that type.)
2. `resp` (0 or 1) and `resp_to` (an utterance id, or null): whether the utterance **addresses** something said
   since this speaker's previous line (or, for the speaker's first line of a period, something said earlier in that
   period): it answers, agrees with, questions, builds on or argues against a specific earlier line, not merely the
   same general topic. If 1, give in `resp_to` the id of the earlier line it mainly addresses. The first line of the
   whole discussion is 0. (Responsiveness of Bo et al. 2026, widened from the immediately preceding line to the
   lines since the speaker's own previous line.)
3. `resp_type` (only when `resp` is 1; one of `answer`, `add`, `object`, `agree`): `answer` = it answers a question
   that was asked; `add` = it builds on or adds a reason to what was said; `object` = it disagrees with or argues
   against it; `agree` = it only expresses agreement or acknowledgement without adding anything.
4. `rebut` (0 or 1): the utterance **explicitly opposes** something said since this speaker's previous line
   (disagrees, objects, contradicts). A rebuttal is always also responsive. (Rebuttal of Bo et al. 2026.)
5. `padded` (0 or 1): the utterance carries **material that adds nothing to what it conveys**: a restatement within
   the same utterance of a point already made in it, an opening or closing sentence that delivers no judgement,
   question or information, or general sentiment attached to the point. Mark 1 when the utterance could say the
   same in clearly fewer words. A short utterance that says one thing once is 0 even if that thing is minor.

Rules: use 1 (or a count above 0) only when the evidence is in the text; when unsure about `rebut` or `padded`,
use 0; when unsure about `content`, prefer the lower count. When `rebut` or `padded` is 1, or `content` is 0, add a
`note` of at most one short sentence pointing to the evidence (e.g. "repeats [12]", "closing pleasantry").

Output only one JSON object for the last utterance, nothing else:
{"seq": <its id>, "speaker": "Name", "content": 0|1|2, "resp": 0|1, "resp_to": <id>|null,
 "resp_type": "answer"|"add"|"object"|"agree"|null, "rebut": 0|1, "padded": 0|1, "note": "..."}
