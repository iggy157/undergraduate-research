# 監査 C: 筋書き (plan) — 2026-10-28

対象: `common/scenario.py`, `scripts/gen_scenarios.py`, `scripts/prompts/scenario_request.jinja`, `common/prompts/scenario.jinja`,
`scenarios/*/*.json` + `.attempts.json` (9 本), DESIGN §13, paper_draft §3.4/§4, `log/_pilot5` の process 条件 18 局。
**注意**: 監査中 (04:29〜04:31 JST) に `scenario_request.jinja`・`common/scenario.py` (`_validate_prose` 強化)・DESIGN.md (L498) が
書き換えられた。本報告は 04:31 時点のコードと、03:25〜03:52 に生成された 9 本の筋書き、それで回した 18 局を対象にする。

## 結論 (3 行以内)

1. 現行 9 本の「process 筋書き」は結末も秘密も含んでいる (人狼 3/3 で占い師・人狼・狂人の名、議論 6/6 で選択肢名・ラベルか「leans/rejected/emerges」)。multi-private-process は事実上 multi-public 相当で、「計画の効果 / 未来情報の効果」の分離は pilot5 では成立していない (作者も L498 で認め再生成予定)。
2. 検証・修復・記録は方向は正しいが、人狼 3 本は生成後 (03:48) に修復が後付けされ attempts と最終ファイルが食い違う、process 粒度の乖離検出は期間数しか見ない、生成の記録に prompt と sampling が無い、という再現性の穴がある。
3. 「greedy で同じ筋書き」は根拠が無い (seed 無し、再生成の比較無し、DESIGN §14 自身が非決定性を認める)。再現性はファイルの sha1 で担保する方針に書き換えるべき。

## 発見した問題 (深刻度順)

| # | 深刻度 | 項目 | 証拠 | 影響 | 修正案 |
|---|---|---|---|---|---|
| 1 | Critical | process 筋書きが役職と結末を公開している | `scenarios/aiwolf/aiwolf_0001.json` period 1 public「Benjamin reveals his divination of Shizue as the Werewolf … the group leans toward Benjamin's evidence」; 0002「Toshio knows Kenji is the werewolf … Sakura … to protect the werewolf」; 0003 同型 (占い師・人狼・狂人の 3 役が全席に出る)。議論: sl_0001「They lean towards A」, sl_0002「Option A is rejected … Option C … most equitable」, sl_0003「Option A emerges as the most stable choice」, cs_0001「benefits of the Microbiome Atlas」, cs_0002 period 3 に候補名 4 つ。ログ: `log/_pilot5/aiwolf/multi-private/aiwolf_0001__multi-private-process__*` の system 末尾 Plan に上記がそのまま入る (18 局全て確認) | multi-private-process は秘密 (役職) と結末を受け取っており、DESIGN §13「秘密も結末も含まない」・paper §3.4「全条件 (multi-private を含む)」の前提が崩れる。実測: 議論 6 局の最終票が筋書きの隠し `votes` と一致 5/5,3/5,5/5,5/5,5/5,5/5 (無計画 multi-private は 5/5,3/5,2/5,4/5,1/5,5/5)、採択一致 6/6 vs 4/6。`early_reveal_partial` が cs_0003 で 16 件 (無計画 2 件)、sl_0002 で 5 (1)。人狼 0001 では狂人 Kenji が 4 ターン Shizue を庇った末に Shizue に投票、人狼 Shizue も自分に投票 (plan 追従が役職の動機に勝つ) | 04:30 の `_validate_prose` 強化 + 再生成 + 18 局やり直し (作者の予定どおり)。加えて (a) 旧 9 本と旧 18 局は `log/_pilots/` 等へ退避し本実験に混ぜない、(b) 論文には「process 筋書きの漏洩をどう検査したか」を書く (語彙規則 + 人手確認 1 名) |
| 2 | Major | 旧検証 (`_OUTCOME_WORDS` 10 語) は漏洩を検出できず、新検証は過剰にも見える | 旧: `executed|…|wins|win` のみ (04:30 前の L47)。新: 「supports/backs/agrees on/consensus/leans」禁止 + 人狼では**他の参加者名を一切**禁止 + 選択肢語 (`free`, `study`, `location`) 禁止。現 9 本は新検証で 4〜15 件不合格 (実行確認) | 新規則下の process 筋書きは「誰が誰を疑うか」「どの案に傾くか」を言えず、席の筋も「何を気にするか」だけになる。計画の効果が「構造だけの計画」の効果に縮む (それ自体は設計上の選択だが、論文で明示が要る)。また選択肢語の機械判定は語彙依存で、言い換え (「the enclosure」= Option A) は通る (sl_0002 seats[Rin] は「the enclosure (Option A)」で捕まるが「the enclosure」だけなら通る) | 「process = 話題・論点・情報の種類・意見の動きの一般的記述」と paper §3.4 に定義を書き直す。機械検査に加え、再生成した 9 本 (本実験では 90 本) を**筋書きだけから結末を当てられるか**で人手/LLM 判定 (当てられたら不合格) する |
| 3 | Major | 人狼 3 本は生成後に修復が後付けされ、attempts と最終ファイルが一致しない | `aiwolf_000{1,2,3}.attempts.json` (03:25〜03:28) の attempt 2 は `period 1: divine = Kenji/Sakura/Benjamin`、`problems: []`、`repairs` キー無し。最終 `.json` (mtime 03:48:17, `gen_scenarios.py` も 03:48) は `divine: null` + `repairs: ["period 1: dropped divine after the deciding execution"]`。attempt 1 の問題文「no attack after the deciding execution」は現行 validator に存在しない文言 | 当時の validator は終局後の `divine` を見逃し、後からコードを直して 3 本を書き換えた。その経緯が attempts に無い。さらに single-batch-process の aiwolf_0001/0002 (03:46/03:47) は**修復前のファイル**で走り、header.scenario.sha1 (`de4bf8…`, `107366…`) が現ファイルと不一致 (0003 と multi-private-process 3 局は一致)。process 粒度では divine は削られるので提示文は同じだが、header が指すファイルはもう存在しない | 再生成で解消するが、以後は (a) `.attempts.json` を手修正・再修復のたびに追記する、(b) 使った筋書きの**ファイル本体を `raw/` に複製**する (sha1 だけでは復元不能)、(c) validator を変えたら全筋書きを再検証して結果を DESIGN に残す |
| 4 | Major | process 粒度では `find_scenario_deviations` は期間の有無しか検出しない | `common/scenario.py` L471〜: 票・処刑・襲撃・占い・勝敗は plan 側の該当キーが無ければ比較しない。18 局全てで `scenario_deviation` は空 (確認済) | paper §4.3 表 4-2 の「乖離率 (process)」は定義できない。「乖離なし部分集合は補助」(§8) も空集合で成立 | process 用の乖離指標を別に定義する: (i) 期間ごとの話題一致 (plan public と当該期間の発話の LLM/人手判定)、(ii) 席の筋との立場一致、(iii) **隠し `votes`/`final` との一致率** (process が本当に結末を含まないなら無計画条件と同程度になるはず — 漏洩の検査にもなる)。(iii) は `scenario_view` 前の turn ファイルで機械計算できる (本監査の集計スクリプトで実証) |
| 5 | Major | 人狼の筋書きが 3 本とも同型 (0 夜に占い師が人狼を当て、1 日目に処刑、2 期間で終局) | 3 本の `period 0 divine` = 人狼、`final.winner = VILLAGE`、periods = [0, 1]。`single/base/fake.py canned_scenario` と同じ筋 | greedy の最頻筋。本実験 30 設定でも同型が続けば、人狼の計画条件は「2 日で終わる台本」に固定され、無計画条件 (aiwolf_0002 multi-private は 3 日・人狼勝ち) と長さ・難度が揃わない。査読者は「plan 条件は易しいゲームだけ」と見る | 生成時に多様性の制約 (占い先を乱数で固定して与える、期間数の下限) を入れるか、計画条件の比較を**同じ期間数の無計画局**に限る。少なくとも筋書きの長さ分布を報告する |
| 6 | Major | 「同文で置く」が multi-private では成り立たない (自席の筋のみ) | `common/render.py` L156 `None if reveal else [int(seat)]`; ログで multi-private-process は seat_lines=1、他条件は 5。paper §3.4「両方式とも system の末尾に `## Plan` として同文で置き」 | multi-public-process vs multi-private-process は「秘密」に加えて「他 4 席の筋 (4 行)」も違う。情報量軸に筋書き量が混ざる | paper §3.4 と DESIGN §13 に「private は自席の筋のみ、public/single は全席」と明記し、差を「他席の立場の予告」として解釈する。あるいは public 側にも自席のみを渡す条件を 1 つ加えて切り分ける |
| 7 | Minor | 生成の記録が対局ログより薄い | `gen_scenarios.py` L62: `response/usage/finish_reason/error` のみ。`meta["tokens"]`・`prompt_token_ids` (llm.py L136/143) は捨てる。system/user の本文、`sampling`、`model_info` も無し。`source.temperature: null` は CLI 引数で、実効値 0 (`config/models.yml default`) が読めない | 再現には現行コードで再描画するしかなく、validator 文言が変わると retry プロンプトが再現できない (#3) | 対局ログと同じ `llm_call` 形式 (messages / sampling / tokens / prompt_token_ids / model_info) で記録する |
| 8 | Minor | `repair_plan` は Over 後の行を消すが空ターンを残し、その後「no lines」で不合格になる | `shared_living_0003.attempts.json` attempt 1〜2: repairs 10〜15 件 → problems「turn 3/4: no lines」。modelは「turn 2 で全員 Over → turn 3,4 で Skip」の型を繰り返す | 修復が内容を歪める (本物の行を落とす) 可能性と、修復しても不合格という二重の無駄。最終 9 本に turn 修復は入っていない (確認済) ので内容の歪みは無い | 空ターンは落とす (または Over 後の行があれば Over を取り消す方を採る)。repair の単体テストが無い (tests/ に `repair` 無し) |
| 9 | Minor | turn 粒度の要旨の質: 「turn 3 全員 Skip, turn 4 全員 Over」が定型 | aiwolf_0001/0003, cs_0002/0003, sl_0003 の多くの期間。議論 cs_0001 は要旨が三人称「Suggests …」、cs_0002 は一人称の台詞。人狼 0001 turn 2 Mizuki「If Benjamin is the Seer, the game ends now」(結末の暗示) | turn 条件は上限条件なので致命ではないが、要旨の書式が設定間で揺れる。全員 Skip の 1 ターンは実質 3 ターンの台本 | 要旨の書式 (三人称 1 文) を要求文で固定。Skip/Over の全員一致ターンは禁止しなくてよいが、生成後に分布を報告する |
| 10 | Minor | `single/base/run.py` L124 の既定 `"outline"` | `scenario.get("granularity", "outline")` vs `DEFAULT_GRANULARITY = "process"` | `scenario_view` が必ず `granularity` を入れるので実害なし | 定数に揃える |

## 依頼された 6 点への回答

1. **筋書きの質**: 役職・関心事・カードとの整合は良い (cs_0001 の seats はカード名と関心事に対応、sl の選択肢 A/B/C も正しい)。だが「占い師が X を名指し」は過程として許容するつもりでも、**公開の筋に占い師の名と占い結果が入れば役職が全席に伝わる**ので、multi-private に渡す process 筋書きでは許容できない (#1)。査読者は「process plan は outcome plan の言い換え」と見る。turn 要旨は妥当だが定型化 (#9)。
2. **生成モデル自身が single の system で書くこと**: 妥当 (同一モデル・同一情報で、筋書き自体が条件差にならない)。ただし筋書きは single-batch の書き手が「書く前に立てる計画」そのものなので、single-batch にとっては自分の事前分布、multi にとっては外部拘束になる非対称がある。pilot5 の最終票一致率 (無計画 single-batch 対 筋書きの隠し votes) は 9 局で 4/5,3/5,4/5,5/5,3/5,4/5,4/5,1/5,5/5、採択/勝敗一致 8/9、無計画 multi-private は 6/9 — n が小さく推測の域だが、single 寄りの傾向は否定できない。対策: 「筋書き生成の system を role 段落なし (観察者) にする」か、論文で非対称を明記し「計画が single の事前分布と一致する度合い」を報告する。
3. **検証・修復・記録**: 検証の範囲 (票→同票→処刑→勝敗、生存、Over 後、ターン数) は十分。prose 検査は旧版では不十分 (#2)。修復は決定的で記録されるが #8 の欠陥と、#3 の後付け修復で attempts との整合が崩れた。attempts は response を全文保持するので「何が出たか」は追えるが、「何を入れたか」(prompt, sampling) は追えない (#7)。
4. **multi-private に自席の筋だけ**: 実装は意図どおり (verify も検査)。比較可能性: public 側との差は「秘密」+「他席の筋 4 行」(#6)。他席の筋は「他人の立場の予告」なので、情報量軸の一部として解釈するのが筋。ただし現 9 本では公開の筋だけで結末が分かるので、席の筋の差は二次的だった。
5. **process 粒度の乖離検出**: 何も検出できない (#4)。測るべきは (i) 話題/論点の一致、(ii) 席の立場推移の一致、(iii) 隠し outcome との一致率 (漏洩検査を兼ねる)。(iii) は本監査で集計済み (上表 #1)。
6. **greedy の再現性**: 言えない。seed は渡していない (`single/base/llm.py` に seed 無し)、同一 setup の再生成比較は無い、DESIGN §14 が vLLM greedy の非決定性を実測している。主張を「筋書きは固定ファイル (sha1 を header に記録) であり、生成手順は greedy で attempts を保存した」に限定する。再生成時に 2 回回して一致率を 1 行報告すれば十分。

## 確認した範囲と確認していない範囲

- 確認済: 上記ファイルの全文 (04:31 時点)、9 本の筋書きと attempts (全レコード、最終ファイルとの差分)、ファイル mtime、18 局の header.scenario / sha1 照合 / violations / system 末尾 Plan ブロック (全席の先頭呼び出し)、pilot5 全 63 局の期間数・最終票・結末と筋書きの隠し votes/final の一致、violation code の集計、aiwolf_0001 multi-private-process の Day 0/1 発話。新 validator を 9 本に実行。
- 推測: #2 の「新規則では計画が空疎になる」(再生成結果を見ていない)、#5 の「本実験でも同型が続く」、問 2 の single 寄り傾向 (n=9)。
- 未確認: outcome / outline / turn 粒度の実ログ (pilot5 に無い)、turn 要旨と実発話の対応、`scripts/verify_prompt_control.py` の実行 (他監査の担当)、人手による筋書きの読みやすさ、04:31 以降の変更 (再生成・再実行)。
- 使った集計スクリプト: `/tmp/claude-1091/-diskthalys-ssd14ta-yharada-aiwolf-undergraduate-research/bcec8730-29c9-4bd2-98fc-0a8842b00e36/scratchpad/{check_logs.py,periods.py,hidden_match.py}` (リポジトリには置いていない)。
