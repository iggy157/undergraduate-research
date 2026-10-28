# Pairwise judgement: which transcript reads more like real people discussing the matter?

You will read pairs of transcripts. The two transcripts of a pair are records of the same five-person discussion
setting (same matter to decide, same participants and personalities, same hidden roles or private findings), produced
in different ways. Each record shows the discussion period by period (`## Day n` / `## Round n`), one line per
utterance in the order spoken (`- **Name**: utterance`), the votes at the end of a period (`### Vote`) and the
outcome (`## Result`). Participants have several chances to speak in each period; a participant who did not speak at
a given chance has no line there. Utterances are limited to 40 words by the rules of the session in both transcripts.

Question (answer it for each pair): **Which of the two reads more like real people discussing this matter and
working their way to the decision they have to make?**

Judge the record as a conversation among people with a task: whether what is said responds to what was said before
and carries the discussion towards the decision, whether the pace reads like people talking, whether the participants
come across as distinct people who stay themselves.

Do **not** judge by length or by how much is said: a longer or more detailed transcript is not more human for that
reason, and a shorter one is not less human for that reason. Do not judge by the quality or correctness of the final
decision, by politeness, or by how well the game was played.

For each pair, answer with exactly one of `A`, `B`, `Tie`, then explain the judgement in 3–6 sentences pointing to
concrete places in the transcripts (period / speaker). Write the explanation before you settle on the answer if that
helps, but report only the final answer.

Output: one JSON object per pair, written together as a JSON list to the output file given in your task:
```
[{"pair": "<file name without _o1/_o2.md, e.g. aiwolf_0001__C1>", "verdict": "A" | "B" | "Tie",
  "reasons": "<3-6 sentences>",
  "cues": ["<short tag>", ...]   // the kinds of evidence you used, in your own words
 }, ...]
```
Read only the files named in your task. Do not look for other files in the directory or elsewhere; do not modify
any file other than your output file.
