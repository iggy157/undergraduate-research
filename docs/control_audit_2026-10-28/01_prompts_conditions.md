# 監査 A: プロンプトと条件 (2026-10-28)

担当: 5 条件 + 筋書き条件のプロンプト本文が設計 (DESIGN §6, §7, §13) どおりか。読んだもの: common/prompts/*.jinja, common/render.py, common/conditions.py, common/scenario.py, agent/base/prompts.py, agent/base/seat.py, agent/prompts/*.jinja, single/base/prompt.py, single/prompts/*.jinja, data/*/rules.yml, config/models.yml, scripts/verify_prompt_control.py, scripts/prompts/scenario_request.jinja, docs/paper_draft.md §3。
実ログ: log/_pilot5 の aiwolf_0001 / candidate_selection_0001 / shared_living_0001 × 7 条件 (5 条件 + single-batch-process + multi-private-process) の全 llm_call (計 1,030 call) を、現行テンプレートの再描画と条件間 diff にかけた。

## 結論 (3 行)

1. system は設計どおり: single-batch / stepped / single-online / multi-public は**役割段落 1 行だけ**が違い、multi-private はそこから `## Participants`×5 + `## Hidden information` が `## Your profile` (自席) に置き換わるだけ、-process は末尾に同文の `## Plan` (multi-private は自席の part のみ)。3 setup × 全 call が再描画とバイト一致。
2. しかし **筋書き条件と stepped 条件は壊れている**: (a) process 筋書きが 9/9 で役職・選択肢名・最終的な傾きを含み、「秘密も結末も含まないので multi-private にも渡せる」という前提が成立していない (監査中の 04:30 に validator が強化され、現在 9 本全部が不合格 → verify も fail)。(b) single-batch-stepped の aiwolf では user の出力形式 `-> <target name> (human|werewolf)` に従って書き手が ` Shizue (werewolf)` と書き、サーバが不正として捨てるため **3/3 局で占いが成立していない**。
3. single-batch の user にだけある内容指示 (死者は発言しない / 占い結果は真役職と一致 / 最多票の名前を書く) は「書き手が台本を有効にするための転写要件」として容認できるが、論文で明示する必要がある。役割文・Hidden information 文は概ね公平、文言の小さな偏りを下に列挙する。

## 発見した問題 (深刻度順)

| # | 深刻度 | 項目 | 証拠 | 影響 | 修正案 |
|---|---|---|---|---|---|
| 1 | **Critical** | **stepped の aiwolf で占いが毎回無効**。user の format_aiwolf.jinja L11/L20 `- divine: <Seer's name> -> <target name> (human\|werewolf)` に従い、続き書きの DIVINE 応答が ` Shizue (werewolf)` (stop `\n`)。server/aiwolf/logic.py L93 `match_name` が完全一致しか取らず `valid:false` → 占い師は結果を受け取らず、書き手ビューに `- divine: Benjamin -> none` と出る | log/_pilot5/aiwolf/single-batch-stepped/aiwolf_0001__…/*.log L27 `{"action":"divine","valid":false,"raw":" Shizue (werewolf)"}`、aiwolf_0002 L26、aiwolf_0003 L26 と L58 (` Mizuki (human)`: 真役職は Werewolf。書き手が結果を決めている実例)。Day1 T1 の stepped assistant に `- divine: Benjamin -> none` (本報告の diff 出力) | stepped は「batch と同一プロンプト + 結末だけサーバ」ではなく「占いが無い batch」になっている。それでも Seer が Day 1 に「Shizue is the Werewolf」と言う (全知の帰結) ので、batch との差の解釈が崩れる。aiwolf の stepped 3 局は無効 | `agent/base/seat.py` の stepped DIVINE/ATTACK は stop に `" ("` を足すか、サーバ側 `match_name` を「先頭の候補名 + 任意の括弧」に緩める。書き手が書いた `(human\|werewolf)` は `raw` として残し、`divine_mismatch` 相当で集計する。aiwolf stepped を再実行 |
| 2 | **Critical** | **process 筋書きが秘密と結末を含む**。aiwolf 3/3: Day 1 の public 行が「Benjamin reveals his divination of Shizue as the Werewolf」「Toshio knows Kenji is the werewolf」「Jonathan, as the Seer, knows Mizuki is the werewolf」。multi-private に渡る自席 part も「Kenji: … to protect his werewolf ally (Shizue)」(Possessed は規則上、人狼を知らない)。議論 6/6: Round 3 public に選択肢名 (cs_0001 'Microbiome Atlas'、cs_0002 は 4 つ全部; Round 3 開示のはず) と `Option A … lean towards A`、seat part に `shifts to supporting A` (= 最終投票) | 描画結果は本報告の scenario_block 出力 (全 9 本)。pilot5 当時の `_OUTCOME_WORDS` は executed/adopted/wins 等のみ。common/scenario.py は 2026-10-28 04:30 に強化され (L48-52, L137-)、現行 validator で 9/9 不合格 (aiwolf 各 4 件、cs 6/15/14、sl 8/11/8)、`verify_prompt_control.py --setups *_0001` も 3/3 fail | multi-private-process は実質 public (役職・結末が system に入る)。pilot5 の -process 18 局は「process ≠ outcome」の主張に使えない。-process 条件では `early_reveal` (選択肢名の先出し) が筋書き由来で混入 | 新 validator で筋書きを再生成し -process を全部再実行。aiwolf では「誰が誰を疑う」も結末なので public 行は話題と空気だけに制限 (新 validator の方針どおり)。論文 §3.4 に「process でも公開の筋は結末を強く示唆しうる (aiwolf は特に)」と限界を書く |
| 3 | Major | **single-batch の user にだけある内容指示**: format_aiwolf.jinja L26 「dead players have no further lines. The divine result must match the target's true role. Write ## Result right after the deciding Vote or Action and nothing else.」、L17/L24 `(one line per living participant)`、`- execution: <name of the player with the most votes>`、format_discussion.jinja L13 `titles exactly as listed`、L24 `adopted: <label … most votes>`。online / multi に対応物なし (サーバが実行) | single/prompts/format_*.jinja; 実ログ single-batch / stepped / -process の user に同文 (再描画一致) | 判定: 転写を有効にするための「書き手専用の転写要件」(ii-b)。ただし「dead players have no further lines」は schedule_notes「Executed and attacked players are dead from the next day on」の言い換えで DESIGN §6.3 (再記述禁止) に触れる。verify は 15 字以上の**完全一致**しか見ないので通る。stepped では同文が入るが無意味 (サーバが強制) で、設計上「同一プロンプト」の代償 | (a) DESIGN §7.3 の表に「書き手専用の転写要件」として 3 文を明記し、論文 §3.3 にも書く。(b) 「dead players …」は削る (schedule で既に言っている)。(c) 占い結果の一致は書き手にしか書けない要件なので残す |
| 4 | Major | **書き手ビューに `### Findings` / `### Options` が無い**。single-online / stepped の user は全席の `- investigate: X -> t1; t2` 行は持つが、調べた結果の本文は system の `## Hidden information` にしか無く、選択肢も system のみ。multi は Round 2 に自席の Findings 本文、Round 3 に Options を台本の中で見る | candidate_selection_0001: single-online R3T1 の user に Findings 無し、multi-public/private の同位置に `### Findings` (本文 2 件) と `### Options` あり (本報告の節一覧) | single-online vs multi-public は「1 文脈か席ごとか」だけのはずが、「情報の提示位置 (system の一覧 vs 使う直前のインライン)」も違う。DESIGN §7.4 は「全知性による必然の差」として容認しているが、hidden states と局所応答性の比較に効く | 書き手ビューにも Round 2 に全席分の `### Findings`、Round 3 に `### Options` を入れる (全知なので情報量は増えない、位置だけ揃う)。入れないなら論文で「全知の書き手」軸の一部として明記 |
| 5 | Minor | 役割文 3 種の非対称: online writer だけ仕組みを説明される (「each time you are shown the discussion so far and write only its next line, for the participant named at the start of that line」)。参加者は「speaking only in your own turns」だけで、「台本の続きを 1 行書く」とは言われない。batch/stepped の書き手には出力単位の記述なし (stepped は設計上同文) | common/prompts/role.jinja L2/L4/L6; 実ログの diff は役割段落 1 行のみ | 文面は短く、全条件で finish_reason=stop 100%、TALK の最大 completion 61 token なので実害は見えない。査読者は「online だけ指示が丁寧」と見る可能性 | 参加者文に「each time you are shown the discussion so far and write only your next line」を足して online と対にするか、online から仕組みの説明を削る (ラベル `- **X**:` が仕組みを示す) |
| 6 | Minor | Hidden information の文が書き手向け: 「The participants do not know them before the schedule above says so」を multi-public の**参加者**も読む (自分は参加者なのに「参加者は知らない」)。見出しも `## Participants` (三人称の 5 人、自分を含む) | common/prompts/hidden.jinja L2; 実ログ multi-public の system | multi-public は診断条件 (paper §3.2) なので致命ではないが、「知っていて知らないふり」をプロンプトが明示しない | 「They become known only as the schedule above says; nothing from them may be said in the talk before the round in which it is revealed.」のように主語を消す |
| 7 | Minor | 筋書きファイルの sha1 がログと不一致: aiwolf_0001/0002 の single-batch-process header は de4bf84c / 107366ff、ディスク (mtime 03:48:17、run は 03:46) と multi-private-process は 11eac45e / f674ab95 | header.scenario.sha1 vs `sha1sum scenarios/aiwolf/*.json` | 描画した `## Plan` は現ファイルと一致 (再描画 1/1) なので process 内容は同じだが、記録された sha1 のファイルが存在せず「同一筋書き」を sha1 で証明できない | 筋書きを書き換えたら全条件を再実行する運用に。gen_scenarios が既存ファイルを書き換える経路 (--force / repairs) をログに残す |
| 8 | Minor | 停止列と上限の条件差 (下記 (5))。VOTE/ACTION の stop が stepped `["\n"]`、online/multi なし、batch なし。timeout 600 vs 1800 | header.sampling、agent/base/seat.py L310、config/models.yml | 上限は一度も効いていない (14 局で finish_reason=stop 100%、FULL 最大 960 token)。差は生成単位の必然。#1 はこの stop と format の相互作用で起きた | 論文の統制表に「停止列: TALK 共通 4 列、票・行動は行末 (stepped) / なし (online, multi)、上限は不発」と書く |
| 9 | Minor | 文書と実装のずれ: DESIGN §6.2/§7.2 は `## For the writer only`、single_disclosure.jinja、output_rules.jinja、出力先頭の Participants 表を記述するが、実装は hidden.jinja、output_rules 無し、表無し (§13 は正しい) | docs/DESIGN.md L261, L286, L319-321, L371, L383, L406-409 | 第三者が DESIGN から再構成すると別のプロンプトになる | §6.2/§7.2 を §13 に合わせて書き直す |
| 10 | Minor | 語の不統一 (条件間ではなくドメイン内): candidate_selection の schedule は「selected」、format_discussion と Plan は「adopted」、scenario_context の Outcome は「candidate A is selected」 | data/candidate_selection/rules.yml L23, single/prompts/format_discussion.jinja L24, common/scenario.py `final_text` | 全条件同文なので統制には無害 | option_noun と同様に rules.yml に動詞を置く |

## 依頼された確認点への回答

(1) **single-batch の user の内容指示** — #3 のとおり。他に `(one line per living participant, in the fixed speaking order; repeat for Turn 2, 3 and 4; a participant who said Over has no line in the later turns)` は structure/schedule の言い換えだが、雛形の説明として必要。統制上は「書き手専用の転写要件」として列挙して容認し、「dead players …」だけ削る。
(2) **役割文の公平性** — 3 文とも「under the rules and the flow given」を共有し、長さは 160 / 318 / 190 字。差は #5 のみ。
(3) **Hidden information** — #6 のみ。aiwolf には Hidden ブロックが無く、役職は `## Participants` の `Role:` 行 (multi-public も同じ)。
(4) **Plan ブロック** — 9 本を process / seat 1 のみ / outline で描画。process 粒度に `Votes:` / `Executed:` / `Night:` / `Outcome:` が無いことは 9/9 で確認 (verify の文字列検査も通る)。しかし散文で役職・選択肢名・傾きが漏れる (#2)。multi-private には自席 part だけ渡ることを実ログの diff で確認 (`Each participant's part:` の下が 1 行)。
(5) **停止列と max_tokens** — TALK: stepped / online / multi とも `["\n- **", "\n####", "\n###", "\n##"]`、batch は無し (書き手が自分で次のラベルを書く)。VOTE / ACTION: stepped `["\n"]`、online / multi なし、batch なし。max_tokens: 行単位 1024 / 64 / 64、batch 16384 (全文)。timeout: server 系 600 s、batch 1800 s。stepped だけ `/v1/completions` (prompt ids + 続き) で他は chat.completions。実測: TALK 最大 61 token (multi-public)、FULL 960 token、finish_reason は 14 局全 call で stop。上限は不発、差は生成単位の必然 (#8)。ただし stepped の DIVINE は 8 token = `(werewolf)` 込みで #1 を起こした。

## 設計で容認している非対称 (論文で明記すべきもの) と査読者の見方

| 項目 | single-batch / stepped | single-online | multi-public / private | 査読者の見方 |
|---|---|---|---|---|
| user の要求文 | 「Write the complete transcript …」+ `## Output format` (雛形); stepped は同文 + assistant に台本と札 | 台本 + `- **X**:` のみ (指示文なし) | 席ビュー + `- **X**:` のみ | 妥当。ただし「online / multi には指示文がゼロ」と明記する |
| VOTE / ACTION | batch: 書き手が全部書く。stepped: 札 `- Kenji ->` だけ | 「Vote request. Output only the name of one player.」+ `Candidates: …` (インライン、自分を含む) / 「Divine request …」+ 箇条書き (自分を除く) | 同左 | 候補列挙は server 系の必然。VOTE と ACTION で形式が違うのは内部不統一 (前回 #9、未修正) |
| 台本に見えるもの | 書き手ビュー: 全席の行動行、翌朝の `- divine: S -> T (werewolf)` | 同左 | 席ビュー: 自分の行動行、`### Findings` (本文)、`### Options`、他席の占い行は無し | 情報量の軸そのもの。ただし #4 (提示位置) は軸外 |
| 人物欄 | `## Participants` ×5 | 同左 | public: 同左 / private: `## Your profile` | 設計どおり |
| 停止・上限 | #8 | #8 | #8 | 不発を数値で示せば問題なし |

## 4 観点の判定

- 統制: system は設計差のみ (確認済み)。user は #3 / #4 の非対称が設計差の外にある。筋書き条件は #2 で統制が崩れている。
- 正しさ: 描画は DESIGN §13 どおりで、ログは再描画とバイト一致 (3 setup × 7 条件、1,030 call)。stepped の aiwolf は #1 で設計 (「結末はサーバが決める」) が成立していない。
- 査読耐性: #1 と #2 は Critical (再実行で直る)。#3 は Major だが論文で列挙すれば Minor に落ちる。#4 は「online vs multi の差は文脈分割だけ」という主張への反例になりうる。
- 再現性: テンプレート + rules.yml + setup から全 system/user が決定的に再現できることを確認。欠けるのは #7 (筋書きの sha1) と #9 (DESIGN の記述)。

## 確認した範囲と確認していない範囲

確認済み: aiwolf_0001 / candidate_selection_0001 / shared_living_0001 の 7 条件の全 llm_call について、system と (single 系の) user が現行テンプレートの再描画とバイト一致; 条件間の system diff (役割段落 / 人物欄 / Plan のみ); 9 本の筋書きを process・seat 別・outline で描画; stepped の DIVINE/VOTE/INVESTIGATE の生応答と server ログの valid; stop / max_tokens / finish_reason の全 call 集計; 新 validator で 9 本を再検証。
未確認 (推測を含む): aiwolf_0002/0003 と cs/sl の 0002/0003 のログは #1 (divine) と header の sha1 しか見ていない; 席ビュー・書き手ビューがサーバ記録から復元した文字列と一致するか (監査 B/C の範囲、tests/test_conditions.py が保証と主張); #4 の「提示位置」が結果に効くかは推測; common/scenario.py が監査中に変更されたので、本報告の #2 の件数は 04:30 時点のコードによる。
