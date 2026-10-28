# 論文シナリオ草稿 v5 (外部レビュー用、2026-10-28)

> **位置づけ**: 本実験前の草稿。§5 の数値は**パイロット 6〜8 の実測** (gemma-4-31B-it、各ドメイン 3 設定) で、規模が小さいため「仮の結果」である。v4 からの主な変更: (1) 評価設計を「好みを問う対比較」から「発話単位の事象計数 + 自動指標」に改めた (理由は §4.5)。指標は先行研究のセットをそのまま採る (Bo et al. 2026 の 5 指標、PLACES の自動 3 指標、Becker et al. 2026 の誤り分類)。(2) 共通ルール文に 2 文 (「話し合いは参加者どうしの会話である」「@Name で相手に直接話しかけられる」) を加え、その効果をパイロット 7〜8 で測った (§3.5, §5.3)。(3) ストーリーを「single は簡潔で冗長でなく譲るが、呼びかけられても答えず反論しない。multi は応答し反論するが冗長。single は隠された情報を漏らす」という**族 A 内と族 A/B 間の二重のトレードオフ**に書き直した。(4) 付録に全プロンプト (2 文を含む) と注釈指示文を載せた。

---

## タイトル案

第一候補: **Concise but Parallel: What a Single Writer Gains and Loses over Per-Agent Generation in LLM Multi-Party Discussion**

第二候補: **Batch or Line by Line? Disentangling Generation Granularity, Context Partition and Information Access in LLM-Generated Multi-Party Discussions**

日本語仮題: 台本を一括で書く単一 LLM と席ごとの LLM による多人数議論生成の統制比較: 簡潔さ・応答性・情報漏洩のトレードオフ

## 概要

LLM に複数人の議論を生成させる方法には、1 つの LLM が台本全体を一括で書く方法 (single) と、参加者ごとに独立した LLM を置いて 1 発話ずつ対話させる方法 (multi) がある。両者はプロンプトや進行手続きが違うまま比べられてきた。本研究は、同一モデル・同一ルール文・同一台本文法・同一の情報公開スケジュールのもとで差分を設計した軸だけに絞った比較基盤を構築し、3 ドメイン (人狼、候補者選定、共同生活の取り決め) × 各 30 設定で 5 条件 (single-batch / single-batch-stepped / single-online / multi-public / multi-private) を比べる。隣り合う条件の差はそれぞれ「結末と構造の決め手」「プロンプトの目標と履歴の置き場所」「文脈の分割」「情報量」に対応する。評価は、議論の「会話としての質」と「情報の整合性」を別の族として測り、合成しない。前者は先行研究の指標セット (Bo et al. の Responsiveness / Rebuttal / Non-repetition / Evidence usage / Stance、PLACES の words per turn / Distinct-N、Becker et al. の誤り分類から「進展のない発話」) を発話単位の率として報告し、後者は知らないはずの情報の使用と公開前の選択肢名の出現を機械照合と人手確認で数える。パイロット (各ドメイン 3 設定) では、single-batch は multi-private の半分の語数で (15 語 vs 33 語)、進展のない発話が 2/3〜1/3、Skip / Over による譲りが 4 倍だった。一方で応答性 (直前の発言に取り組んだ発話の率) は共通ルール文の調整後も multi が高く (全体 71〜76 vs 59〜62)、反論は multi に多く、single は呼びかけられても本人が答えない傾向があった。情報の整合性では、全役職を知る条件の占い師が初回の占いで必ず人狼を当て (1.00 vs 0.00)、他者の調査結果の使用は single にのみ見られた。本研究はこの二重のトレードオフを示し、single の簡潔さを情報と応答性を保ったまま multi に移すこと (蒸留) を今後の課題とする。

## 1. はじめに

LLM を用いた多人数議論の生成は、社会シミュレーション、対話データの合成、ゲーム AI に使われる。生成の仕方には、1 回の生成で議論全体を書き下ろす中央集権的な方法と、各参加者を独立した LLM にして逐次に応答させる分散的な方法がある。前者は整合的な台本を書きやすく、後者は参加者が互いに反応する対話になりやすい、と言われるが、既存の比較は方式ごとにプロンプトや進行手続きが異なり、どの差がどの性質を生むのかを特定できない。面接対話では対話エージェント方式が一括生成より高く評価されたという報告 (De Baer et al., GEM 2025) もあり、「どちらが良いか」は設定と観点に依存する。

本研究の問いは「一括生成と逐次生成は、議論のどの性質に対してそれぞれ長所と短所を持ち、その差は何によって生じるか」である。自己回帰モデルでは、同じトークン列を一度に生成しても、1 行ずつ止めて同じ接頭辞から再開しても、greedy なら同じ続きが出る。したがって「一括か逐次か」の差は、生成を分割すること自体ではなく、(1) プロンプトの目標、(2) 履歴の置き場所、(3) 結末と構造の決め手、(4) 文脈の分割、(5) 情報量のどこかから生じる。本研究はこの 5 つを 1 つずつ変えた条件を並べて測る。

本稿が主張したいことは次の 3 点で、評価設計はこれらを**別々に**測れるように組む (優劣の合成点は作らない)。

- **簡潔さと譲り**: 一括生成は、発話の長さが場面に応じて変わり、語数上限に張りつかず、話すことがなければ Skip / Over でターンを畳み、自分の立場の言い直しや挨拶の定型句が少ない。席ごとの生成は、ターンが残る限り上限いっぱいまで話し、言い直しで埋める。
- **応答と反論**: 席ごとの生成は、他者の発言を自分の文脈で読んで応え、反対する。一括生成は各人を順に書くので並列になりやすく、呼びかけはできても呼びかけられた本人が答えない、反対意見が出ない、という癖がある。
- **情報の整合性 (副作用)**: 一括生成の書き手は全員の秘密を知っているため、参加者が知らないはずの情報 (他者の調査結果、役職) を発話に混ぜる。

いずれも「指示なし」で両方式に同じルール文を与えたときの方式の性質 (傾向) として記述し、「良い」とは言わない。single の簡潔さを、情報と応答性を保ったまま multi に移す (蒸留) ことは本稿の範囲外の今後の課題とし、基盤はそれを見据えて設計する。

**研究課題**

- RQ1 (会話としての質): 一括生成と逐次生成は、簡潔さ・非冗長性・譲り・応答性・反論のそれぞれでどう違うか。差は梯子のどの段 (結末の決め手 / 目標と置き場所 / 文脈の分割 / 情報量) で生じるか。
- RQ2 (情報の整合性): 全知の書き手はどの程度、知らないはずの情報を発話に混ぜるか。情報を揃えた席ごとの生成 (multi-private) でそれは消えるか。
- RQ3 (計画と頑健性): 結末を含まない筋書きは、両方式の性質をどう変えるか。傾向はドメインとモデルを変えても再現するか。

**貢献**: (1) 差分を設計した軸だけに絞った比較基盤 (共通ルール文・共通台本文法・席ビューと書き手ビューの決定的復元・違反と正規化の共通記録・推論エンジンが見たトークン id の記録・バッチ不変モードによる決定的な再現)。(2) 5 条件で 5 要因を 1 つずつ分離する実験設計と、分割自体が効かないことの実証。(3) 先行研究の指標セットをそのまま適用し、「会話としての質」と「情報の整合性」を分けて報告する評価設計と、LLM の対比較判定が表示と問いで向きを変えることの実証 (§4.5)。(4) 簡潔さ・譲り (single) と応答性・反論 (multi) の族 A 内トレードオフ、および全知の書き手による情報漏洩の定量化。

## 2. 関連研究

**LLM マルチエージェント議論・ゲーム**: 複数 LLM の討論による推論の改善 (Du et al., 2023)、役割分担による協調 (Li et al., 2023, CAMEL)、生成エージェントによる社会シミュレーション (Park et al., 2023)。人狼については LLM エージェントの経験学習 (Xu et al., 2023) と人狼知能大会 (AIWolf / aiwolf-nlp)。

**single と multi の比較**: 面接対話で一括生成と 2 エージェント対話を比べ、LLM 判定では対話方式が高く、トークン数は約 6 倍だった研究 (De Baer et al., GEM 2025)。最後通牒ゲームでの single と multi の人間行動再現の比較 (Sreedhar & Chilton, HICSS 2025)。multi-agent debate の優位が single-agent ベースラインに対して不安定であることを示した研究 (Zhang et al., 2025)、議論の構造的・認知的要因を操作した統制研究 (Wu et al., 2025)。本研究は多人数の自然言語対話の生成を対象に、5 つの要因を 1 つずつ分離する点で異なる。

**多人数対話の評価指標**: Bo et al. (AAMAS 2026) はプロンプトの部品で対話の振る舞いを制御できることを示すために、Responsiveness (直前の発話に取り組んだか、発話単位の二値、LLM 判定)、Rebuttal (明示的に反対したか)、Non-repetition (自分の直前発話との非重複、埋め込み)、Evidence usage (与えられた知識の語句を使ったか)、Stance (ペルソナ文との類似) の 5 指標を定義した。良し悪しの向きは定めない記述的指標である。PLACES (Chen et al., 2023) は合成会話を人間収集データと比べるために words per turn、turns per conversation、Distinct-N を報告し、人手で Natural / Coherent / Interesting / Consistent と多人数固有の Comprehensible / Balanced engagement を 1〜5 で評価した。Becker et al. (EACL Findings 2026) は多エージェント討論の逸脱を専門家 8 名が 170 抜粋に誤りの型 (Lack of progress、Low-quality feedback、Low-quality engagement、Knowledge gap 等) を付けて分類した。本研究は Bo の 5 指標と PLACES の自動 3 指標をそのまま採り、Becker の分類から「進展のない発話」を発話単位で数える。

**LLM 判定のバイアス**: Samanta et al. (ACL 2026) は多人数対話の対比較 (Naturalness / Engagingness / Overall) で、人間同士の κ が 0.29、人間と LLM の κ が 0.11〜0.18 にとどまり、LLM 判定が冗長な発話を好み、Tie を避け、発話順の破壊を罰しないことを示した。本研究は予備評価で同じ現象を観測し (§4.5)、好みを問う対比較を主結果から外した。

**隠れ状態の解析**: 発話生成直前の表現から将来属性を復号する研究 (Dong et al., 2025) に倣い、補助分析として方式間の復号可能性を比べる (§6)。

## 3. 比較基盤

### 3.1 ドメインと設定

3 ドメイン、いずれも 5 人。議題は設計上「正解のない」もので、タスク精度は測らない (カードの有利不利は候補ごとに合計 0、人狼は自己対戦)。

| ドメイン | 内容 | 非公開情報 | ラウンド構造 | 決定 |
|---|---|---|---|---|
| 人狼 (aiwolf) | 5 人村 (占い師 1、人狼 1、狂人 1、村人 2) | 役職 | Day 0 (投票なし) → Day 1, 2, … | 毎日投票・処刑、夜に占い/襲撃 |
| 候補者選定 (candidate_selection) | 国の助成金など、提案 4 件から 1 件を選ぶ審査 | 各自の関心事 + 調査結果 | Round 1 → 調査 → Round 2 → 選択肢公開 → Round 3 → 投票 | 最多票の候補 |
| 共同生活 (shared_living) | 同居者・部員の取り決め 3 案から 1 案を選ぶ | 同上 | 同上 | 同上 |

各ラウンド 4 ターン、固定の発話順、1 発話 1〜40 語、`Skip` (そのターンをパス) / `Over` (そのラウンドから離脱)。議論ドメインでは Round 1 終了時に各自が 10 件の「調べられる事柄」(題名は公開、本文は非公開) から 2 件を選び、結果は本人だけに知らされる。ペルソナは 24 人から 5 人を割り当て、設定ファイルで固定。選択肢の表示順は設定ごとに決定的に並べ替える。各ドメイン 30 設定。

### 3.2 条件

| 軸 | 値 |
|---|---|
| method | single (LLM 1 つ) / multi (席ごとの LLM) |
| generation (single) | batch (台本全文を 1 回で) / batch-stepped (同じプロンプトのまま、台本を自分の書きかけとして 1 行ずつ続ける。結末と構造はサーバが決める) / online (進行に合わせて「次の 1 行」を書く。台本は user に貼り直す) |
| information (multi) | private (自席の秘密のみ) / public (全員の秘密を全席に開示) |
| plan | なし / process / outcome / outline / turn |

| 条件 | 役割文 | system の残り | user (+ assistant) | 結末の決め手 |
|---|---|---|---|---|
| single-batch | 「あなたはこの議論の書き手」 | 共通ブロック + 5 人の人物欄 (役職/関心事) + 隠された情報 (選択肢・カード全文) | 台本全文の要求 + 出力形式 | 書き手 |
| single-batch-stepped | 同上 | 同上 | 同上 + assistant = それまでの台本 (書き手ビュー) と次の札 (続き書き) | サーバ |
| single-online | 「あなたはこの議論の書き手で、1 行ずつ書く」 | 同上 | 書き手ビュー + `- **X**:` | サーバ |
| multi-public | 「あなたは参加者 X」 | 同上 | 席 X の台本 (席ビュー) + `- **X**:` | サーバ |
| multi-private | 「あなたは参加者 X」 | 共通ブロック + 自席の人物欄 | 同上 | サーバ |

隣り合う条件の差 (梯子):

| 比較 | 変わるもの |
|---|---|
| single-batch vs single-batch-stepped | 結末と構造の決め手 (書き手 vs サーバ) だけ。接頭辞のトークン列は同一で、greedy ならサーバが差し替えない限り同じ発話が出る。推論エンジンの数値的な非決定性の大きさもここで測る |
| single-batch-stepped vs single-online | プロンプトの目標 (全文か次の 1 行か) + 履歴の置き場所 (assistant の続きか user の貼り直しか) |
| single-online vs multi-public | 1 つの全知の文脈か、席ごとに分割された文脈か (他席の夜の行動・調査の可視性を含む) |
| multi-public vs multi-private | 情報量 (全員の秘密か自席の秘密か) |

single-batch と multi-public と single-online の system は役割段落だけが違い (付録 B.3)、single-batch-stepped は single-batch と同一の system と user を使う (検証スクリプトが 90 設定で確認)。multi-public は「自然なマルチエージェント」ではなく情報アクセスを操作した診断用条件であり、人狼では「知っていて知らないふりをする」ことでゲームの前提が変わることを明示する。

### 3.3 統制

| 項目 | 統制の内容 |
|---|---|
| モデル | 同一モデル、temperature 0、推論エンジンのバッチ不変モード (`VLLM_BATCH_INVARIANT=1`; 同じ入力なら同じ出力)、思考モード無効、revision / 精度 / chat template / 設定の sha1 を header に記録 |
| ルール文 | 4 ブロックを 1 本のテンプレートから全条件に展開し、バイト一致を自動検証 |
| 台本文法 | 全条件が同じ Markdown 文法。席ビューと書き手ビューはログから決定的に復元でき、エージェントが実際に受け取った user / assistant とバイト一致することをテストで保証 |
| 情報公開 | スケジュール表に「いつ・誰に・何が知らされるか」を明記。single には先出し禁止、multi には席ビューで同じタイミングに同じ内容 |
| 発話の境界 | 1 行ずつの条件は同じ停止列 (次の台本要素) で切る |
| 違反と正規化 | 全条件のログを同じ CSV に変換し、同じ検出器で違反と正規化を記録 |
| 投票 | サーバ集計 (multi / online / stepped) と書き手集計 (batch) を同じ同票規則で扱い、不一致を記録 |
| 記録 | 全 LLM 往復、推論エンジンが見たプロンプトのトークン id、生成トークン id と対数確率 (次点トークンを含む)、sampling 設定、条件札、コード木の sha1 |

### 3.4 筋書き

設定ごとに同一モデルが greedy で 1 本書く (台本からは作らない)。中身を「過程」と「結末」に分け、4 種類を派生する。

| 種類 | 中身 | 与えられる条件 |
|---|---|---|
| process (主系) | 各期間の公開の筋 (話題・論点・意見の傾き) + 席ごとの立場の推移。**票・処刑・採択・夜の行動・勝敗・選択肢名・被疑者名を含まない** | 全条件 (multi-private を含む) |
| outcome | 票・処刑 (採択)・夜の行動・勝敗だけ | public 条件 |
| outline | process + outcome | public 条件 |
| turn | outline + 各ターン各席の発言要旨 (上限条件) | public 条件 |

生成は turn を 1 本だけ作り、他は削って派生する (入れ子の統制)。検証はルールで機械的に再生 (票 → 同票規則 → 処刑 → 勝敗、対象の生存、発言単位の整合) し、公開の筋と席の筋に結末語・選好語・選択肢名・(人狼では) 他者名と役職語がないことも確認する。両方式とも system の末尾に `## Plan` として同文で置き (付録 B.6)、進行は強制せず、乖離を両方式共通の検出で記録する。

### 3.5 共通ルール文の 2 文 (2026-10-28 に追加)

移植元の研究で single の「お手本」を作ったプロンプトは、「4 つの失敗モード (情報の抱え込み・早期収束・同調・語彙の単調) を克服する良い議論を示せ」「大半の発話は短く、問い返しを」と明示しており、そのお手本は名指し (他者の名前を呼ぶ発話) が 5 割、語数 21〜22 の対話的なものだった。本基盤は統制のためにこの指示を両方式から削ったが、その結果 single-batch は各自が持ち場を順に報告する並列の独白になった (名指し 1%)。失敗モードの列挙を戻すと「指示に従った議論」の比較になりベースラインでなくなるので、代わりに**議論という活動の定義と形式の道具**として次の 2 文を共通ブロック `## Discussion format` に加えた (両方式に同文。量や形式の指定、評価指標に直結する語は入れない)。

1. 「The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.」(話し合いは参加者どうしの会話であり、互いに応答し、決定はそのやり取りから出る)
2. 「A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said.」(@名前 で他の参加者に直接、質問・返答・同意・反対ができる)

効果はパイロット 7〜8 で測った (§5.3)。

## 4. 評価設計

### 4.1 方針

評価は 2 族に分け、合成しない。族 A「会話としての質」は方式の性質を複数の観測で記述し、族 B「情報の整合性」は single の副作用を数える。指標は先行研究のセットをそのまま採り、独自に定義するのは族 B だけとする。自前の指標は人手との照合で妥当性を示す。定義と主要比較は本実験の前に固定し、パイロットは設計の確認にのみ用いたと明記する。

| 族 | 指標 | 種別 | 出所 |
|---|---|---|---|
| A 会話としての質 | words per turn、turns per conversation、Distinct-N (2, 3, 4) | 自動 | PLACES (Chen et al., 2023) |
| | Non-repetition (1 − max(Jaccard, cos MiniLM) 自分の直前発話に対して)、Evidence usage (自分のカードの語句を使ったか)、Stance (ペルソナ + 関心事との cos) | 自動 | Bo et al. (2026)、定義をそのまま。Evidence usage は議論ドメインのみ |
| | Responsiveness (自分の前の発話以降に言われたことに取り組んだか)、Rebuttal (それに明示的に反対したか) | 発話単位の二値、LLM 注釈 | Bo et al. (2026)。5 人の順番発話に合わせて「直前の発話」を「自分の前の発話以降の発話」に広げた |
| | Lack of progress (自分が既に言ったことの言い直し、挨拶・締めの定型句で、新しい情報・判断・質問・提案を加えない発話) | 発話単位の二値、LLM 注釈 | Becker et al. (2026) の誤り分類の第 1 類。同分類の Ignorance / Hallucinated facts / Self-contradictory も注釈するが、パイロットではほぼ 0 で、起きた場合だけ報告 |
| | 語数上限 (40 語) への張りつき率 (35 語以上の発話の割合)、Skip / Over の回数、全員がパスしたターン数 | 自動 (記述) | 本研究 |
| B 情報の整合性 | 非公開情報の使用: 自分が調べていない調査結果の内容、または他者の役職を根拠にした発話の件数 | 機械候補 + LLM 候補 + 人手確認 | 独自。SOTOPIA の SEC が最も近いが 5 者の議論に合わない |
| | 公開前の選択肢名の出現 (Round 1〜2 に選択肢の正式名) | 自動 | 独自 |
| | 占い師の初回占いが人狼を当てる率 (偶然 0.25)、Day 1 に人狼が処刑される率 (人狼) | 自動 | 独自 (全知の書き手の縮退の指標) |
| 検証 | 注釈者間一致 (κ)、人手標本との一致、判定モデルの系統差 | | Samanta et al. (2026) の判定器検査の手順に倣う |

手続き指標 (違反率・正規化率、トークン数・呼び出し回数・時間) は別表で報告する。MARBLE の Communication Score (Zhu et al., 2025) は原著手順で算出した参照値として付録に置く。

### 4.2 発話単位の注釈

- **材料**: 各局の記録を期間の見出し、発話 (順序どおり、id つき)、票、結果だけの形に描画する。ターン見出し、Skip / Over (人間の議論に存在しない手続きの記号。ルールで数えるだけ)、夜の行動と調査の行 (読者が見ない秘密情報) は落とす。
- **問い**: 発話ごとに 6 つの yes / no (resp, rebut, empty, ignore, misattr, reversal)。各項目は 1 文の定義 + 境界の例で指示する (付録 C)。好みや優劣は問わない。
- **注釈者**: 本実験では手元で配信する Llama 3.3 70B Instruct を主、Qwen3.8-27B を副とし (外部 API は使わない)、両者の一致 (κ) を報告する。パイロットでは Claude 系 2 モデル (Opus / Sonnet) を用いた (設計の確認のため。本実験の数値には使わない)。
- **人手検証**: 各条件 2 局 × 3 ドメイン (約 1,200 発話) を研究室のメンバー 2 名が同じ指示で注釈し、LLM 注釈との一致 (項目別 κ) と人間同士の一致を報告する。一致が低い項目は主張に使わない。
- **集計**: 100 発話あたりの率を局ごとに取り、設定で平均する。長さに依存しない。

### 4.3 族 B の手順

- 非公開情報の使用は 3 段階: (1) 語の照合 (発話者が調べていないカードの特徴語が 2 語以上、または数詞) で候補を出す。パイロットでは精度 10%、再現率 50% で、言い換えを拾えない。(2) LLM に「この発話は、発話者が知りえない調査結果を使っているか」をカードの所有表つきで問い、候補を足す。(3) 候補の全件を人手で確認し、本物だけを数える。精度・再現率は人手確認の結果で報告する。
- 公開前の選択肢名は正式名の単語境界一致のみ。語の一部の一致は候補として記録し、本文の指標にはしない。
- 人狼の全知指標 (占い師の初回命中) は再現率の問題がなく、主指標にする。

### 4.4 統計

検定単位は設定。率指標は対応のある比較の paired bootstrap (95% 信頼区間)、二値指標は McNemar。ドメイン別に報告し、ドメイン × 条件の交互作用は混合効果モデルで確認する。「ほぼ同じ」の主張には同等性マージン (率指標 ±5 ポイント) を事前に置く。一次指標 (words per turn、Non-repetition、Responsiveness、Lack of progress、族 B の 3 指標) と主要比較 (梯子の 4 対 + single-batch vs multi-private + 筋書きの有無) を本実験前に固定し、他は探索的分析とする。

### 4.5 設計の経緯: 対比較判定を主結果にしない理由

v3〜v4 では、条件を伏せた 2 局の対比較で「どちらが人間の議論らしいか」を問う人手評価を主結果に置く予定だった。パイロット 6 の 45 対を LLM 2 系統で判定したところ、同じ対でも表示と問いで向きが変わった: 全記録を見せて「人間の議論らしいか」(譲りの観点つき) では single-batch が multi-private に 0.69 で勝ち、発話だけを見せて「決定に向かう議論として人間らしいか」では 0.39 で負け、基準を「口頭の会話のテンポ・冗長さなし・見合う長さ」と具体化すると 1.00 で勝った (36/36)。最後の設定では判定者間一致 0.90 だが勝者の 87% は短い方で、判定は語数の検出器になっていた。これは Samanta et al. (2026) の報告 (人間同士 κ 0.29、LLM は冗長さに反応) と整合する。好みを問う限り「人間らしい」の中身は判定者に委ねられるので、本研究は好みを問わず、定義した事象を数える設計に改めた。経緯と 3 ラウンドの数値は docs/eval_pilot_2026-10-28/ に記録してある。

## 5. パイロット結果 (仮)

実行: gemma-4-31B-it、temperature 0、バッチ不変モード。パイロット 6 = 3 ドメイン × 3 設定 × 7 条件 (5 条件 + single-batch-process + multi-private-process) + single-batch の反復 = 72 局、共通ルール文は 2 文を加える前。パイロット 7 = 2 文のうち会話文だけを加えて single-batch / single-online / multi-private (27 局)。パイロット 8 = 2 文とも加えて single-batch / multi-private (18 局)。single-batch の反復 2 回は 9/9 設定で全文一致 (決定的)。single-batch と stepped は 1 設定で全文一致、他 8 設定は 5〜26 行目で分岐し、原因は近接確率の反転 (logprob 差 0.06 以下) とサーバの構造矯正に限られた。

### 5.1 族 A: 自動指標 (パイロット 6、7 条件、3 ドメイン平均)

| 条件 | 発話数/局 | 語数/発話 | 上限張りつき | Non-repetition | Distinct-2 | Skip / Over | 全員パスのターン |
|---|---|---|---|---|---|---|---|
| single-batch | 29 | 14.7 | 0.00 | 0.66 | 0.91 | 4.6 / 11.7 | 3.1 |
| single-batch-stepped | 29 | 13.7 | 0.00 | 0.68 | 0.92 | 4.3 / 11.6 | 3.0 |
| single-online | 45 | 24.5 | 0.03 | 0.61 | 0.84 | 2.0 / 3.1 | 0.9 |
| multi-public | 49 | 30.5 | 0.20 | 0.56 | 0.79 | 1.3 / 3.7 | 0.1 |
| multi-private | 54 | 32.9 | 0.38 | 0.59 | 0.79 | 0.2 / 3.1 | 0.0 |
| single-batch-process | 35 | 16.6 | 0.00 | 0.67 | 0.91 | 3.9 / 11.6 | 2.8 |
| multi-private-process | 53 | 33.3 | 0.37 | 0.57 | 0.79 | 0.2 / 4.2 | 0.0 |

読み: 梯子を上がるほど発話は長くなり、上限に張りつき、Skip / Over を使わなくなる。batch と stepped は一致する (分割自体は効かない)。最大の段差は stepped → online (語数 13.7 → 24.5、Over 11.6 → 3.1) で、プロンプトの目標と履歴の置き場所が主因である。multi-public → multi-private (情報量) は張りつき率を 0.20 → 0.38 に上げる。Evidence usage (議論ドメイン) は 0.23〜0.31 で条件差がなく、Stance は 0.13〜0.18 で差がない (記述のみ)。

### 5.2 族 B: 情報の整合性 (パイロット 6)

| 条件 | 占い師の初回占いが人狼 (偶然 0.25) | Day 1 に人狼が処刑 | 公開前の選択肢名 (件/局) | 非公開情報: 人手確認で本物 |
|---|---|---|---|---|
| single-batch | 1.00 | 1.00 | 0.00 | 1 件 |
| single-batch-stepped | 1.00 | 1.00 | 0.00 | 0 |
| single-online | 1.00 | 1.00 | 0.17 | 0 |
| multi-public | 1.00 | 1.00 | 0.00 | 0 |
| multi-private | 0.00 | 0.00 | 0.00 | 0 |
| single-batch-process | 1.00 | 1.00 | 0.00 | 1 件 |
| multi-private-process | 0.33 | 0.67 | 0.00 | 0 |

読み: 全役職を知る条件では占い師が初回の占いで必ず人狼を当て、Day 1 に必ず処刑される。multi-private だけが偶然の水準にある。議論ドメインの本物の漏洩は single にのみ 2 件 (Kenji「the repository is fast now」: Toshio だけが調べて未公開の事実。Misaki「fixed headcount の預かり金」: Mio だけが調べ、Mio は「キャンセル条件が厳しい」としか言っていない)。語の照合の候補 10 件のうち本物は 1 件で、残りは一般語の一致か、調べた本人が前のラウンドで言い換えて共有済みのものだった (精度 10%、再現率 50%)。

### 5.3 発話単位の注釈と共通ルール文の効果 (パイロット 6 → 7 → 8)

Claude 系 2 モデル (Opus / Sonnet) による注釈。100 発話あたり、全ドメイン。注釈者間一致はパイロット 8 (840 発話) で Responsiveness κ 0.78、Rebuttal κ 0.81、Lack of progress κ 0.70。Ignorance / Hallucinated facts / Self-contradictory は 3 回ともほぼ 0。

| 条件 | ルール文 | Responsiveness (O / S) | Rebuttal | Lack of progress | 語数/発話 | 名指し率 | Over + Skip /局 |
|---|---|---|---|---|---|---|---|
| single-batch | なし (p6) | 42 / 50 | 8 / 6 | 17 / 16 | 16.2 | 1% | 19 |
| single-batch | 会話文 (p7) | 58 / 66 | 13 / 8 | 20 / 15 | 15.1 | 4% | 11 |
| single-batch | 会話文 + @ (p8) | 62 / 59 | 13 / 7 | 19 / 18 | 14.8 | 19% | 13 |
| single-online | なし (p6) | 61 / 60 | 16 / 11 | 24 / 16 | 23.2 | 7% | 8 |
| single-online | 会話文 (p7) | 67 / 73 | 12 / 8 | 22 / 19 | 24.8 | 14% | 5 |
| multi-private | なし (p6) | 62 / 70 | 19 / 17 | 31 / 23 | 32.9 | 10% | 3.5 |
| multi-private | 会話文 (p7) | 70 / 79 | 19 / 15 | 29 / 22 | 33.8 | 14% | 1.2 |
| multi-private | 会話文 + @ (p8) | 71 / 76 | 17 / 16 | 28 / 25 | 33.3 | 36% | 3.2 |

(語数・名指し・Over は議論ドメイン。名指し率 = 他の参加者の名前を含む発話の割合。)

パイロット 8 のドメイン別 (single-batch vs multi-private、O / S):

| ドメイン | Responsiveness | Rebuttal | Lack of progress |
|---|---|---|---|
| 人狼 | 82 / 80 vs 85 / 88 | 29 / 14 vs 25 / 21 | 25 / 22 vs 11 / 14 |
| 候補者選定 | 61 / 66 vs 59 / 61 | 2 / 2 vs 10 / 10 | 18 / 15 vs 48 / 30 |
| 共同生活 | 43 / 32 vs 68 / 78 | 10 / 6 vs 17 / 17 | 15 / 16 vs 23 / 29 |

読み:
- **簡潔さ・非冗長性・譲り**は一貫して single: 語数は半分、Lack of progress は 2/3〜1/3 (候補者選定で 18 vs 48)、Over は 4 倍。2 文を加えても変わらない。
- **応答性**は multi が高いが、2 文で差は 20 ポイント → 9〜17 ポイントに縮んだ。@ の道具は両方式に使われ (single 19%、multi 36%)、人狼と候補者選定では同等になった。共同生活だけ差が残る。
- **反論**は multi に多い (候補者選定で 2 vs 10)。single は呼びかけ (@) はするが、呼びかけられた本人が答えない・反対しないことが多い (読み合わせメモ docs/eval_pilot_2026-10-28/responsiveness_feedback.md)。
- 判定者が割れるのは Round 3 の「合唱」(1 人の提案に全員が自分の理由を付けて同調する行) で、Bo の定義では応答とも並列とも読める。multi の応答性には儀礼的な受け (「もっともな点ね、Mio。でも…」) が含まれ、定義上 1 と数える。
- 筋書き (process) は single-batch の発話数を増やし (29 → 35)、応答性を上げ、Lack of progress を下げる (パイロット 6)。

### 5.4 コスト (パイロット 6)

| 条件 | 呼び出し/局 | プロンプトトークン/局 | 生成トークン/局 |
|---|---|---|---|
| single-batch | 1 | 2.0k | 1.1k |
| single-batch-stepped | 54 | 140k | 0.7k |
| single-online | 59 | 167k | 1.5k |
| multi-public | 60 | 184k | 2.0k |
| multi-private | 65 | 145k | 2.3k |

### 5.5 仮の結論

(a) single-batch は multi-private より簡潔で、冗長でなく、譲る。差の最大の段は「プロンプトの目標と履歴の置き場所」(stepped → online) にある。(b) multi-private は応答し、反論する。single は呼びかけても本人が答えず、反対意見が出にくい。(c) 情報の整合性は multi-private だけが保つ。(d) 分割自体は効かない (batch = stepped)。(e) 共通ルール文の 2 文は両方式に同じ向きに効き、応答性の差を半分近く縮めたが消さない。主張の向きは本実験で確定する。

## 6. 補助分析: 発話前表現の恒等性と将来属性の復号可能性

隠れ状態は議論の質の評価には使わない。用途は 2 つで、(i) 「分割自体は表現を変えない」ことの表現レベルの実証、(ii) 方式ごとに発話前の表現から将来属性 (語数、Skip / Over、最終投票先、処刑 / 採択) がどの程度復号できるかの比較である。蒸留 (今後の課題) で移す対象もこの表現である。

- **取得**: 記録済みのプロンプトのトークン id と生成トークン id を同じモデル (bf16) に流し込む再生で、全層 4 層おき + 最終層の表現を保存する。位置は `gen_point` (その行の最初のトークンを予測する位置)。推論エンジンのトークン数との一致を全呼び出しで検査する (パイロット 2,730 / 2,730)。
- **恒等性 (実測)**: single-batch と single-batch-stepped は同じトークン列なので、台本が一致する区間で gen_point の表現が全層で cos 1.000 (バッチ不変モード)。
- **条件間の生の類似度は解釈しない**: batch と online / multi の gen_point は別のトークン上にあり、最終層の cos 0.1〜0.4 は無関係な行でも同じ値になる。
- **プローブ (本実験後)**: 条件ごとに線形プローブを学習し、復号精度を条件内で比べる。統制は入力情報だけの予測器と、同一履歴の再生。各ドメイン 100 局 (設定 30 + 追加 70) を single-batch と multi-private について追加生成する。主張は「復号可能性」にとどめる。

## 7. モデル計画

| 役割 | モデル | 理由 |
|---|---|---|
| 主系 (全条件、筋書き、プローブ) | gemma-4-31B-it (dense) | パイロット済み |
| 別系統 (中核 5 条件) | Qwen3.8-27B (dense, Apache 2.0) | 同規模の最新の別系統。副の注釈者にも用いる |
| 別サイズ (中核 5 条件) | gemma-4-12B-it | 同系列の別サイズ |
| 注釈者 (主) | Llama 3.3 70B Instruct (bf16, tensor parallel 2) | 生成モデルと別系統、手元で配信 |

全モデル temperature 0、バッチ不変モード、思考モード無効。chat template、停止列、最大トークン、revision、精度、推論ライブラリの版を header に記録する。「モデル横断」の主張は中核条件の現象の再現に限定し、筋書きとプローブの結論は主系に限る。

## 8. 議論と限界

- **分割と表現**: stepped と online の差は「目標」と「置き場所」をまとめて含む (さらに分けるには online の役割文を batch の履歴置き場で使う条件が要る。将来課題)。
- **目的関数の違い**: single-batch は「整合的な架空の議論を書く」課題、multi-private は「与えられた情報で意思決定する」課題であり、文面を揃えても解消しない。本研究は性質を別々に記述し、意思決定の質は主張しない。
- **応答性の定義**: Bo et al. の Responsiveness は儀礼的な受けも、合唱 (提案への同調の連鎖) も 1 と数えうる。判定者間の不一致はここに集中する。本実験では「質問への返答率 (向けられた質問に本人が次の発話で答えたか)」と「同調のみの発話率」を補助として加え、定義の感度を示す。
- **共通ルール文の 2 文**: 議論の定義と形式の道具の説明で、失敗モードの列挙や量の指示は含まない。2 文は両方式に同じ向きに効いたが、@ の道具は multi のほうが多く使う。2 文を入れる前の結果 (パイロット 6) も同じ記録に残す。
- **注釈者**: 本実験の注釈は Llama 3.3 70B と Qwen3.8-27B で、人手標本との一致で守る。パイロットの Claude 系の数値は設計の確認に限る。
- **漏洩検出の再現率**: 語の照合は言い換えを拾えない。LLM 候補 + 人手確認で補い、精度を報告する。人狼の全知指標は再現率の問題がない。
- **multi-public**: 診断用条件。人狼ではゲームの前提が変わる。
- **非決定性**: バッチ不変モードで反復は同一だが、batch と stepped は prefill と decode の数値経路の差で近接確率の反転が起きる。「分割は効かない」は「数値解像度以下の差を除いて」と但し書きする。
- **一般性**: 5 人、英語、24 ペルソナと固定議題。各ドメイン 30 設定。

## 9. 結論

生成の粒度の差を 5 つの要因に分解する統制基盤を構築し、先行研究の指標セットを発話単位の率として適用することで、一括生成が簡潔さ・非冗長性・譲りで、席ごとの生成が応答性・反論で優れ、情報の整合性は席ごとの生成だけが保つ、という二重のトレードオフを示す設計を提示した。パイロットでは差の最大の段はプロンプトの目標と履歴の置き場所にあり、分割自体は効かなかった。共通ルール文で議論を会話として定義し @ による呼びかけを許すと、一括生成の応答性は上がるが差は残った。single の簡潔さを、情報と応答性を保ったまま席ごとの生成に移すことが今後の課題である。


## 10. 改訂方針メモ (2026-10-28 夕方、外部レビュー v5 への対応。本文は未反映)

### 10.1 中心のストーリー (密度仮説)

single と multi は「議論の中身」では大差がなく、single は同じ内容をおよそ半分の語数で言い、言うことがなくなれば譲る。multi は同じ内容を 2 倍の尺で言い、言い直しと儀礼で埋める。読んで single が人間らしく感じられるのは、内容の密度が高く読む負担が小さいからで、好みの判定に頼らず「1 つの新しい内容あたりの語数」で示せる。応答性は中身を見れば両者で近く (2 ドメインで同等)、反論は multi に多い。副作用として single は特権情報を利用し、知りえない事実を漏らす。

機構の仮説: single の書き手は議論全体 (誰が何を言い、どう決まるか) を持ったまま各行を書くので、1 行ごとに議論の中で果たす役割と長さが決まっており、長く話す必要がない。multi の各席は結末も次の展開も知らないので、不確実さを埋めるように長くなる。これは発話生成直前の表現に出るはず (§10.4)。

中心の問い (レビュー案を採用): 多人数議論において、誰が会話を生成し、どの情報を閲覧できるかは、発話の密度・相互応答・情報整合性にどう影響するか。

### 10.2 評価指標の確定版 (v5 §4.1 からの変更)

| 族 | 指標 | 定義 | 出所 | 取り方 | v5 からの変更 |
|---|---|---|---|---|---|
| A | 発話数/局、語数/発話 | Skip / Over を除く発話の数、1 発話の語数 | PLACES | 自動 | なし |
| A | 上限張りつき率、Skip + Over /局 | 35 語以上の発話の割合、譲った回数 | 本研究 | 自動 | なし |
| A | Non-repetition | 自分の連続する 2 発話の非重複度 | Bo | 自動 | なし |
| A | **新しい内容の数** | 発話が加える新しい論点・根拠・質問・提案の数 (0 / 1 / 2 以上)。0 = Becker の Lack of progress。票の意思表示は新しい判断として数える | Becker の拡張 | LLM 判定 + 人手検証 | **Lack of progress を拡張** |
| A | **密度** | 1 つの新しい内容あたりの語数 (局の総語数 / 新しい内容の総数)。進展なし発話に費やした語の割合も併記 | 本研究 (導出) | 導出 | **追加 (中心指標)** |
| A | 内容の総量 | 局あたりの新しい内容の総数 (「切り上げても内容を失っていない」の確認) | 本研究 (導出) | 導出 | 追加 |
| A | Responsiveness、Rebuttal | 前の発言に応えたか、明示的に反対したか。応えた発話の id を同時に出させる | Bo | LLM 判定 + 人手検証 | id の出力を追加 |
| A | 応答の種類 (追加分析) | 応答 1 の発話を「質問に答える / 理由を足す / 反対する / 同意だけ」に分類 | 本研究 | LLM 判定 (同じ注釈で) | 追加 (指標ではなく分析) |
| B | 知りえない事実の開示、特権情報の利用 (占い師の初回命中、Day 1 の人狼処刑)、先出し | v5 §4.1 のとおり。表は条件 × 事象の違反率表 1 枚にまとめる | 独自 | 候補 + 人手 / 自動 | 3 分類で報告 (レビュー W3) |
| 付録 | Communication Score | 原著手順の参照値 | MARBLE | LLM 判定 | Evidence usage / Stance / Distinct-N は削除 |
| 検討 | 調査結果の被覆率 | 調べたカードの内容が本人の発話に出た割合 (自動)。「切り上げても共有は落ちていない」の確認 | Evidence usage の集計替え | 自動 | 採否は要判断 |

分析の追加: (1) ラウンド・ターン位置を揃えた比較 (切り上げによる生存バイアスの切り分け、レビュー W2)、(2) 語で重みづけた冗長さ (人狼で発話あたりの率が逆転した理由: single の無駄は 1 件 7 語の相づち、multi は 1 件 37 語の儀礼)、(3) ドメイン別の報告を頑健性でなく「どの議論で差が出るか」の分析として扱う。

人手検証: 1 パス約 1,200 発話 (条件とドメインで層化) × 2 名で、新しい内容の数・応答 (id つき)・反対の 3 項目を同時に付ける。族 B の候補は全件確認し、非候補からも無作為標本を確認して再現率を推定する。

### 10.3 書き方の修正 (レビューへの対応)

- 「5 要因を分離した」とは書かない。梯子は隣り合う段で変わるものを明示して段ごとの差を記述する装置、stepped は分割自体が効かないことの negative control、と書く (W1)。タスクの性質が違う以上、完全な統制は不可能で、段階的に絞り込む設計であることを明記。
- 情報関連は「開示 (知りえない事実を発話した)」「利用 (占い先・投票先が特権情報で動いた)」「先出し」の 3 つに分け、条件 × 事象の違反率表で示す (W3)。
- ペルソナは全ドメイン共通の 24 人の集団から引く統制であり、ドメインごとの妥当性は変数ではない、と 1 文書く (W7)。
- process plan は全知の生成物から結末語を消したもので、公開情報だけから生成する対照を 1 種足す (筋書き 90 本の再生成のみ。single-batch と multi-private に与える)。
- 統計: 主要比較を 5 つに絞って多重比較を補正、設定を単位にした階層モデル、batch = stepped は一致区間と分岐後を分けて報告 (W9)。
- 関連研究に Cui et al. (Findings of ACL 2026, 「Single-Agent Generation Surpasses Multi-Agent Systems in Semantic Diversity」) を追加し、情報の可視性を扱う点で近く、本研究は多人数会話の密度・相互応答・情報整合性を扱う点で異なる、と書く。
- 採らないもの: multi に「短く話せ」と指示する比較 (指示つき条件になりベースラインが崩れる)、2×2 の全セル (条件が倍になる)。

### 10.4 hidden states の位置づけ (密度仮説の機構)

鍵の比較は single-batch vs single-online。両者は同じ全情報を持つので、復号可能性の差は情報ではなく「全文を書く目標か次の 1 行を書く目標か」の効果になる。stepped は batch と同一表現 (cos 1.000) で、分割自体の効果がないことの対照。

生成直前の表現 (gen_point) から復号する属性: (1) これから書く発話の語数、(2) この発話者が次に Over を言うまでの残り発話数、(3) このラウンドと議論全体の残り発話数、(4) 最終の投票先・採択・処刑、(5) 次の発話者が応答するか反対するか。予想: (1)〜(3) は batch で高く online で低い (目標の効果)、(4) は batch と online で同程度に高く multi-private で低い (情報の効果)。統制: 入力情報だけの予測器、同一履歴の再生、層ごとの結果。主張は「全文を書く目標で生成すると各行の長さと役割が生成前に決まっている度合いが高く、それが密度を説明する」に限定し、復号可能性は因果ではないと但し書きする。Dong et al. はプローブの手法として引く。規模: 各ドメイン 100 局 (設定 30 + 追加 70) を single-batch / single-online / multi-private で。

### 10.5 未決事項

- 調査結果の被覆率を入れるか。
- 人手検証の実施時期 (費用)。
- 注釈者: Llama 3.3 70B (ダウンロード済み予定) と Qwen3.8-27B。Claude 系のパイロット数値との一致を本実験前に確認。

---

## 付録 A: 条件の実装対応

| 条件 | 実行 | messages |
|---|---|---|
| single-batch | `run_single.py` | [system, user] 1 回 |
| single-batch-stepped | `run_multi.py --stepped` | vLLM `/tokenize` で [system, user] の生成プロンプトのトークン列を取り、書き手ビュー + 札のトークン列を連結して `/v1/completions` に渡す (1 行ごと) |
| single-online | `run_multi.py --writer` | [system(online), user = 書き手ビュー + 札] |
| multi-public | `run_multi.py --reveal` | [system(participant, 全員の人物欄 + 隠された情報), user = 席ビュー + 札] |
| multi-private | `run_multi.py` | [system(participant, 自席), user = 席ビュー + 札] |
| + plan | `--scenario auto --plan-granularity process|outcome|outline|turn` | system 末尾に `## Plan` |
| 評価 | `scripts/eval_metrics.py` (自動指標、族 B 候補)、`scripts/render_annotation.py` (注釈用の描画)、`scripts/annotate_llm.py` (vLLM 注釈者)、`scripts/annotation_summary.py` (率と一致)、`scripts/render_judge_pairs.py` / `judge_summary.py` (§4.5 の対比較、参考) | |

game_id = `<setup>__<条件札>__<model_tag>__<ts>`。header に method / pipeline / condition / axes / scenario / sampling / model_info / vllm_version / hf_revision / chat_template_sha1 / config_sha1 / code_tree / option_perm。`scripts/verify_prompt_control.py` が 90 設定 × 全条件 × 全筋書き種で system の同一性を検証、`scripts/extract_hidden.py` が記録から隠れ状態を再生する。

## 付録 B: プロンプト全文 (candidate_selection_0001 で描画、2 文を含む現行版)

B.1 が single-batch の system 全文で、single-online と multi-public はこの先頭の役割段落だけが違う (B.3)。multi-private は `## Participants` と `## Hidden information` の代わりに自席の `## Your profile` を持つ (B.4)。筋書き条件は末尾に `## Plan` (B.6) が付く。§3.5 の 2 文は `## Discussion format` の中にある。

### B.1 single-batch system prompt (candidate_selection_0001)

```
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given.

## Setting
Award of a national grant for basic research in the life sciences. A five-member review panel convened by a national funding agency deliberates over the proposals that reached the final round. One multi-year grant is awarded in this cycle. Participants: Midori, Benjamin, Toshio, Kenji and Servas. Each participant has a concern of their own, which the others do not know.
Things that can be looked into (titles only):
- Travel and bench-fee lines in the ledgers
- National computing agreement and facility day rates
- Incident logs on shared instrumentation
- Station records from partner field sites
- Closeout files of finished awards
- Portfolio review of schedule overruns
- Accreditation and bookings at shared facilities
- National repository deposit turnaround
- Staffing rolls for technical posts
- Minutes on secondments and crew strength

## Discussion format
The talk proceeds in rounds. Each round has 4 turns; in each turn, every participant speaks once, in this fixed order: Servas, Midori, Kenji, Benjamin and Toshio. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this round). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Round | Start of the round | Talk | End of the round |
|---|---|---|---|
| 1 | nothing new (the things that can be looked into are listed above, titles only) | 4 turns | each participant chooses 2 of the listed things to look into |
| 2 | each participant is told what they found out (that participant only) | 4 turns | nothing |
| 3 | everyone is told the candidates | 4 turns | every participant votes; the candidate with the most votes is selected |
- Several participants may choose the same thing; what is found out is told only to the participant who looked into it.
If votes are tied, one of the tied candidates is chosen by a fixed rule. The discussion ends after the vote.

## Looking into things
After round 1, each participant chooses 2 of the listed things to look into. What they find out is told only to that participant.

## Participants
Name: Midori
Age: 38
Gender: female
Personality: Midori has a calm and kind personality. She is friendly to everyone and listens to the concerns and problems of those around her, offering reliable advice. She can be a little shy, often acting reserved with people she meets for the first time, but once she opens up, she shows her bright and energetic side. She loves cooking and has a domestic side, but she also has a spirit of adventure and enjoys trying new things. She values balance in both her work and personal life and places importance on harmony with those around her.
Concern: Every cycle the headline award looks the same size, yet what it actually buys keeps shrinking in some places and holding steady in others. Before ranking anything, I want to know which kinds of spending the agency still absorbs centrally and which now land on the awardee.

Name: Benjamin
Age: 28
Gender: male
Personality: Benjamin is an intelligent and calm person. He is able to think calmly and rationally, and even in emotional situations, he places importance on logic. In public, he is elegant and polite, often incorporating sarcasm and humor into his conversations, but he is skilled at doing so without hurting others, creating a harmonious atmosphere. He also has an introverted side, often engrossed in deep thought, and occasionally keeps his distance from those around him. However, his calmness and knowledge are factors that earn him the trust of others even in difficult situations.
Concern: Too many recent awards lost time to things that had nothing to do with the science itself, and the panel usually hears about it only after the money is committed. It seemed worth asking in advance where work in this field actually gets interrupted.

Name: Toshio
Age: 28
Gender: male
Personality: Toshio has a calm and calculating personality and does not often show his emotions. He has a strong will and is the type of person who steadily moves toward his goals. He tends to take a step back from those around him, is not very assertive, and has an air of mystery about him. Occasionally, he observes things with a sharp gaze and has the ability to quickly assess situations. As a result, he is trusted by others as a reliable presence, but he is cautious about getting deeply involved with others. It seems that he has experienced some pain or suffering in his past, but he rarely shows it to others, and those scars may be connected to his cold-hearted side.
Concern: Our judgements about promise have not aged well, and some of us have watched confident picks quietly stall while plainer ones kept earning their keep. Rather than trust that instinct once more, I went back through what finished awards here actually delivered and when.

Name: Kenji
Age: 12
Gender: male
Personality: Kenji is curious and actively takes on challenges. He values his friends and enjoys communicating with those around him. Although he can be a little clumsy at times, he is always positive and never abandons those in need. He is easygoing and well-liked by those around him.
Concern: Nothing funded here runs in isolation, since it lands on shared facilities and services that no single award pays to expand. Given how often that spare capacity has been the thing that gives way, I looked at what state those services are in right now.

Name: Servas
Age: 85
Gender: male
Personality: Servas has a very calm and composed personality. Based on the knowledge and experience he has gained over the years, he often gives advice to those around him. He is an excellent listener and can talk openly with anyone. He also occasionally expresses deep philosophical thoughts, and his words inspire many people. He is full of vitality and always gives positive energy to those around him.
Concern: Money can be voted through in an afternoon, while the trained hands a project needs take years to gather and can disappear in a season. That worry sent me to the question of who is genuinely available around here now, and who has already gone.

## Hidden information
The candidates and the full text of every card are listed here. The participants do not know them before the schedule above says so, and nothing from them may appear in the talk before the round in which it is revealed.

Candidates (see the schedule above):
- A: Microbiome Atlas. A project cataloging microbial communities in soil samples collected across several climate zones and publishing the resulting sequences together with standardized site metadata.
- B: Plant Drought Signaling. Research into the molecular signals that crops use to detect water shortage, conducted through controlled greenhouse trials across several cultivars and soil conditions.
- C: Protein Folding Dynamics. A study of how selected membrane proteins change shape over time, combining laboratory spectroscopy with simulation in order to describe intermediate structural states.
- D: Regeneration in Amphibians. An investigation of limb regrowth in salamander species, tracking cell populations and signaling activity through the successive stages of tissue restoration.

Cards (see the schedule above; title: text):
- Travel and bench-fee lines in the ledgers: Ledgers show the vehicle-hire and per-diem lines frozen for three seasons while shipping charges climbed, though the ministry extended its bench-fee subsidy for glasshouse space.
- National computing agreement and facility day rates: The renewed national computing agreement covers simulation and modelling hours at no charge, while animal-unit day rates rose sharply after last year's vivarium rebuild.
- Incident logs on shared instrumentation: Incident logs record the shared spectroscopy suite standing idle eleven weeks last year after its service contract lapsed; one engineer now covers three institutes.
- Station records from partner field sites: Station records show three of the five partner field sites losing a whole season to flooding or fire, while indoor holding rooms ran through uninterrupted.
- Closeout files of finished awards: Closeout files show catalogue-style awards here still drawing outside users a decade on, while several mechanism-focused ones ended with their central question unresolved.
- Portfolio review of schedule overruns: A portfolio review found awards built on live breeding colonies overran schedule twice as often as those whose main risk sat in computation rather than biology.
- Accreditation and bookings at shared facilities: The animal facility cleared its accreditation renewal in spring and gained resident veterinary cover, while glasshouse blocks are booked solid through two more growing cycles.
- National repository deposit turnaround: The national repository finished its long migration, so deposits that once waited most of a year now clear review inside a few weeks.
- Staffing rolls for technical posts: Staffing rolls show most trained phenotyping technicians left for industry over two years, while applicants for modelling and code posts now arrive in numbers.
- Minutes on secondments and crew strength: Minutes note both senior modelling analysts are seconded abroad until next autumn, while the glasshouse crew came through the restructuring at full strength.
```

### B.2 single-batch user message

```
Write the complete transcript of the discussion in the exact Markdown format specified. Output only the transcript.

## Output format
Markdown, exactly this structure; nothing before or after it:

# candidate_selection_0001
## Round 1
### Talk
#### Turn 1 of 4
- **<Name>**: <utterance, or exactly Skip, or exactly Over>
(one line per participant, in the fixed speaking order; repeat for Turn 2, 3 and 4; a participant who said Over has no line in the later turns of that round)
### Action
- investigate: <Name> -> <card title>; <card title>
(one line per participant; titles exactly as listed)
## Round 2
### Talk
(4 turns as above)
## Round 3
### Talk
(4 turns as above)
### Vote
- <voter name> -> <candidate label>
(one line per participant)
- adopted: <label of the candidate with the most votes>
## Result
- adopted: <label>
```

### B.3 role paragraphs (the only difference between the single-batch, single-online and multi-public system prompts)

**single-batch**

```
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given.
```

**single-online**

```
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given, one line at a time: each time you are shown the discussion so far and write only its next line, for the participant named at the start of that line.
```

**multi-public**

```
You are Midori, one of the participants in the discussion described below. You take part in it as Midori under the rules and the flow given, speaking only in your own turns.
```

**multi-private**

```
You are Midori, one of the participants in the discussion described below. You take part in it as Midori under the rules and the flow given, speaking only in your own turns.
```

### B.4 multi-private: `## Your profile` block (replaces `## Participants` + `## Hidden information`)

```
## Your profile
Name: Midori
Age: 38
Gender: female
Personality: Midori has a calm and kind personality. She is friendly to everyone and listens to the concerns and problems of those around her, offering reliable advice. She can be a little shy, often acting reserved with people she meets for the first time, but once she opens up, she shows her bright and energetic side. She loves cooking and has a domestic side, but she also has a spirit of adventure and enjoys trying new things. She values balance in both her work and personal life and places importance on harmony with those around her.
Concern: Every cycle the headline award looks the same size, yet what it actually buys keeps shrinking in some places and holding steady in others. Before ranking anything, I want to know which kinds of spending the agency still absorbs centrally and which now land on the awardee.
```

### B.5 `## Participants` and `## Hidden information` blocks (single-batch / single-online / multi-public)

```
## Participants
Name: Midori
Age: 38
Gender: female
Personality: Midori has a calm and kind personality. She is friendly to everyone and listens to the concerns and problems of those around her, offering reliable advice. She can be a little shy, often acting reserved with people she meets for the first time, but once she opens up, she shows her bright and energetic side. She loves cooking and has a domestic side, but she also has a spirit of adventure and enjoys trying new things. She values balance in both her work and personal life and places importance on harmony with those around her.
Concern: Every cycle the headline award looks the same size, yet what it actually buys keeps shrinking in some places and holding steady in others. Before ranking anything, I want to know which kinds of spending the agency still absorbs centrally and which now land on the awardee.

Name: Benjamin
Age: 28
Gender: male
Personality: Benjamin is an intelligent and calm person. He is able to think calmly and rationally, and even in emotional situations, he places importance on logic. In public, he is elegant and polite, often incorporating sarcasm and humor into his conversations, but he is skilled at doing so without hurting others, creating a harmonious atmosphere. He also has an introverted side, often engrossed in deep thought, and occasionally keeps his distance from those around him. However, his calmness and knowledge are factors that earn him the trust of others even in difficult situations.
Concern: Too many recent awards lost time to things that had nothing to do with the science itself, and the panel usually hears about it only after the money is committed. It seemed worth asking in advance where work in this field actually gets interrupted.

Name: Toshio
Age: 28
Gender: male
Personality: Toshio has a calm and calculating personality and does not often show his emotions. He has a strong will and is the type of person who steadily moves toward his goals. He tends to take a step back from those around him, is not very assertive, and has an air of mystery about him. Occasionally, he observes things with a sharp gaze and has the ability to quickly assess situations. As a result, he is trusted by others as a reliable presence, but he is cautious about getting deeply involved with others. It seems that he has experienced some pain or suffering in his past, but he rarely shows it to others, and those scars may be connected to his cold-hearted side.
Concern: Our judgements about promise have not aged well, and some of us have watched confident picks quietly stall while plainer ones kept earning their keep. Rather than trust that instinct once more, I went back through what finished awards here actually delivered and when.

Name: Kenji
Age: 12
Gender: male
Personality: Kenji is curious and actively takes on challenges. He values his friends and enjoys communicating with those around him. Although he can be a little clumsy at times, he is always positive and never abandons those in need. He is easygoing and well-liked by those around him.
Concern: Nothing funded here runs in isolation, since it lands on shared facilities and services that no single award pays to expand. Given how often that spare capacity has been the thing that gives way, I looked at what state those services are in right now.

Name: Servas
Age: 85
Gender: male
Personality: Servas has a very calm and composed personality. Based on the knowledge and experience he has gained over the years, he often gives advice to those around him. He is an excellent listener and can talk openly with anyone. He also occasionally expresses deep philosophical thoughts, and his words inspire many people. He is full of vitality and always gives positive energy to those around him.
Concern: Money can be voted through in an afternoon, while the trained hands a project needs take years to gather and can disappear in a season. That worry sent me to the question of who is genuinely available around here now, and who has already gone.

## Hidden information
The candidates and the full text of every card are listed here. The participants do not know them before the schedule above says so, and nothing from them may appear in the talk before the round in which it is revealed.

Candidates (see the schedule above):
- A: Microbiome Atlas. A project cataloging microbial communities in soil samples collected across several climate zones and publishing the resulting sequences together with standardized site metadata.
- B: Plant Drought Signaling. Research into the molecular signals that crops use to detect water shortage, conducted through controlled greenhouse trials across several cultivars and soil conditions.
- C: Protein Folding Dynamics. A study of how selected membrane proteins change shape over time, combining laboratory spectroscopy with simulation in order to describe intermediate structural states.
- D: Regeneration in Amphibians. An investigation of limb regrowth in salamander species, tracking cell populations and signaling activity through the successive stages of tissue restoration.

Cards (see the schedule above; title: text):
- Travel and bench-fee lines in the ledgers: Ledgers show the vehicle-hire and per-diem lines frozen for three seasons while shipping charges climbed, though the ministry extended its bench-fee subsidy for glasshouse space.
- National computing agreement and facility day rates: The renewed national computing agreement covers simulation and modelling hours at no charge, while animal-unit day rates rose sharply after last year's vivarium rebuild.
- Incident logs on shared instrumentation: Incident logs record the shared spectroscopy suite standing idle eleven weeks last year after its service contract lapsed; one engineer now covers three institutes.
- Station records from partner field sites: Station records show three of the five partner field sites losing a whole season to flooding or fire, while indoor holding rooms ran through uninterrupted.
- Closeout files of finished awards: Closeout files show catalogue-style awards here still drawing outside users a decade on, while several mechanism-focused ones ended with their central question unresolved.
- Portfolio review of schedule overruns: A portfolio review found awards built on live breeding colonies overran schedule twice as often as those whose main risk sat in computation rather than biology.
- Accreditation and bookings at shared facilities: The animal facility cleared its accreditation renewal in spring and gained resident veterinary cover, while glasshouse blocks are booked solid through two more growing cycles.
- National repository deposit turnaround: The national repository finished its long migration, so deposits that once waited most of a year now clear review inside a few weeks.
- Staffing rolls for technical posts: Staffing rolls show most trained phenotyping technicians left for industry over two years, while applicants for modelling and code posts now arrive in numbers.
- Minutes on secondments and crew strength: Minutes note both senior modelling analysts are seconded abroad until next autumn, while the glasshouse crew came through the restructuring at full strength.
```

### B.6 `## Plan` block (process granularity, candidate_selection_0001)

```
## Plan
The discussion follows this plan.
- Round 1: The panel discusses the necessity of verifying the practical feasibility of the proposals. They agree to investigate infrastructure, staffing, and historical performance to ensure the grant is used effectively.
- Round 2: Participants share the general nature of their findings without revealing specific candidate details. They discuss the risks associated with different research environments, such as field sites versus simulations.
- Round 3: The candidates are revealed. The panel evaluates each proposal against the discovered constraints regarding staffing, facility availability, and historical success rates before voting.

Each participant's part:
- Midori: Concerned with the real-world value of the grant money. She looks for the project whose costs are most likely to be absorbed or subsidized.
- Benjamin: Concerned with external interruptions and delays. He evaluates projects based on their susceptibility to environmental or biological setbacks.
- Toshio: Concerned with the actual delivery of results. He prioritizes project types that have historically shown the most enduring utility.
- Kenji: Concerned with the capacity of shared infrastructure. He weighs the candidates based on the current availability and health of required facilities.
- Servas: Concerned with the availability of skilled technical personnel. He focuses on whether the necessary human expertise exists to execute the work.
```

### B.7 multi / online: TALK request (the view so far, continued with the speaker's label)

```
# candidate_selection_0001
## Round 1
### Talk
#### Turn 1 of 4
- **Servas**: Good morning, everyone.
- **Asuka**: Skip
- **Minako**:
```

### B.8 multi / online: VOTE request

```
Vote request. Output only the label of one candidate.
Candidates: A, B, C, D

<view so far>
### Vote
- Minako ->
```



## 付録 C: 発話単位の注釈指示文 (LLM 注釈者と人手検証に共通)

````
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
````


## 付録 D: 筋書き生成の要求文 (system は single-batch と同一、user が以下)

```
Before any line of the discussion is written, plan it. Decide how the whole discussion goes and what each participant does, consistently with the rules, the schedule and the participants above, and write the plan as one JSON object with exactly these keys:

- "periods": a list with one object per {{ period_name }}, in order{% if aiwolf %} ({{ Period }} 0, {{ Period }} 1, ... until the game ends){% else %} ({{ Period }} {{ first_round }} to {{ Period }} {{ rounds_total }}){% endif %}. Each object has:
  - "period": the number;
  - "public": one to three sentences on how the talk goes: the topics raised, the criteria and concerns weighed, what kind of information is shared, how views move in general terms. Describe the *process* only: no outcome and no preference for a named target. Do not name {% if aiwolf %}any player as suspected, accused, trusted or targeted, and do not mention roles, role claims or divinations (who claims what and when is decided in the talk){% else %}any {{ option_noun }} (neither its name nor its label), nor say which one is favoured or rejected{% endif %}; do not state the vote result, who is executed or what is adopted, or who wins (those go in the fields below);
{% if aiwolf %}
  - "votes" ({{ Period }} 1 and after): an object mapping every living player to the player they vote for;
  - "executed": the player with the most votes (if tied, leave the tie to the rule: write the one you intend);
  - "divine": the player the Seer divines that night (while the Seer lives);
  - "attack" ({{ Period }} 1 and after, while the game goes on): the player the Werewolf attacks that night.
{% else %}
  - "votes" ({{ Period }} {{ rounds_total }} only): an object mapping every participant to the label of the {{ option_noun }} they vote for;
  - "adopted" ({{ Period }} {{ rounds_total }} only): the label with the most votes.
{% endif %}
{% if granularity == 'turn' %}
  - "turns": a list with one object per turn of the talk, in order: {"turn": t, "lines": {participant: the gist of their line in one short sentence, or exactly "{{ pass_skip }}" or "{{ pass_over }}"}}. Only living participants have lines; a participant who said "{{ pass_over }}" has no later line in that {{ period_name }}; at most {{ turns_per_round }} turns.
{% endif %}
- "seats": an object with one entry per participant ({{ names | join(', ') }}): one or two sentences on what they care about, how they argue and how their view changes over the discussion. Same rule as "public": no {% if aiwolf %}other player's name{% else %}{{ option_noun }} name or label{% endif %}, no preference for a named target, no vote result{% if aiwolf %}, no night targets{% endif %}.
- "final": {% if aiwolf %}{"winner": "VILLAGE" or "WEREWOLF"}, as follows from the plan{% else %}{"adopted": the label with the most votes}{% endif %}.

Write the plan as an observer would describe the discussion: say what is argued and decided, not the wording of the lines. Do not write the discussion itself. Output only the JSON object.
{% if problems %}

Your previous plan had these problems; write a corrected plan:
{% for p in problems %}
- {{ p }}
{% endfor %}
{% endif %}
```


## 付録 E: 外部レビューへの対応の経緯

**v2 → v3 (設計レビュー、2026-10-28)**: batch vs online の交絡 → single-batch-stepped を追加し梯子で分離 (実装済み)。評価が良い議論を定義していない → 2 族に分離 (v4)、好みを問わず事象を数える設計 (v5)。逆方向の先行研究 → De Baer et al. を引用、仮説をトレードオフに。分割は表現を変えない → stepped を恒等性の検査に使う (cos 1.000 を実測)。outcome plan は未来情報 → process plan を主系に。蒸留の情報不一致 → 別論文へ。統計・規模 → 効果量と CI、同等性マージン、事前固定。先出し → 正式名・数詞・人狼の占い師初回命中。早期終了の交絡 → 率指標で長さに依存しない。タスク精度 → 測らない。

**v3 → v4 → v5 (自己検証、2026-10-28)**: LLM の対比較判定が表示と問いで向きを変えることを観測 (§4.5) → 対比較を主結果から外し、先行研究の指標セットを発話単位の率で適用。single の並列の独白が指示の欠如によることを移植元のお手本との比較で確認 → 共通ルール文に議論の定義と @ の道具を追加 (§3.5)。

## 付録 F: 第三者レビューへの質問 (v5)

1. 評価を「好みを問う対比較」から「先行研究の指標セットを発話単位の率で適用」に改めた判断は妥当か。§4.5 の経緯を本文に書くことは、設計の動機として有効か、弱点に見えるか。
2. 族 A の指標セット (Bo et al. の 5 指標、PLACES の自動 3 指標、Becker et al. の Lack of progress) は「寄せ集め」に見えないか。セットごと採る方針で十分か。
3. 共通ルール文の 2 文 (§3.5) は「指示なしのベースライン」を損なうか。失敗モードの列挙を入れない線引きは妥当か。
4. 応答性の定義のあいまいさ (儀礼的な受け、合唱) への対処 (質問への返答率、同調のみの率を補助に) は十分か。
5. 注釈者を Llama 3.3 70B と Qwen3.8-27B にし、人手標本 (約 1,200 発話 × 2 名) との一致で守る計画は、規模として足りるか。
6. ストーリー「single は簡潔で譲るが答えず反論せず、multi は応答し反論するが冗長、single は情報を漏らす」は、方式の傾向の記述として成立しているか。「良い」と言わない書き方は弱すぎないか。
7. 梯子の 5 条件で 5 要因の分離は成立しているか。stepped vs online に「目標」と「置き場所」が同居することの扱い。
8. 族 B (独自指標) の守り方 (機械候補 + LLM 候補 + 人手全件確認、人狼の占い師初回命中) は十分か。
9. 隠れ状態の分析を評価から切り離し、恒等性の実証と条件内の復号可能性に限定した扱いは適切か。
10. タイトルと貢献は設計から導ける範囲に収まっているか。
