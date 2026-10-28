# 監査 E 第 2 ラウンド: 横断的検閲 — 2026-10-28 パイロット 6

対象: BRIEF_round2、00_SUMMARY の「発見と対処」表、05 (第 1 ラウンドの自分の報告)、11〜13 (A/B/C 第 2 ラウンド)、pilot6_inspect.txt、pilot6_hidden.txt、DESIGN §13〜14 末尾、paper_draft v3 §1/§3/§4/§8、common/{scenario,setup,llm_meta}.py、scripts/run_multi.py、single/__main__.py、config/{experiment,models}.yml、scenarios 9 本、setups 90 本、log/_pilot6 の header と結末。
自分で再計算したもの: 現行 validator で 9 本を再検証、setups の option_perm の分布、pilot6 議論 48 局の採択を表示位置と元ラベルで集計、人狼 24 局の夜 0 の占い先。A/B/C の第 2 ラウンドのバイト照合・トークン照合・tests は再実行せず記載を採用した。

## 結論 (3 行)

1. 第 1 ラウンドの必須修正 5 件のうち、筋書きの漏洩・非決定性の床・ラベル順・header の 4 件は**機構として満たした** (validator 9/9、Plan のバイト一致 630 call、反復 9/9 同一、採択の表示位置 10/13/16/9、header の版情報は本実験で埋まる)。評価の最小設計は未着手。
2. ただし修正の検証から**新しい事実が 2 つ**出た: (i) A 偏重はラベル順ではなく**内容**だった (元ラベル A が 48 局中 34 局で採択、表示位置は分散) ので「正解のない議題」の前提と結末系の指標を見直す必要がある、(ii) **コードが成果物より後に変わる**運用 (筋書き生成中の gen_scenarios.py、validator の語彙追加、header の endpoint 追加) が続いており、現行 validator は shared_living_0003 を不合格にする。git も版の記録も無い。
3. 本実験には**進んでよいが、その前に (a) を 1 日分**: コード凍結と版の記録 (git 導入)、凍結後に筋書き 90 本を一括生成 (sl_0003 を含む)、top-2 logprob と接続先の記録、stepped の夜 ≥ 1 の接頭辞、占い行の raw、反復の縮小とサーバ割当の規則、評価の 1 ページ文書 (一次指標・対・マージン・描画・除外)。

## (1) 必須修正の充足状況

| 第 1 R 必須 | 状態 | 根拠 | 残るもの |
|---|---|---|---|
| 1 process 筋書きの漏洩 | **満たした** (機構) | validator 9/9 空 (自分で再実行、ただし下の sl_0003 を除く)、process 描画に名前・選択肢・結末語なし (A/C)、Plan のバイト一致 single 9/9・multi 621/621、multi-private-process の先出し 27 → 1 件、夜 0 の占い先が計画と一致 1/3 (漏洩なら 3/3) | (b) 人狼の process は「占い師が Day 1 に公表」を 3/3 で固定し結末が 3/3 反転 (A#1, C#3)。(b) 席の筋 5 つを合わせると結末を推定できる (書き手のみ)。(a) sl_0003 は現行 validator で不合格 (新 #2) |
| 2 非決定性の床 | **満たした** | `VLLM_BATCH_INVARIANT=1` で single-batch 反復 9/9 全文一致 (token id・logprob・prompt まで: B)。batch/stepped の残る分岐は近接確率 4 件 (Δlp ≤ 0.06、同一 token 上の Δlp p99 = 0.06 と整合) + サーバの構造矯正 4 件。DESIGN 末尾の説明 (prefill vs decode の数値経路差) は B のトークン照合と整合 | (b) 反復は single-batch のみで server 条件の決定性は未測定 (新 #4)。(b) 1-2 位差は未記録 (新 #5)。(b) 2 台のサーバの同一性は未検証で pilot6 の header に接続先が無い (新 #3) |
| 3 ラベル順の相殺 | **満たした** (機構) が**原因の診断が変わった** | option_perm は seed の別ストリームで setup 90 本に入り、cs は元 A の表示位置 {0:11, 1:7, 2:4, 3:8}、sl は {10, 8, 12}。pilot6 の採択を表示位置で見ると 10/13/16/9 (分散)、**元ラベルで見ると A 34 / B 10 / C 3 / D 1** | 偏りは内容 (新 #1)。setup 内では 5 条件がほぼ同じ選択肢を採る (6 setup 中 2 は 1 種、他は 2〜3 種) |
| 4 評価の最小設計 | **未着手** | BRIEF_round2 (検閲後に設計) | 本実験の前に必要かは下の (2) |
| 5 header の推論環境 | **コードは満たした**、pilot6 は欠落 | `common/llm_meta.py` は vllm_version・model_root・hf_revision・chat_template_sha1・config_sha1 を返す (B が現サーバで確認)。pilot6 の 72 header は vllm_version 以外 None (修正前に回したため)。`endpoint` と `server_timeout_s` は pilot6 後に追加 (run_multi.py L99-118、single/__main__.py L72; pilot6 の header キーに無い) | (b) pilot6 の header は「None、推定 842da37、接続先不明」と注記。(a) コードの版は依然どこにも無い (新 #2) |
| 補: online→multi-public の可視性 | DESIGN §13 に明記済み | §13 末尾の 1 段落。paper §3.2 の梯子表と貢献 (2) は未修正 (v4 で) | 下の (4) #1 |

## (3) 第 2 ラウンドで新たに見つけた横断的な問題

| # | 分類 | 項目 | 証拠 | 影響 | 対処 |
|---|---|---|---|---|---|
| 1 | **(b)** Major | **選択肢の内容に優位がある**: 元ラベル A が 48 局中 34 局 (71%) で採択。表示位置は分散 (10/13/16/9) なので第 1 ラウンド #5 の「ラベル順バイアス」は誤診で、インスタンス生成の内容 (元 A) の優位が主因 | 自分の集計 (header.option_perm × outcome.adopted)。setup 別の元ラベル: cs_0001 {A,B}、cs_0002 {A}、cs_0003 {A,B,D}、sl_0001 {A,C}、sl_0002 {B,C}、sl_0003 {A} | 統制は壊れない (全条件同じ instance) が、(i) paper §3.1「正解のない議題 (カードの有利不利は合計 0)」が内容の優位で崩れる、(ii) setup 内で条件が同じ結末に収束するので、結末系の指標 (採択の分散、票と立場の整合、プローブの「最終投票先」ラベル) は条件間の分散を持たない | 本実験後にインスタンス別の「優位選択肢率」を表で出し、§3.1 を「内容の優位は残る (x%)」に。プローブのラベルは「最終投票先」より発話単位の属性 (語数・Skip/Over・呼びかけ先) を主に。10 インスタンス全部で元 A が優位かは本実験で分かる (pilot は 6 インスタンス) |
| 2 | **(a)** Major | **コードの版が記録されず、成果物より後に変わる**: (i) 現行 `_OUTCOME_WORDS` は `yields? to` と `the team's need` を含み、**shared_living_0003.json は現行 validator で不合格** (自分で再実行: `seats[Mizuki]: 'yields to'`)。pilot6 の sl_0003 の process 2 局はこの筋書きで回った (server は読込時に検証するので、今は同じ局を再実行できない)。(ii) gen_scenarios.py が生成中に変更 (C#1)。(iii) endpoint / llm_meta も pilot6 後に変更。header には setup_sha1・rules_hash・models_yml_sha1・scenario.sha1 はあるがコードの版は無く、git も無い | common/scenario.py L48-52、scenarios/shared_living/shared_living_0003.json、log/_pilot6 header キー一覧 (endpoint 無し)、BRIEF「git 管理なし」 | 第三者が「どのコードがこのログを作ったか」を特定できない。本実験 (450+ 局、90 本) を同じ運用で回すと再現性の主張 (paper §3.3「固定記録」) が成立しない | **本実験前に git init + 初回コミット**、header と筋書き source に commit hash (dirty フラグ付き) を記録。コードを凍結してから筋書き 90 本を一括生成 (sl_0003 を含む) し、全本を凍結 validator で再検証。本実験中はコードを変えない (変えたら版を上げて記録) |
| 3 | **(a)** Minor | **2 台のサーバ (:8000 / :8010) の同一性が未検証**で、pilot6 では接続先が残っていない。条件をサーバに固定して割り振ると、サーバ差 (GPU・起動引数・カーネル選択) が条件と交絡する | config/models.yml `default` / `default_b`、pilot6 header に endpoint 無し (コードは追加済み) | batch-invariant でも別プロセス・別 GPU の数値一致は保証されない。batch と stepped の「恒等性」をサーバ跨ぎで測ると偽の分岐が出る | 割当の規則を 1 行で決める: **同じ setup の全条件は同じサーバ** (サーバは setup 単位で交互)。加えて 3 setup × single-batch を両サーバで回し一致を確認 (安価)。endpoint は本実験の header に入る (確認済み: コード) |
| 4 | **(a)** Minor (設計) | **反復の意味**: T=0 + batch-invariant では反復は同一 (9/9)。本実験の「反復」は分散推定にならず GPU 時間だけ使う。一方 server 条件 (multi / online: 5 席の並行要求) の決定性は未測定 | pilot6_inspect「replicates IDENTICAL 9/9」、反復は single-batch のみ | 検定単位は setup (paper §4.2 どおり) で反復は寄与しない。server 条件が非決定的なら「batch と multi の差」に雑音の床が要る | 反復を「決定性検査」に縮小: 各条件 3 setup × 2 回 (server 条件を含む) で一致率を報告し、残りは回さない。既定 sampling の頑健性走行 (§4.1) は別 |
| 5 | **(a)** Minor | **top-2 logprob が未記録**: 分岐の「近接」は batch と stepped が各自選んだ token の logprob 差 (間接) でしか言えない (B#5)。後から足せない | single/base/llm.py L120-133 (`logprobs=True` のみ)、00_SUMMARY #5「保留」 | 「数値解像度以下の反転」の直接証拠が無いまま本実験を回すと、§4.3 (b) の根拠が間接のまま | `top_logprobs=2` を本実験の記録に足す (1 行)。hidden states の再生 (HF) から出る margin は vLLM の数値と別なので代替にならない |
| 6 | **(a)** Minor | stepped の夜 ≥ 1 の接頭辞に占い結果が入らず、Day 2 に進む局で batch と必ず分岐 (B#2)。有効な占い行に書き手の `raw` が無い (A#3, B#1) | agent/aiwolf/__init__.py L77-86、server/aiwolf/logic.py L96-100 | 本実験の stepped 人狼で Day 2 に進む局が出れば恒等区間が切れる。書き手が偽の結果を書いた局を .log から数えられない | どちらも小さい修正。本実験前に入れ、tests を足す |
| 7 | **(b)** | 人狼の全知条件の退化は不変: single-batch ×2・stepped・online・public・batch-process の **15/15 局が夜 0 に人狼を占い Day 1 終局**。multi-private は 3/3 WEREWOLF (3 日)、multi-private-process は 3/3 VILLAGE (占い師 CO の指示: C#3) | 自分の集計 (夜 0 の占い先 vs 筋書きの人狼)、pilot6_inspect の結末 | aiwolf の条件比較は「ゲームの長さと結末」の層別なしでは質の比較にならない。multi-private だけ 3 日続くので長さの交絡が議論ドメインより大きい | 本実験で期間数・夜 0 命中率・Day 1 終局率を手続き指標に。人手評価は期間数を揃えた部分集合を併記。主系から外すかは本実験の分布で決める |
| 8 | **(b)** | option_perm は無作為で釣り合いは強制されない (cs の元 A の表示位置 2 は 30 setup 中 4) | setups 集計 | #1 により位置の効果は小さく見えるので実害は小さい | 報告のみ。Latin 方格に変えるのは (c) (setup 凍結) |
| 9 | (c) | 追加条件 (participant 役割文 + 書き手ビュー)、筋書きの多様性制約、占い師 CO 時刻の禁止規則 | 05#3、C#3 | 条件は凍結 | 採らない。ただし「CO 時刻を書かない」規則は条件ではなく生成規則なので、本実験の 90 本生成前にどちらにするか**決めて記録**する (どちらでも可、変えるなら pilot との差を注記) |

## (2) 本実験に進んでよいか

進んでよい。第 1 ラウンドの Critical 2 件は実ログで解消し、退行は無い (A/B/C の照合: system 1,127 call・user 110 call・Plan 630 call・TALK 以外 408 call がバイト一致、tests 201 passed、error/truncated 0)。
評価設計を「本実験の前」に置く第 1 ラウンドの判断は、**範囲を縮めて維持**する。理由: 評価の詳細 (評価者の人数・画面) は後でよいが、(i) 記録に後から足せないもの (top-2 logprob、接続先、コード版)、(ii) 走行の設計 (反復の扱い、サーバ割当、除外規則)、(iii) 一次指標・主要比較・同等性マージンの事前固定 (paper §4.2 が約束している) は、結果 (手続き指標は走行直後に見える) を見る前に書いておかないと探索的分析と区別できない。scripts/render_blind_pairs.py が描画の出発点として既にある。

**進む前の (a)** (いずれも小さく、合計 1 日程度):
1. git init + 初回コミット。header と筋書き source に commit hash を記録 (#2)。以後コードを凍結し、変更は版を上げる。
2. 凍結後に筋書き 90 本を一括生成し、凍結 validator で全本を再検証 (sl_0003 を含む)。CO 時刻の規則は生成前に決めて記録 (#2, #9)。
3. `top_logprobs=2` の記録、header の endpoint (コード済み) の確認 (#5, #3)。
4. stepped の夜 ≥ 1 の接頭辞、占い行の raw と `divine_mismatch` (#6)。
5. 走行の規則 1 ページ: サーバ割当 (setup 単位)、反復 = 決定性検査 (各条件 3 setup)、除外規則 (error / truncated / 早期終局の扱い)、サーバ跨ぎ一致の確認 3 setup (#3, #4)。
6. 評価の 1 ページ: 一次軸 2〜3 (人手)、主要比較 5 対、同等性マージン、描画 (書き手ビュー正規化後、行動行・Over 行の表示)、盲検監査 (条件推定の回答)、長さ共変量と長さ揃え部分集合、LLM 判定の手順。
7. DESIGN §6.2/§7.2 と §13 表 (continue_final_message)、L199 (raw_differs) の古い記述 (A#4, B#7)。

**進めながらでよいもの (b)**: #1 (優位選択肢率は本実験の集計)、#7 (層別)、paper v4 の書き直し (下)。

## 条件凍結の方針で査読に耐えるか (online→multi-public の可視性)

耐える。ただし条件は: 梯子の段を「要因 1 つ」と言わず、§3.2 の表のその行に **役割の枠組み (書き手→参加者) / 文脈の分割 / 他席の動的な秘密 (占い・調査結果) の可視性** の 3 つを並記し、multi-public を「静的な秘密のみ公開」と定義し、貢献 (2) の「5 要因を 1 つずつ」を「隣接条件ごとに 1〜3 要因 (表に列挙)」に下げ、§4.3 (c) の帰属を「文脈の分割 (役割の枠組みと動的秘密の可視性を含む)」と書くこと。査読者が「分離していない」と指摘しても、論文がそれを先に言っていれば Major にはならない。分離条件を足さない理由 (診断条件であり主張の対象でない) を §8 に 1 文。

## (4) 論文 v4 で必ず書くべき限界 (条件凍結のもと)

1. 梯子の段の多要因: stepped→online は目標 + 置き場所 (+ 出力形式・制約文・候補一覧の有無)、online→multi-public は上の 3 要因。multi-public = 静的秘密のみ。
2. batch と stepped の差の中身: 反復は決定的 (9/9)、分岐は prefill/decode の数値経路差による近接確率の反転 (Δlp ≤ 0.06) とサーバの構造矯正に限られ、恒等区間は 5〜26 行 (1 setup は全文)。「再現可能」は batch-invariant モードと同一サーバの条件付き。
3. 筋書きの性質: 同一モデル greedy の既定軌道で、single にはほぼ無変化・multi には書き手の筋の注入 (非対称)。人狼の process は占い師の公表時刻を含み結末をほぼ決める。席の筋 5 つの合成で結末が推定できる (書き手のみが見る)。乖離率 0 は拘束力の指標であって計画の効果ではない。
4. 議論ドメインの内容の優位 (元 A 71%) と、setup 内で条件が同じ結末に収束すること。結末系の指標とプローブの「最終投票先」の分散が小さい。
5. 人狼の全知条件の退化 (夜 0 命中・Day 1 終局 15/15)、multi-private のみ 3 日。期間数の層別。
6. 条件が長さ (15 vs 33 語)・Over 率から判別できる: 盲検の限界、長さ共変量、評価者の条件推定率を報告。
7. 先出しの向き (pilot: online ≥ batch) と検出の偽陽性: 「一括生成に固有」は仮説として書く。
8. 推論環境の記録: pilot の header は版情報と接続先が欠け、hf_revision は refs/main からの推定。本実験は commit hash・snapshot・template sha1・endpoint を記録。
9. 評価者が見るのは正規化後の台本 (batch の pass_after_over 等は書き手の習慣、multi はサーバが強制)。
10. 一般性: 5 人・英語・24 ペルソナの再利用 (変量効果)・ドメイン構造差 (人狼 2 期間、先出し指標なし)、筋書きとプローブは主系モデルのみ。
11. 筋書き生成コードの版 (pilot 9 本中 8 本は累積なし版) — pilot の筋書きを論文に載せる場合。
12. multi-public の「知っていて知らないふり」(既記載) と、process が multi-private では自席の筋のみである非対称 (§3.4 L115 の「同文」を修正)。

## 確認した範囲と確認していない範囲

- 確認済み (自分で実行・読んだ): 現行 validator による 9 本の再検証 (sl_0003 のみ不合格)、setups 90 本の option_perm 分布、pilot6 議論 48 局の採択 (表示位置・元ラベル)、人狼 24 局の夜 0 の占い先と期間数、pilot6 header のキー (endpoint 無し)、llm_meta.py・setup.py (option_permutation / options)・scenario.py L40-190・run_multi.py L93-118・single/__main__.py L72・models.yml・experiment.yml、DESIGN §13〜14 末尾、paper v3 §1/§3/§4/§7/§8、A/B/C 第 2 ラウンド報告。
- A/B/C の記載を採用 (再実行せず): バイト一致 (system / user / Plan / 非 TALK)、トークン単位の分岐とΔlogprob、tests 201、served_info の実機確認、hf_revision の推定、筋書き attempts の再生一致。
- 未確認 (推測を含む): 2 台のサーバの数値一致 (#3 は懸念であり観測ではない)、server 条件の決定性 (#4)、10 インスタンス全部の内容の優位 (#1 は 6 インスタンスの観測)、hidden states の値 (pilot6_hidden.txt を信用)、Qwen3.8 / gemma-4-12B。
