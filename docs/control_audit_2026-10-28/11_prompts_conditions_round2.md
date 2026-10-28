# 監査 A 第 2 ラウンド: プロンプトと条件 (2026-10-28、パイロット 6)

担当: 第 1 ラウンド (01_prompts_conditions.md) の指摘への修正が効いているか、退行が無いか。読んだもの: common/scenario.py (現行 validator)、common/render.py、common/prompts/*.jinja、agent/base/prompts.py、single/base/prompt.py、single/prompts/*.jinja、server/base/parse.py、server/aiwolf/logic.py、scripts/prompts/scenario_request.jinja、pilot6_inspect.txt。
実ログ: log/_pilot6 の aiwolf_0001 / shared_living_0001 × 8 局 (5 条件 + batch 反復 + 2 process 条件、計 497 call) を現行テンプレートで再描画して照合、9 setup × 2 process 条件 (18 局、計 630 call) の `## Plan` を筋書きファイルの process ビューの再描画と照合、candidate_selection_0001 / shared_living_0002 × 8 局で option_perm の一貫性を確認。検査スクリプトは scratchpad (audit_a2.py、読み取りのみ)。

## 結論 (3 行)

1. **Critical 2 (process 筋書きの漏洩) は解消**: 9 本すべてが現行 validator を通り、process 描画に選択肢名・ラベル・結末語・(人狼の) 他者名は無い。ログの `## Plan` は再描画と全 call バイト一致 (single-batch-process 9/9、multi-private-process 621/621)、multi-private-process は自席 part のみ、header の sha1 はディスクと一致 (第 1 ラウンド #7 も解消)。
2. **option_perm は一貫**: header.option_perm、setup、system の `## Hidden information`、席ビューの `### Options`、VOTE の `Candidates:`、票・result のラベルが全条件で同じ表示順 (A, B, … の付け直し) を使う。**条件間の system / user の差は第 1 ラウンドどおり**で退行なし (役割段落 1 行 / Participants+Hidden ↔ Your profile / Plan 同文、stepped と process の user は batch と同一、全 497 call が再描画と一致)。stepped の占いは 3/3 有効。
3. 残るのは語レベルの取りこぼし: shared_living_0003 の seat part 1 行が**集団の帰結**を書く (「yields to the team's need for stability」= 採択される Fixed Desks)、validator の語彙に無い選好動詞 (preference / pushes for / moves toward / yields) が 4 本に残る (自席の立場なので設計内)、人狼では「Seer が Day 1 に結果を公表する」ことが公開の筋で固定され multi-private-process の結末が 3/3 VILLAGE に反転 (plan 無しは 3/3 WEREWOLF)。(a) は小さな修正 2 件 + 文書 1 件。

## 発見した問題 (深刻度順)

| # | 深刻度 | 分類 | 項目 | 証拠 | 影響 | 修正案 |
|---|---|---|---|---|---|---|
| 1 | Major | **(b)** (+ (a) の語彙追加は任意) | **aiwolf の process 筋書きは「Seer が Day 1 に結果を公表し、誰かが accused になる」ことを公開の筋で固定する**。3/3 本が同型 (Day 0 導入 → Day 1「The Seer shares a discovery / reveals a result … the accused」)。人狼席 (multi-private-process) もこの行を読む | scenarios/aiwolf/*.json period 1 public、本報告の描画 (全 3 本)、log/_pilot6/aiwolf/multi-private/aiwolf_0001__multi-private-process__…/*.jsonl seat 4 (Shizue=Werewolf) の system `## Plan`。pilot6_inspect: multi-private-process の結末 VILLAGE 3/3、multi-private は WEREWOLF 3/3 | 名前も結末語も無いので現行の定義「process = 話題と流れ」は満たすが、5 人 1 狼では「Seer が Day 1 に claim する」= ほぼ勝敗。-process の効果の大半がこの 1 文で説明できる可能性 (D の範囲) | 条件は凍結なので採らない。論文 §3.4 の限界に「人狼の process 筋書きは Seer の公表時刻を固定し、それが結末をほぼ決める」と明記。任意: `scenario_request.jinja` の人狼規則に「役職の行動 (claim / divine) の時刻を書かない」を足し、本実験の筋書き生成でだけ適用 |
| 2 | Minor | **(a)** | **shared_living_0003 の seat part が集団の帰結を書く**: Mizuki「… but eventually yields to the team's need for stability」(= 採択 C: Fixed Desks by Function、全 7 局で C)。Rin「moves toward stability once …」、Toshio「remains consistent in his preference for the least expensive change」も最終の傾き。`_OUTCOME_WORDS` に yields / preference / moves toward / pushes for が無く通過 | scenarios/shared_living/shared_living_0003.json seats、common/scenario.py L48-52 の正規表現 (本報告で 6 句を照合、全部 None)。log …/shared_living_0003__multi-private-process__… seat (Mizuki) の system に同文、single-batch-process は 5 行全部 | 自席の立場は設計内 (seat = stance over time) だが「the team's need」は集団の結末。multi-private-process では Mizuki 1 席、single-batch-process では書き手に結末が渡る。1/9 本、1 行 | `_OUTCOME_WORDS` に集団の帰結を指す句 `yields? to|the (team|group)'s need` を追加 (本報告で 9 本に当てると sl_0003 Mizuki の 1 行だけが該当)、shared_living_0003 を再生成して process 2 局を再実行 (本実験前)。自席の選好動詞 (preference / pushes for / moves toward) まで禁止すると cs_0003 Toshio と sl_0003 Toshio / Rin も該当するが、それらは自席の立場 (#6, (b)) なので語彙に入れない |
| 3 | Minor | **(a)** | **有効な占い・襲撃の action 行に `raw` が無い**。stepped の書き手が書いた ` Shizue (werewolf)` は jsonl の llm_call.response にしか残らず、.log の action 行は `{"action":"divine","result":"WEREWOLF","valid":true}`。vote 行は `raw` を持つ | server/aiwolf/logic.py L96 (valid 時は raw を渡さない) vs L99-100 (無効時のみ)、log/_pilot6/aiwolf/single-batch-stepped/*/*.log action 行 | 書き手が書いた種別と真役職の不一致 (第 1 ラウンド #1 の「書き手が結果を決めている」例) が .log から検出できない。pilot6 は 3/3 一致 (` Shizue (werewolf)` / ` Kenji (werewolf)` / ` Mizuki (werewolf)`、全員真の人狼) | vote 行と同様に valid 時も `raw` を記録し、括弧内が真役職と違えば `divine_claim_mismatch` を violations に |
| 4 | Minor | **(a)** (文書のみ) | DESIGN §6.2 / §7.2 の古い記述が残る: `output_rules.jinja` (L286, L406)、`single_disclosure.jinja` / 「For the writer only」(L67, L319-321, L371, L409)。実装は hidden.jinja、output_rules 無し | docs/DESIGN.md 該当行; 00_SUMMARY #15 は §13 と IMPLEMENTATION_NOTES のみ修正 | 第 1 ラウンド #9 のまま。第三者が §6-7 から再構成すると別のプロンプト | §6.2 / §7.2 / §7.4 の表を §13 と common/render.py に合わせる |
| 5 | Minor | **(b)** | header の `option_perm` は「表示順に並べた元ラベル」(例 `['A','D','B','C']` = 表示 B が元 D) で、表示ラベル→元ラベルの対応は code の docstring と DESIGN L499 にしかない。票・result・pilot6_inspect の「adopted」は**表示ラベル** | log header、common/setup.py L300-315、pilot6_inspect「adopted labels」 | 集計で「A が採択」と書くと位置の偏りの話になる。元ラベル (内容) で集計したい評価では変換が要る | 論文の集計は「表示位置」と「選択肢内容 (orig_label)」を分けて書く。header に `options: [{label, orig_label, name}]` を足すと自明になる (任意) |
| 6 | Minor | **(b)** | 選好動詞 (自席の立場) は process の定義どおりだが語彙が偏る: sl_0001 5/5 行が argues for/against・resists、cs_0003 Toshio「pushes for options that serve the widest user base」、sl_0003 Yumi「argues for a layout that keeps related roles together」(= Fixed Desks の言い換え) | 本報告の process 描画 | 自席にしか渡らない (multi-private) ので統制は壊れない。書き手 (single-batch-process) は 5 席分を見るので結末を推定できる = 全知の書き手の必然 | 論文で「process の seat part は各自の立場を含み、5 つを合わせると結末を示唆しうる (書き手だけがそれを見る)」と書く |
| 7 | Minor | **(b)** | aiwolf の seat part に自席の役職語: Benjamin「his divination results」(Seer)、Kenji「steering suspicion away from his allies」(Possessed)、Benjamin (0003)「protecting the werewolf's interests」 | 描画 3 本、SCAN「role word」 | multi-private では自席 part のみなので自分の役職 (既知) の再述。書き手は全知。統制上無害 | 無し (論文の筋書き例に載せるときは注記) |
| 8 | Minor | (b) | 第 1 ラウンド #5 (役割文の非対称)、#6 (hidden.jinja「The participants do not know them」を multi-public の参加者も読む)、#10 (selected / adopted) は未変更 | common/prompts/role.jinja、hidden.jinja L2、data/candidate_selection/rules.yml L23 vs scenario.py final_text | 第 1 ラウンドの評価のまま (Minor) | 論文の統制表に列挙 |

## 依頼された確認点への回答

1. **process 筋書きの漏洩 (9 本)** — 現行 validator: ファイル 9/9、process ビュー 9/9 とも不合格 0。描画 (`scenario_block(env, ctx, scenario_view(sc, "process"))`) に選択肢名 (6 本の全 option 名を照合)、ラベル参照、`_OUTCOME_WORDS`、人狼の他者名 (自席ラベル以外の名前) は無い。追加走査で引っかかった語は `Hours` (sl_0002「labor hours」、option A「Managed Collection Hours」) と `Desks` (sl_0003「moving desks」、option C) のみで、どちらも素材語 (validator の規則どおり)。ログ: single-batch-process の system 末尾 `## Plan` は描画と 9/9 一致、multi-private-process は自席 part 版と 621/621 call 一致、part の名前は自席のみ 621/621、period 行は single-batch-process と全席で同一。header.scenario.sha1 は 18/18 でディスクと一致。残る問題は #1 (人狼の公表時刻)、#2 (sl_0003 の集団の帰結 1 行)。
2. **option_perm の一貫性** — cs_0001: setup/header `['A','D','B','C']`、system Hidden は `A: Microbiome Atlas / B: Plant Drought Signaling / C: Protein Folding Dynamics / D: Regeneration in Amphibians` (= 表示順)、席ビュー `### Options` の 4 行は Hidden の 4 行とバイト一致 (multi-public / multi-private / -process)、`Candidates: A, B, C, D`、票は A×5 (online と batch-process は C×5)、result と header.outcome も同じ表示ラベル。sl_0002: `['C','B','A']` で `A: Managed Collection Hours / B: Rotating Location / C: Enclosed Structure`、同様に全条件一致 (票 B×5、mp-process A×5、batch-process B×4 A×1)。single 系は Hidden のみ (席ビュー無し、設計どおり)。問題なし (#5 は記録の説明)。
3. **条件間の差 (aiwolf_0001 / shared_living_0001、各 8 局)** — system は全 call が再描画と一致 (aiwolf 1+1+46+46+46+62+1+63、sl 1+1+60+70+70+70+1+70)。diff: batch→stepped 0 行、batch→online 役割段落 1 行、batch→multi-public 役割段落 1 行 (自席名)、multi-public→multi-private は `## Participants` 4 人分 + `## Hidden information` (sl) が `## Your profile` に (役割段落は同一)、batch→batch-process と private→private-process は `## Plan` の追加のみ (後者は自席 part 1 行)。user: single-batch / stepped / -process で同一 (再描画一致 1/1, 46/46, 1/1; sl 1/1, 60/60, 1/1)。stepped の messages は system/user/assistant、stop は TALK 4 列 / VOTE・ACTION `["\n"]`、server 系は TALK 4 列 / VOTE・ACTION なし、finish_reason は全 call stop (最大 completion 60 token)。VOTE / ACTION の要求文は 3 server 条件で同文。退行なし。
4. **batch だけの制約文と書き手ビューの Findings / Options を (b) とする方針** — 異論なし。根拠: (i) 制約文 (format_aiwolf.jinja 末尾 3 文、format_discussion の `titles exactly as listed`) は pilot6 でも batch / stepped / -process の user に同文で入り、stepped ではサーバが強制するので無意味だが「同一プロンプト」の対価として設計内。(ii) 書き手ビュー (single-online) に `### Options` が無いことは pilot6 でも同じ (views=none) が、同じ 4 行が system の Hidden にあり情報量は等しく、位置の差は「1 人の全知の文脈」軸の一部として 00_SUMMARY #6 で扱われている。ただし論文の統制表に (i) の 3 文と (ii) の「提示位置」を明記すること。

## 第 1 ラウンド指摘の追跡

| 第 1 R # | 状態 | 根拠 |
|---|---|---|
| 1 stepped 占い無効 | 解消 | match_name が末尾括弧を除去 (parse.py L43); 3/3 局 valid、書き手の括弧内は 3/3 で真役職と一致。残: #3 (raw 未記録) |
| 2 process 漏洩 | 解消 (語レベルの残り #1, #2) | validator 9/9 合格、描画に名前・選択肢・結末語なし |
| 3 batch の制約文 | (b) 維持 | 上記 4 |
| 4 Findings / Options | (b) 維持 | 上記 4 |
| 5, 6, 10 文言 | 未変更 (b) | #8 |
| 7 sha1 不一致 | 解消 | 18/18 一致 |
| 8 停止列・上限 | 変化なし、不発 | finish_reason stop 100% |
| 9 DESIGN の古い記述 | 未修正 | #4 |

## 4 観点の判定

- 統制: system / user の条件差は設計差のみ (497 call 照合)。process 条件は 9/9 本で名前・選択肢・結末語を含まないが、人狼の公表時刻 (#1) と sl_0003 の 1 行 (#2) が結末を示唆する。
- 正しさ: ログは再描画とバイト一致 (system 1,127 call、single 系 user 110 call、Plan 630 call)。stepped の占いは設計どおりサーバが判定。
- 査読耐性: #1 は -process 条件の解釈 (特に人狼) に効くので論文で先に言う。#2 は再生成で消える。他は Minor。
- 再現性: 筋書きの sha1・option_perm・Plan は header から決定的に再現できる。欠けるのは #3 (書き手の占い記述) と #4 (文書)。

## 確認した範囲と確認していない範囲

確認済み: 上記の全照合 (aiwolf_0001 / shared_living_0001 の 8 局 × 全 call、9 setup × 2 process 条件 × 全 call の Plan、cs_0001 / sl_0002 の 8 局 × option_perm、aiwolf stepped 3 局の DIVINE / VOTE 応答と action 行、verify_prompt_control.py 9 setup OK)。
未確認 (推測を含む): cs / sl の 0002-0003 と aiwolf_0002-0003 の非 process 条件の system は再描画していない (verify と pilot6_inspect の view check に依拠); #1 の「公表時刻が結末を決める」は 3 局の結末の反転からの推測で、因果は D の範囲; #2 の語彙追加は本報告の狭い句でだけ 9 本に当てた (広い句は上記のとおり 2 本追加で該当); 席ビューの `### Findings` の本文一致は B の範囲; header の hf_revision / chat_template_sha1 / config_sha1 が None なのは B へ (本報告の範囲外、記録の欠落として要確認)。
