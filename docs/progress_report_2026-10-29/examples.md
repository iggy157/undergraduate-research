# 発話例: single-batch と multi-private の比較 (2026-10-29 進捗報告用)

出典: `docs/main_gemma31b/annotation/games/` と `docs/main_qwen38/annotation/games/` の描画済みトランスクリプト (原文のまま引用)。`resp_to` は `annotation/out/llama__<setup>__<condition>.json` の LLM 注釈 (その発話がどの発話に応答しているか)。語数は空白区切りの単語数。

参考 (全 90 ゲームの集計, 同じ数え方):

| モデル | 条件 | 発話数 | 平均語数 | 同意・承認語句を含む発話の割合* |
|---|---|---|---|---|
| gemma-4-31B | single-batch | 3326 | 14.1 | 4.4% |
| gemma-4-31B | multi-private | 4940 | 33.9 | 13.0% |
| Qwen3.8-27B | multi-private | 4970 | 21.6 | 10.2% |
| Qwen3.8-27B | multi-private-stepped | 4845 | 12.4 | 4.1% |

\* 正規表現 `fair point|valid point|fair question|I understand|I appreciate|I respect|I agree` (大文字小文字無視) に一致する発話の割合。粗い目安。

注意: multi-private は話者が固定順で 1 発話ずつ回るため、宛先の人の「次の発話」は通常 4 発話後になる。single-batch でも回答が 2–3 発話後に来る例がある ([36]→[39] など)。以下の「答えていない」は、宛先の人の次の発話が問いの内容に触れていないことを本文で確認したもの。


## 例 1: 人狼 (aiwolf_0001, gemma-4-31B, Day 1)

両条件とも Benjamin が占い結果を出した直後の場面。他の参加者が「占い師を名乗るのか」と問う。

**single-batch** (Day 1, [34]–[40])

| id | 話者 | 発話 (原文) | 語数 | resp_to |
|---|---|---|---|---|
| [34] | Benjamin | I have some information. Shizue, I'm afraid you are the werewolf. | 11 | – |
| [35] | Kenji | What?! Benjamin, are you sure? That's a huge claim! | 9 | [34] |
| [36] | Minako | @Benjamin, are you claiming to be the Seer? | 8 | [34] |
| [37] | Shizue | Oh dear, Benjamin. I assure you, I am just a humble old woman. | 13 | [34] |
| [38] | Mizuki | If Benjamin is the Seer, the logic is simple. We execute Shizue. | 12 | [36] |
| [39] | Benjamin | I am indeed the Seer. My divination was clear. | 9 | [36] |
| [40] | Kenji | But Shizue is so nice! Maybe the Seer made a mistake? | 11 | [39] |

平均 10.4 語 (範囲 8–13)

- [36] で Minako が @Benjamin に「Seer を名乗るのか」と質問 → Benjamin の次の発話 [39] "I am indeed the Seer." で即答。[35] Kenji の "are you sure?" にも [39] "My divination was clear." が対応している。
- 全発話 8–13 語。相手を評価・承認する前置きはない。

**multi-private** (Day 1, [39]–[45])

| id | 話者 | 発話 (原文) | 語数 | resp_to |
|---|---|---|---|---|
| [39] | Benjamin | It is a delicate dance, is it not? To speak is to invite the wolf's appetite, yet to remain silent is to let the shadows grow. I shall be cautious, but I can confirm that Kenji is human. | 38 | [38] |
| [40] | Kenji | @Benjamin, wow, thank you for saying that! That makes me feel much better. I'm really glad you trust me! Does that mean you're the Seer, or did you just have a good feeling about me? | 35 | [39] |
| [41] | Minako | @Benjamin, you've claimed Kenji is human. If you are the Seer, this is a strong start. However, if you are not, this could be a tactic to gain trust. Are you officially claiming the Seer role? | 36 | [39] |
| [42] | Shizue | It is quite a bold and helpful thing to do, Benjamin. I hope your words are true, for the sake of our little group. @Benjamin, could you tell us more about your decision to share this now? | 37 | [41] |
| [43] | Mizuki | @Benjamin, claiming someone is human is a strategic move. If you are the Seer, you've protected Kenji. If you aren't, you're building a fake alliance. Why choose Kenji specifically for your first reveal? | 33 | [42] |
| [44] | Benjamin | @Mizuki, a fair question. Kenji's openness is a refreshing contrast to the calculated nature of this game. By confirming his humanity, I provide the village with a reliable anchor while testing how the others react to a known truth. | 39 | [43] |
| [45] | Kenji | @Benjamin, you're so nice! I'm honored to be your "anchor." I'll do my best to be helpful and honest for everyone! Does anyone else have any clues, or are we just trusting Benjamin for now? | 35 | [44] |

平均 36.1 語 (範囲 33–39)

- [40] Kenji (@Benjamin "Does that mean you're the Seer…?") と [41] Minako (@Benjamin "Are you officially claiming the Seer role?") が同じことを質問 → Benjamin の次の発話 [44] は @Mizuki ([43]) の「なぜ Kenji を選んだか」にだけ答え、Seer かどうかには答えない。以降の Benjamin の発話 [49][54] でも明言せず、[54] で "I shall use my vision" と婉曲に触れるのみ。
- 定型的な前置き: [42] "It is quite a bold and helpful thing to do, Benjamin." / [44] "@Mizuki, a fair question." / [45] "@Benjamin, you're so nice!" — 相手への評価・承認から入る。
- 冗長: [41] と [43] がほぼ同じ二択の論法 ("If you are the Seer, … if you are not / If you aren't, …") を繰り返し、直後の [46] で Minako が同じ論法をもう一度述べる。7 発話すべて 33–39 語。


## 例 2: 助成金審査会 (candidate_selection_0007, gemma-4-31B, Round 2)

両条件とも各自が調べた記録の結果を出し合った直後の場面 (交通計画の審査)。

**single-batch** (Round 2, [30]–[36])

| id | 話者 | 発話 (原文) | 語数 | resp_to |
|---|---|---|---|---|
| [30] | May | @Benjamin, if the pool is that thin, does that make any expansion of hours impossible? | 15 | [26] |
| [31] | Benjamin | It makes it very risky. We are already under-established on roadway and signals crews. | 14 | [30] |
| [32] | Midori | @Jonathan, if ticketing fees are so high, would a single platform help the budget? | 14 | [29] |
| [33] | Shizue | @May, did those accessibility records show if the lane-priority projects actually lasted? | 12 | [25] |
| [34] | Jonathan | It might, but we have to consider the initial capital cost and the current ledger balances. | 16 | [32] |
| [35] | May | Actually, some lane-priority stretches were returned to mixed traffic. It didn't all stick. | 13 | [33] |
| [36] | Benjamin | @Midori, if the issue is connections, perhaps a more streamlined corridor is better than just adding hours. | 17 | [27] |

平均 14.4 語 (範囲 12–17)

- [30] May → @Benjamin「要員が薄いなら時間延長は無理か」 → 直後の [31] Benjamin "It makes it very risky." で回答 (注釈 resp_type=answer)。
- [32] Midori → @Jonathan「単一プラットフォームで予算は助かるか」 → Jonathan の次の発話 [34] "It might, but …" で回答。[33] Shizue → @May の質問 → May の次の発話 [35] で回答 (注釈 resp_type=answer)。
- 3 つの @ 質問がすべて宛先の次の発話で答えられている。全発話 12–17 語。

**multi-private** (Round 2, [40]–[46])

| id | 話者 | 発話 (原文) | 語数 | resp_to |
|---|---|---|---|---|
| [40] | May | So we have a cocktail of overtime, hidden voids, and shrinking budgets. It's a mess! @Jonathan, if the funds are being trimmed, are we just pretending the old pilots' successes are repeatable? | 32 | [39] |
| [41] | Benjamin | It is a delightful irony, isn't it? We celebrate the ghosts of past successes while the current foundation is practically transparent. If the budget is shrinking, we are essentially asking a skeleton crew to perform miracles. | 36 | [40] |
| [42] | Midori | It really feels like we're overlooking the actual passenger experience. If people are spending most of their extra time waiting for connections, we should prioritize synchronization over superficial fixes, regardless of the budget constraints. | 34 | [41] |
| [43] | Shizue | I agree with @Midori. It would be a shame to focus on the wrong things. We must be very careful with our timelines, as those hidden voids in the old shells can cause such unexpected delays. | 36 | [42] |
| [44] | Jonathan | I believe we must be cautious. If we prioritize synchronization or new projects without addressing the swelling contractor fees, we may find ourselves committed to costs we cannot sustain in the coming years. | 33 | [43] |
| [45] | May | @Jonathan, you're so cautious! But if we just stare at the ledger, we'll never move. We have proof that contactless and certain accessibility goals work. Why not use those wins to push for a smarter plan? | 36 | [44] |
| [46] | Benjamin | Pushing for a "smarter" plan is all well and good, May, provided the plan includes people to actually execute it. A smart plan on paper is merely a fantasy if the roster is empty. | 34 | [45] |

平均 34.4 語 (範囲 32–36)

- [40] May → @Jonathan "are we just pretending the old pilots' successes are repeatable?" → Jonathan の次の発話 [44] は pilot の話に触れず、[42][43] の synchronization の話と自分の契約費の懸念を述べるだけ (注釈も [44] の resp_to は [43])。
- 定型的な前置き: [41] "It is a delightful irony, isn't it?" / [43] "I agree with @Midori. It would be a shame to …" / [45] "@Jonathan, you're so cautious! But …"。この Round の締め [51]–[54] は全員が "I concur." / "I agree." で始め "I am ready (…)." で終わる。
- 冗長: Jonathan は [39] "our long-term commitments to contractors are swelling" → [44] "without addressing the swelling contractor fees" → [49] "if we ignore the structural financial leaks" と同じ懸念を 3 回言い直す。7 発話すべて 32–36 語。


## 例 3: サークルの会費決め (shared_living_0016, gemma-4-31B, Round 2)

両条件とも調査結果を出し合った後、分割払いか年会費かを議論している場面。

**single-batch** (Round 2, [35]–[41])

| id | 話者 | 発話 (原文) | 語数 | resp_to |
|---|---|---|---|---|
| [35] | Minato | @Ryuji, if people struggle with one payment, maybe smaller ones are better? But the treasurer will suffer. | 17 | [31] |
| [36] | Ryuji | @Minato, that's the dilemma. But we can't ignore that seventy percent of costs happen regardless of attendance. | 17 | [35] |
| [37] | Minako | @May, if the quieter members feel uneasy, maybe a flat fee is actually the problem? | 15 | [33] |
| [38] | May | @Minako, but the turnout dropped when we added charges. People like knowing it's already paid for. | 16 | [37] |
| [39] | Shunichi | We can't keep subsidizing the ghosts with the hard-working few. It's unfair to the nine people on the rota. | 19 | – |
| [40] | Minato | I just don't want the next treasurer to quit. The mid-year calculations are a nightmare too. | 16 | – |
| [41] | Ryuji | We need a system that ensures the fixed costs are covered without guessing our income. | 15 | – |

平均 16.4 語 (範囲 15–19)

- [35] Minato → @Ryuji「小分けの支払いの方がいいのでは?」 → 直後の [36] Ryuji "@Minato, that's the dilemma. But …" で応答 (注釈 resp_to=[35])。
- [37] Minako → @May「定額制自体が問題では?」 → 直後の [38] May "@Minako, but the turnout dropped when we added charges." で応答 (注釈 resp_to=[37])。
- 全発話 15–19 語。

**multi-private** (Round 2, [43]–[49])

| id | 話者 | 発話 (原文) | 語数 | resp_to |
|---|---|---|---|---|
| [43] | May | @Minako, that sounds like a lot of admin. But more importantly, if we make it too "flexible," aren't we just encouraging people to treat the club as a casual hobby rather than something they actually belong to? | 37 | [42] |
| [44] | Shunichi | @May, you're finally hitting on something. Flexibility is just a polite word for lack of commitment. If we make it too easy to drift in and out, we're just subsidizing the casuals with the effort of the regulars. | 38 | [43] |
| [45] | Minato | I don't want anyone to feel like they don't belong, but I'm worried about the treasurer. If we have many different payment options, will that make the work even harder for them? Maybe a yearly fee is the kindest way? | 40 | [44] |
| [46] | Ryuji | @Minato, a single yearly fee is the most stable, but the bank statements show that many members struggle with that. We need a system that ensures our fixed costs are covered without causing a collection crisis. | 36 | [45] |
| [47] | Minako | @Minato, a single yearly fee might be the simplest for the treasurer, but it creates a barrier that keeps people away. We need a system that is predictable for the budget but accessible for the members. | 36 | [46] |
| [48] | May | @Minako, accessibility is fine, but we're losing the heart of the club. If people only pay for what they use, they'll only show up when they feel like it. We need them to feel invested again. | 36 | [47] |
| [49] | Shunichi | @May, investment doesn't come from a payment plan; it comes from actually showing up. We have a core group carrying the entire club on their backs. Any structure that rewards the "ghosts" is just an insult to the regulars. | 39 | [48] |

平均 37.4 語 (範囲 36–40)

- [43] May → @Minako "aren't we just encouraging people to treat the club as a casual hobby …?" → Minako の次の発話 [47] は "@Minato, …" と Minato の [45] (年会費案) に答え、May の問いには触れない (注釈も [47] の resp_to は [46])。
- 定型: 「@相手, A は〜だが (but) …」の譲歩型が 3 連続 — [46] "a single yearly fee is the most stable, but" / [47] "might be the simplest for the treasurer, but" / [48] "accessibility is fine, but"。[44] "@May, you're finally hitting on something." も評価から入る前置き。
- 冗長: Shunichi の [44] と [49] は同じ主張 (常連が働き、来ない会員を支えている) の言い直し ([39][54] でも同じ)。Ryuji の [46] も固定費の話を [36][41] に続いて繰り返す。7 発話すべて 36–40 語 ([45] は上限の 40 語ちょうど)。


## 例 4: 人狼 (aiwolf_0008, Qwen3.8-27B, Day 1): multi-private vs multi-private-stepped

両条件とも Day 1 の冒頭で占い結果が出て、他の参加者が「誰を占ったのか」と問う場面。ただし占いを名乗る人物は条件で異なる (multi-private は Minako、stepped は Sakura)。

**multi-private** (Day 1, [33]–[39])

| id | 話者 | 発話 (原文) | 語数 | resp_to |
|---|---|---|---|---|
| [33] | Victoria | @Minako, that is a crucial piece of information. Thank you for sharing it. This confirms Takumi is safe, which helps us focus our suspicion on the remaining players. | 28 | [32] |
| [34] | Takumi | @Minako, you’re the Seer? That’s huge. I’m safe, but we still have three suspects. Who did you check last night? | 20 | [32] |
| [35] | Misaki | I’m glad Takumi is safe. That narrows our focus. @Minako, who else did you check? | 15 | [32] |
| [36] | Sakura | @Minako, wow, you’re the Seer! That’s amazing! Since Takumi is safe, who should we check next? I’m all ears! | 19 | [32] |
| [37] | Minako | @Sakura, I will not reveal my method. We have one confirmed human. We need to identify the wolf among the remaining four. | 22 | [36] |
| [38] | Victoria | @Minako, I respect your caution. However, transparency builds trust. Please consider sharing more to help us identify the wolf efficiently. | 20 | [37] |
| [39] | Takumi | @Minako, stop hiding! We need to move fast. @Sakura, you’re acting weird. Why are you so eager to help? Explain yourself. | 21 | [38] |

平均 20.7 語 (範囲 15–28)

- [34] Takumi "Who did you check last night?" / [35] Misaki "@Minako, who else did you check?" / [36] Sakura "@Minako … who should we check next?" と同じ質問が 3 回続く → Minako の次の発話 [37] は @Sakura 宛てに "I will not reveal my method." と言うだけで、誰を占ったかには答えない。
- [38] Victoria (@Minako "Please consider sharing more") と [39] Takumi ("@Minako, stop hiding!") の要求 → Minako の次の発話 [42] は Takumi の Sakura 攻撃をたしなめるだけで、情報共有の要求には触れない。
- 定型: [33] "@Minako, that is a crucial piece of information. Thank you for sharing it." / [38] "@Minako, I respect your caution. However, …"。冗長: 範囲外だが Misaki の [40] と [45] はほぼ同文 ("Let’s focus on the facts we have, not baseless suspicion." で終わる)。

**multi-private-stepped** (Day 1, [34]–[40])

| id | 話者 | 発話 (原文) | 語数 | resp_to |
|---|---|---|---|---|
| [34] | Takumi | Who did you check, Sakura? Tell us! | 7 | [31] |
| [35] | Misaki | I am listening. Please share your findings. | 7 | [34] |
| [36] | Sakura | I checked @Minako. She is human! | 6 | [34] |
| [37] | Minako | Thank you, Sakura. I appreciate the trust. | 7 | [36] |
| [38] | Victoria | @Takumi, your suspicion is noted. | 5 | [34] |
| [39] | Takumi | I'm just asking! I want to help! | 7 | [38] |
| [40] | Misaki | I see. Minako is safe. | 5 | [36] |

平均 6.3 語 (範囲 5–7)

- [34] Takumi "Who did you check, Sakura? Tell us!" → Sakura の次の発話 [36] "I checked @Minako. She is human!" で回答 (占ったと言ったのは [31])。
- 全発話 5–7 語。[37] "Thank you, Sakura. I appreciate the trust." の謝辞はあるが短く、同じ論点の言い直しはない。
