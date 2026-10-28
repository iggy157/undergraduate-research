# 論文シナリオ草稿 v4 (査読耐性の確認用、2026-10-28)

> **注意**: 本実験前の草稿です。§5 の数値は**パイロット 6 の実測** (gemma-4-31B-it、各ドメイン 3 設定、72 局) で、規模が小さいため「仮の結果」と明記しています。本実験 (各ドメイン 30 設定) で置き換えます。v3 からの主な変更: (1) 仮説を「single は会話として人間らしく、テンポが良く、冗長でない。一方で全知の書き手が知らないはずの情報を混ぜる副作用がある」という**非対称なトレードオフ**に書き直した。(2) 評価を「良さ」と「副作用」の 2 族に分け、合成しない。(3) 人手評価の問いを Samanta et al. の「実際の人間の議論に見えるのはどちらか」1 問 + 理由の自由記述にし、6 軸採点をやめた。(4) 自動指標を 5 つ (借用 2、記述 1、独自 2) に絞った。(5) 予備評価 (docs/preliminary_eval_2026-10-28/) で LLM 判定が長さに引きずられて向きが逆転した経緯と、その修正を §4.5 に書いた。(6) 付録に全プロンプトと判定指示文を載せた。

---

## タイトル案

第一候補: **Writing the Whole Conversation: A Single LLM Produces More Human-Like Multi-Party Discussion than Per-Agent Generation, at the Cost of Information Leakage**

第二候補: **Batch or Line by Line? Disentangling What Makes LLM Multi-Party Discussion Human-Like**

日本語仮題: 台本を一括で書くと議論は人間らしくなるか: 単一 LLM による台本生成とマルチエージェント生成の統制比較

## 概要

LLM に複数人の議論を生成させる方法には、1 つの LLM が台本全体を一括で書く方法 (single) と、参加者ごとに独立した LLM を置いて 1 発話ずつ対話させる方法 (multi) がある。本研究は、同一モデル・同一ルール文・同一台本文法・同一の情報公開スケジュールのもとで差分を設計した軸だけに絞った比較基盤を構築し、3 ドメイン (人狼、候補者選定、共同生活の取り決め) × 各 30 設定で 5 条件 (single-batch / single-batch-stepped / single-online / multi-public / multi-private) を比べる。隣り合う条件の差はそれぞれ「結末と構造の決め手」「プロンプトの目標と履歴の置き場所」「文脈の分割」「情報量」に対応する。評価は「会話としての質」と「情報の整合性」を別の族として測る。前者は、条件を伏せた対比較で「実際の人間の議論に見えるのはどちらか」を人手で問い (理由を自由記述)、発話長・語数上限への張りつき・反復の自動指標を添える。後者は、知らないはずの情報 (他者の調査結果・役職) の使用と公開前の選択肢名の出現を機械照合と人手確認で数える。パイロット (各ドメイン 3 設定) では、single-batch は multi-private より短く (15 語 vs 33 語)、語数上限への張りつきがなく (0% vs 38%)、Skip / Over で話すことのないターンを畳み、LLM 判定 2 系統の対比較で「人間の議論らしい」とされる率が高かった (0.69)。一方で、人狼では全知の書き手の占い師が初回の占いで必ず人狼を当て (1.00 vs 偶然 0.25、multi-private は 0.00)、議論ドメインでは他者の調査結果を言い換えて使う発話が single にのみ確認された。本研究はこの非対称なトレードオフを示し、single の会話としての長所を情報の整合性を保ったまま multi に移すこと (蒸留) を今後の課題とする。

## 1. はじめに

LLM を用いた多人数議論の生成は、社会シミュレーション、対話データの合成、ゲーム AI に使われる。生成の仕方には、1 回の生成で議論全体を書き下ろす中央集権的な方法と、各参加者を独立した LLM にして逐次に応答させる分散的な方法がある。前者は整合的な台本を書きやすく、後者は参加者が互いに反応する対話になりやすい、と言われるが、既存の比較は方式ごとにプロンプトや進行手続きが異なり、どの差がどの性質を生むのかを特定できない。面接対話では対話エージェント方式が一括生成より高く評価されたという報告 (De Baer et al., GEM 2025) もあり、「どちらが良いか」は設定と観点に依存する。

本研究の問いは「一括生成と逐次生成は、議論のどの性質に対してそれぞれ長所と短所を持ち、その差は何によって生じるか」である。自己回帰モデルでは、同じトークン列を一度に生成しても、1 行ずつ止めて同じ接頭辞から再開しても、greedy なら同じ続きが出る。したがって「一括か逐次か」の差は、生成を分割すること自体ではなく、(1) プロンプトの目標、(2) 履歴の置き場所、(3) 結末と構造の決め手、(4) 文脈の分割、(5) 情報量のどこかから生じる。本研究はこの 5 つを 1 つずつ変えた条件を並べて測る。

本稿が主張したいことは次の 2 点であり、評価設計はこの 2 点を**別々に**測れるように組む。

- **会話としての質**: 一括生成は、発話の長さが場面に応じて変わり、語数上限に張りつかず、話すことがなければ Skip / Over でターンを畳む。結果として議論のテンポが良く、人間の会話らしくなる。逐次の席ごとの生成は、ターンが残る限り上限いっぱいまで話し、定型の挨拶と自分の立場の言い直しで埋める。
- **情報の整合性 (副作用)**: 一括生成の書き手は全員の秘密を知っているため、参加者が知らないはずの情報 (他者の調査結果、役職、未公開の選択肢) を発話に混ぜる。複雑なタスクに適用するには、生成物にこの種の不整合がないかの確認が必要である。

両者を 1 つの点数に合成すると相殺して見えなくなるので、本稿は 2 族を別の表として示し、どちらを優先するかは用途に委ねる。single の会話としての長所を、情報を揃えた multi に移す (蒸留) ことは本稿の範囲外の今後の課題とし、基盤はそれを見据えて設計する。

**研究課題**

- RQ1 (会話としての質): 一括生成は逐次生成より人間の議論らしいか。差は梯子のどの段 (結末の決め手 / 目標と置き場所 / 文脈の分割 / 情報量) で生じるか。
- RQ2 (情報の整合性): 全知の書き手はどの程度、知らないはずの情報を発話に混ぜるか。情報を揃えた席ごとの生成 (multi-private) でそれは消えるか。
- RQ3 (計画と頑健性): 結末を含まない筋書きは、両方式の性質をどう変えるか。傾向はドメインとモデルを変えても再現するか。

**貢献**: (1) 差分を設計した軸だけに絞った比較基盤 (共通ルール文・共通台本文法・席ビューと書き手ビューの決定的復元・違反と正規化の共通記録・推論エンジンが見たトークン id の記録・バッチ不変モードによる決定的な再現)。(2) 5 条件で 5 要因を 1 つずつ分離する実験設計と、分割自体が効かないことの実証。(3) 「会話としての質」と「情報の整合性」を分けた評価設計と、長さに依存しない指標の選定。(4) 一括生成が人間の議論らしさで優れ、情報の整合性で劣るという非対称なトレードオフの提示。(5) 全知の書き手による未公開情報の漏洩 (先出し・他者の秘密の使用・全知の占い) の定量化。

## 2. 関連研究

**LLM マルチエージェント議論・ゲーム**: 複数 LLM の討論による推論の改善 (Du et al., 2023)、役割分担による協調 (Li et al., 2023, CAMEL)、生成エージェントによる社会シミュレーション (Park et al., 2023)。人狼については LLM エージェントの経験学習 (Xu et al., 2023) と人狼知能大会 (AIWolf / aiwolf-nlp)。

**single と multi の比較**: 面接対話で一括生成と 2 エージェント対話を比べ、LLM 判定では対話方式が高く、トークン数は約 6 倍だった研究 (De Baer et al., GEM 2025)。最後通牒ゲームでの single と multi の人間行動再現の比較 (Sreedhar & Chilton, HICSS 2025)。multi-agent debate の優位が single-agent ベースラインに対して不安定であることを示した研究 (Zhang et al., 2025)、議論の構造的・認知的要因を操作した統制研究 (Wu et al., 2025)。本研究は多人数の自然言語対話の生成を対象に、5 つの要因を 1 つずつ分離する点で異なる。

**多人数対話の評価**: 人手評価では PLACES (Chen et al., 2023) の Natural / Coherent / Consistent と、多人数固有の次元 (誰に話しているか分かるか、参加が均等か)。LLM 判定については Samanta et al. (ACL 2026) が多人数対話で「実際の人間が言いそうな会話はどちらか」の対比較を用い、汎用の LLM 判定が発話順の破壊を罰しないことを示した。自動指標は Bo et al. (AAMAS 2026) の Non-repetition (自分の直前発話との非重複) と Evidence usage、PLACES の words per turn を借用する。協調タスク向けの総合点 MultiAgentBench / MARBLE (Zhu et al., 2025) の Communication Score は参照値として付録に置く。先行研究の整理 (12 本の指標と適用可否) は移植元の調査に基づく。

**LLM 判定のバイアス**: 長い応答を好む長さバイアスと位置バイアスは広く報告されている (Zheng et al., 2023 ほか)。本研究は予備評価でこれを実際に観測し (§4.5)、問いの立て方と検証手順で対処する。

**隠れ状態の解析**: 発話生成直前の表現から将来属性を復号する研究 (Dong et al., 2025) に倣い、補助分析として方式間の復号可能性を比べる (§6)。

## 3. 比較基盤

### 3.1 ドメインと設定

3 ドメイン、いずれも 5 人。議題は設計上「正解のない」もので、タスク精度は測らない (カードの有利不利は候補ごとに合計 0、人狼は自己対戦)。

| ドメイン | 内容 | 非公開情報 | ラウンド構造 | 決定 |
|---|---|---|---|---|
| 人狼 (aiwolf) | 5 人村 (占い師 1、人狼 1、狂人 1、村人 2) | 役職 | Day 0 (投票なし) → Day 1, 2, … | 毎日投票・処刑、夜に占い/襲撃 |
| 候補者選定 (candidate_selection) | 国の助成金など、提案 4 件から 1 件を選ぶ審査 | 各自の関心事 + 調査結果 | Round 1 → 調査 → Round 2 → 選択肢公開 → Round 3 → 投票 | 最多票の候補 |
| 共同生活 (shared_living) | 同居者・部員の取り決め 3 案から 1 案を選ぶ | 同上 | 同上 | 同上 |

各ラウンド 4 ターン、固定の発話順、1 発話 1〜40 語、`Skip` (そのターンをパス) / `Over` (そのラウンドから離脱)。議論ドメインでは Round 1 終了時に各自が 10 件の「調べられる事柄」(題名は公開、本文は非公開) から 2 件を選び、結果は本人だけに知らされる。ペルソナは 24 人から 5 人を割り当て、設定ファイルで固定。選択肢の表示順は設定ごとに決定的に並べ替える (ラベル A への偏りの統制)。各ドメイン 30 設定。

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

## 4. 評価設計

### 4.1 方針

評価は 2 族に分け、合成しない。族 A「会話としての質」は single が勝つと予想する側、族 B「情報の整合性」は single が負けると予想する側である。両方を同じ本文に置くことで、結果の向きによらず論文が成立する。指標は「何を測るか」ごとに先行研究から借用し、足りないものだけを定義する。自前の指標は人手との照合で妥当性を示す。定義と主要比較は本実験の前に固定し、パイロットは設計の確認にのみ用いたと明記する。

| 族 | 指標 | 種別 | 出所 |
|---|---|---|---|
| A 会話としての質 | **人間らしさの対比較** (「実際の人間の議論に見えるのはどちらか」A / B / 同等) + 理由の自由記述 | 人手 (主結果) | 問い文は Samanta et al. (2026)。理由の事後分類は Becker et al. (2026) の逸脱要因分類に倣う |
| | words per turn (発話あたりの語数) | 自動 | PLACES (Chen et al., 2023) |
| | 語数上限への張りつき率 (35 語以上の発話の割合、上限 40) | 自動 | 本研究の記述統計 |
| | Non-repetition (自分の直前発話との非重複: 1 − max(Jaccard, cos MiniLM)) | 自動 | Bo et al. (2026)、定義をそのまま |
| | Skip / Over の回数、全員がパスしたターン数 | 自動 (記述) | 本研究 |
| B 情報の整合性 | **非公開情報の使用**: 自分が調べていない調査結果の内容、または他者の役職を根拠にした発話の件数 | 自動 (候補生成) + 人手確認 | 独自。SOTOPIA の SEC (秘密を保てたか) が最も近いが 5 者の議論に合わない |
| | **公開前の選択肢名の出現**: 選択肢公開 (Round 3) より前の発話に選択肢の正式名が出た件数 | 自動 | 独自 |
| | 占い師の初回占いが人狼を当てる率 (偶然 0.25) と Day 1 に人狼が処刑される率 (人狼) | 自動 | 独自 (全知の書き手の縮退の指標) |
| 検証 | 評価者間一致 (κ)、LLM 判定と人手の一致率、長い方が勝った率、順序を入れ替えたときの反転率 | | Samanta et al. の判定器検査の手順 |
| 参照値 | MARBLE Communication Score (原著手順、ローカル判定器) | LLM 判定 | Zhu et al. (2025)。付録のみ |

手続き指標 (違反率・正規化率、トークン数・呼び出し回数・時間) は別表で報告する。

### 4.2 人手評価

- **材料**: 同じ設定で生成した 2 条件の台本を、書き手ビュー (票・処刑・夜の行動・調査の記録を含む全記録) の共通文法で並べ、条件名を伏せて `Transcript A` / `Transcript B` とする。1 対の長さは 2,500〜4,500 語。
- **問い**: 「どちらが実際の人間の議論に見えるか」を A / B / 同等で答え、理由を 3〜6 文で書く (具体的な箇所を指す)。指示文に「長さや量で評価しない」「決定の良し悪し、礼儀正しさ、ゲームの巧拙で評価しない」「発話が直前の発言に応えているか、話すことがあるときに話し無いときに譲っているか、テンポが人の会話か、人物が区別できるか、を見る」を明記する (付録 C の指示文を人手にもそのまま使う)。
- **対 (主要比較、本実験前に固定)**: C1 single-batch vs multi-private (主張の本体)、C2 single-batch vs single-online、C3 single-online vs multi-public、C4 multi-public vs multi-private (梯子の 3 段)、C5 single-batch vs single-batch-process (筋書きの効果)。single-batch vs single-batch-stepped は台本がほぼ同一なので人手には回さず、自動指標と表現の恒等性 (§6) で示す。
- **規模**: 各比較 45 対 (3 ドメイン × 15 設定) = 225 対。各対を 2 名が独立に判定し、順序は対ごとに無作為化する (450 判定)。符号検定の検出力は、真の勝率 0.70 で 0.77、0.80 で 0.98 (n = 45、両側 5%)。パイロットの LLM 判定では C1 0.69、C3 0.83、C4 0.85 (multi-private 側) だった。C5 は差が小さいと予想されるので同等性の判定 (勝率の 95% 信頼区間が 0.40〜0.60 に収まるか) とし、45 対では幅が広いことを限界に書く。
- **評価者**: 研究室のメンバー 4 名 (著者を除く)。1 対 5〜7 分として 1 人あたり約 10 時間を 2 週間に分けて行う。台本は英語のまま読み、ドメインごとの用語集を渡す。一致率は Cohen's κ (対ごとの 2 名) と、理由の分類の一致で報告する。
- **理由の分類**: 自由記述を「直前の発言への応答 / 譲り方 (Skip・Over) / 定型句・埋め草 / 自分の立場の言い直し / 人物の区別 / 一斉の Skip・Over の機械らしさ / 情報の矛盾 / その他」に事後分類し、どの性質が判定を動かしたかを示す。パイロットの LLM 判定の理由から作った分類で、人手でも同じ表を使う。

### 4.3 自動指標の定義

- **words per turn**: 発話 (`Skip` / `Over` を除く talk 行) あたりの語数の平均。本研究では発話順が固定で同一話者の連続発話がないので、発話 = ターン。
- **張りつき率**: 35 語以上の発話の割合。上限は 40 語で、モデルは上限ちょうどには書かず 35〜40 語に収めるので 35 を閾値にした (本実験では閾値の感度を付録で示す)。
- **Non-repetition**: 話者ごとに、連続する自分の発話の対で 1 − max(語 Jaccard, MiniLM 埋め込みの cos) を取り、話者平均、局平均。Bo et al. の定義。
- **非公開情報の使用 (候補生成)**: Round 2 以降の発話について、発話者が調べていないカードの「特徴語」(5 文字以上、議題文と全カード題名にない、他のカード本文にもない語、または数詞) が 2 語以上 (数詞は 1 語) 含まれ、かつそのカードを調べた参加者がそれらの語をまだ発話していない場合に候補とする。候補は全件を人手で確認し、本物 (言い換えも含めて、発話者が知りえない事実) だけを数える。語の照合なので言い換えは拾えず再現率は低い。本実験では LLM による候補生成 (「この発話は、発話者が知りえない調査結果を使っているか」をカードの所有表つきで問う) を加え、両方の候補を人手で確認して精度を報告する。
- **公開前の選択肢名**: Round 1〜2 の発話に選択肢の正式名 (例 `Coastal Lodge`) が単語境界つきで現れた件数。選択肢名の一部の語 (`lodge`) の出現は候補として別に記録し、本文の指標にはしない (一般語の偽陽性が多い)。
- **人狼の全知指標**: 占い師の Night 0 の占い先が人狼である率 (ランダムなら 0.25)、Day 1 の処刑対象が人狼である率。書き手が全役職を知る条件では占い師が「当ててしまう」ので、情報が席ごとに閉じているかの直接の指標になる。
- **MARBLE Communication Score** (付録): 原著のプロンプトと手順を逐語で用い、Qwen3.8-27B と gemma-4-31B をローカル判定器にする。原著は GPT 系判定器なので人手との一致は引き継がない。

### 4.4 LLM 判定の位置づけ

- 人手と同じ指示文・同じ対で、順序を入れ替えて 2 回判定する。モデルは生成モデルと別系統を主 (本実験では Qwen3.8-27B、思考モードで)、比較用にもう 1 系統。パイロットでは Claude 系 2 モデルを用いた (§5.3)。
- 報告する検証: 人手との一致率、順序の反転率、「長い方が勝った率」、位置 (先に示した方) の勝率。
- 用途: 人手との一致が十分なら全 90 設定への拡張に使い、不十分なら人手だけを主結果とする。主張の本体は人手評価に置く。

### 4.5 予備評価からの教訓 (評価の向き)

本設計の前に、同じ対を「どちらが良い議論か」を含む自由記述と 6 軸採点で LLM に判定させた (docs/preliminary_eval_2026-10-28/)。判定者は multi の長い発話を「応答が豊か」と評価し、single の短さと一斉の Skip / Over を「薄い」とし、一括生成群を 12/12 で見抜いたうえで低く評価した。判定者自身が「長い台本を有利に付けた」と自己申告している。機械指標で見ると、multi は発話の 4 割弱が語数上限に張りつき、内容語の半分は既出で、挨拶の定型句が 5〜7% あり、single-batch はいずれもほぼゼロだった。つまり「見たい差」は出ていたが、評価の向きが長さバイアスで逆転していた。この経験から、(1) 問いを「良い議論か」ではなく「人間の議論に見えるか」にし、(2) 長さで評価しないことを指示し、(3) 良さと副作用を分けて集計する設計に改めた。

### 4.6 統計

検定単位は設定。人手の対比較は符号検定と勝率の 95% 信頼区間 (Wilson)、自動指標は対応のある比較の paired bootstrap、二値指標は McNemar。ドメイン別に報告し、ドメイン × 条件の交互作用は混合効果モデルで確認する。「ほぼ同じ」の主張 (C5、multi-public vs multi-private の族 A) には同等性マージン (勝率 ±0.10、率指標 ±0.05) を事前に置く。一次指標 (人手の勝率、族 B の 3 指標、Non-repetition、張りつき率) と主要比較 (C1〜C5) を本実験前に固定し、他は探索的分析とする。

## 5. 結果 (パイロット 6、仮)

実行: gemma-4-31B-it、temperature 0、バッチ不変モード、3 ドメイン × 3 設定 × 7 条件 (5 条件 + single-batch-process + multi-private-process) + single-batch の反復 = 72 局。single-batch の反復 2 回は 9/9 設定で全文一致 (決定的)。single-batch と stepped は 1 設定で全文一致、他 8 設定は 5〜26 行目で分岐し、分岐の原因は近接確率の反転 (logprob 差 0.06 以下) とサーバの構造矯正に限られた。

### 5.1 族 A: 会話としての質 (自動指標)

**表 5-1: 自動指標 (3 ドメイン平均、設定平均)**

| 条件 | 発話数/局 | 語数/発話 | 上限張りつき | Non-repetition | Skip / Over | 全員パスのターン |
|---|---|---|---|---|---|---|
| single-batch | 29 | 14.7 | 0.00 | 0.66 | 4.6 / 11.7 | 3.1 |
| single-batch-stepped | 29 | 13.7 | 0.00 | 0.68 | 4.3 / 11.6 | 3.0 |
| single-online | 45 | 24.5 | 0.03 | 0.61 | 2.0 / 3.1 | 0.9 |
| multi-public | 49 | 30.5 | 0.20 | 0.56 | 1.3 / 3.7 | 0.1 |
| multi-private | 54 | 32.9 | 0.38 | 0.59 | 0.2 / 3.1 | 0.0 |
| single-batch-process | 35 | 16.6 | 0.00 | 0.67 | 3.9 / 11.6 | 2.8 |
| multi-private-process | 53 | 33.3 | 0.37 | 0.57 | 0.2 / 4.2 | 0.0 |

読み: 梯子を上がるほど (batch → online → multi-public → multi-private) 発話は長くなり、上限に張りつき、Skip / Over を使わなくなる。batch と stepped は一致する (分割自体は効かない)。最大の段差は stepped → online (語数 13.7 → 24.5、Over 11.6 → 3.1) で、プロンプトの目標と履歴の置き場所が主因である。multi-public → multi-private (情報量) は張りつき率を 0.20 → 0.38 に上げる。筋書き (process) は single-batch の発話数をやや増やし (29 → 35)、multi では変えない。Non-repetition は single が高い。全員パスのターン (畳みすぎの側の指標) は batch で 3 ターン/局あり、Day 0 や Round 1 の後半を一斉の Skip → Over で閉じる習慣に対応する。

### 5.2 族 B: 情報の整合性

**表 5-2: 情報の整合性 (人狼は 3 設定、議論は 2 ドメイン × 3 設定)**

| 条件 | 占い師の初回占いが人狼 (偶然 0.25) | Day 1 に人狼が処刑 | 公開前の選択肢名 (件/局) | 非公開情報の候補 (件/局、機械) | 人手確認で本物 |
|---|---|---|---|---|---|
| single-batch | 1.00 | 1.00 | 0.00 | 0.33 | 1 件 (下記 Kenji、判定者の指摘から) |
| single-batch-stepped | 1.00 | 1.00 | 0.00 | 0.17 | 0 |
| single-online | 1.00 | 1.00 | 0.17 | 0.00 | 0 |
| multi-public | 1.00 | 1.00 | 0.00 | 0.17 | 0 |
| multi-private | 0.00 | 0.00 | 0.00 | 0.17 | 0 |
| single-batch-process | 1.00 | 1.00 | 0.00 | 0.33 | 1 件 (下記 Misaki) |
| multi-private-process | 0.33 | 0.67 | 0.00 | 0.17 | 0 |

読み: 人狼では、全役職を知る条件 (single 3 条件と multi-public) で占い師が初回の占いで必ず人狼を当て、Day 1 に必ず処刑される。multi-private だけが偶然の水準 (0 / 3) にある。これは「情報が席ごとに閉じているか」の最も明瞭な指標で、本実験で 30 設定に広げる。議論ドメインでは、公開前の選択肢の正式名はほぼ出ない (1 件、single-online)。語の照合による非公開情報の候補は 10 件で、人手で確認すると本物は 1 件 (single-batch-process: Misaki が「人数固定の預かり金、抜けた人の分は残りが払う」と、Mio だけが調べたカードの内容を述べる。Mio 自身は「キャンセル条件が厳しい」としか言っていない) で、残りは一般語の一致か、調べた本人が前のラウンドで言い換えて共有済みのものだった。一方、語の照合が拾えない本物がもう 1 件ある (single-batch: Kenji が「リポジトリは今は速い」と、Toshio だけが調べて未公開の事実を述べる。予備評価の判定者の指摘から人手で確認)。つまり本物の漏洩は single にのみ 2 件、multi には 0 件だが、機械の候補生成は精度 10%、再現率 50% で、本実験では LLM による候補生成を加えて人手確認する。

### 5.3 人間らしさの対比較 (LLM 判定、人手の代用)

45 対 (9 設定 × 5 比較) を付録 C の指示文で、Claude 系 2 モデル (Opus、Sonnet) に順序を入れ替えて 2 回ずつ判定させた (180 判定)。人手評価は未実施で、ここでの判定は設計の確認 (問いが意図した性質を拾うか、長さに引きずられないか) のためである。

**表 5-3: 第 1 条件の勝率 (両順序、同等 = 0.5)**

| 比較 | 第 1 vs 第 2 | Opus | Sonnet | 全体 | 人狼 | 候補者選定 | 共同生活 |
|---|---|---|---|---|---|---|---|
| C1 | single-batch vs multi-private | 0.56 | 0.83 | **0.69** | 0.92 | 0.67 | 0.50 |
| C2 | single-batch vs single-online | 0.61 | 0.94 | 0.78 | 1.00 | 0.75 | 0.58 |
| C3 | single-online vs multi-public | 0.94 | 0.72 | 0.83 | 0.92 | 0.83 | 0.75 |
| C4 | multi-public vs multi-private | 0.19 | 0.11 | 0.15 | 0.25 | 0.12 | 0.08 |
| C5 | single-batch vs single-batch-process | 0.39 | 0.50 | 0.44 | 0.83 | 0.50 | 0.00 |

検証: 2 判定者の一致 62/90 (0.69)。順序を入れ替えて勝者が反転した対は各判定者 8/45 (0.18)。先に示した方が勝った率 0.47 / 0.41 (位置バイアスなし)。**長い方が勝った率 0.42** (長さバイアスは予備評価と逆向きに消えた)。

読み: 「人間の議論に見えるか」を問うと、single-batch は multi-private に 0.69 で勝ち、梯子の各段 (C2, C3) でも書き手側が勝つ。multi-private は multi-public に 0.85 で勝つ (全員の秘密を知る席は「知らないふり」で発話が形式的になる)。ドメイン差が大きく、人狼では single が圧倒し、共同生活では五分である。共同生活では multi の雑談 (からかい、名前での呼びかけ) が「人間らしい」と読まれ、single の一斉 Skip / Over が「機械的」と読まれた。筋書き (process) は single-batch を共同生活でむしろ人間らしくした (C5 の共同生活 0.00 = process 側が 12/12 で勝ち) が、人狼では逆 (0.83)。判定者の理由の分類 (タグ上位): single が勝つとき「直前の発言に応える」「ターンを埋めている (相手の欠点)」「話すことがなければ譲る」「定型の締め (相手の欠点)」「人物の区別」; multi が勝つとき「直前の発言に応える」「本当の意見対立」「間違いと訂正」。一斉の Skip / Over は両方向で「機械的」と指摘され、single の弱点として本文に書く。

### 5.4 コスト

| 条件 | 呼び出し/局 | プロンプトトークン/局 | 生成トークン/局 |
|---|---|---|---|
| single-batch | 1 | 2.0k | 1.1k |
| single-batch-stepped | 54 | 140k | 0.7k |
| single-online | 59 | 167k | 1.5k |
| multi-public | 60 | 184k | 2.0k |
| multi-private | 65 | 145k | 2.3k |

### 5.5 仮の結論

パイロットの範囲では、(a) 会話としての質 (人間らしさの対比較、語数、張りつき、反復) は single-batch が multi-private より良く、差の最大の段は「プロンプトの目標と履歴の置き場所」(stepped → online) にある。(b) 情報の整合性は multi-private だけが保っており、全役職を知る条件では占い師が必ず当てる。(c) 分割自体は効かない (batch = stepped)。(d) 筋書きの効果はドメインで向きが変わる。(e) single の弱点は一斉の Skip / Over の機械らしさと、全知の漏洩である。主張の向きは本実験で確定する。

## 6. 補助分析: 発話前表現の恒等性と将来属性の復号可能性

隠れ状態は議論の質の評価には使わない。用途は 2 つで、(i) 「分割自体は表現を変えない」ことの表現レベルの実証、(ii) 方式ごとに発話前の表現から将来属性 (語数、Skip / Over、最終投票先、処刑 / 採択) がどの程度復号できるかの比較である。蒸留 (今後の課題) で移す対象もこの表現である。

- **取得**: 記録済みのプロンプトのトークン id と生成トークン id を同じモデル (bf16) に流し込む再生で、全層 4 層おき + 最終層の表現を保存する。位置は `gen_point` (その行の最初のトークンを予測する位置: batch / stepped では札 `- **X**:` の末尾、online / multi では生成プロンプトの末尾)。推論エンジンのトークン数との一致を全呼び出しで検査する (パイロット 2,730 / 2,730)。
- **恒等性 (パイロット、実測)**: single-batch と single-batch-stepped は同じトークン列なので、台本が一致する区間で gen_point の表現が全層で cos 1.000 (バッチ不変モード; 非バッチ不変では 0.9998)。これが「分割は効かない」の表現レベルの証拠である。
- **条件間の生の類似度は解釈しない**: batch と online / multi の gen_point は別のトークン上にあり (`**:` vs 思考チャネル末尾)、最終層の cos 0.1〜0.4 は無関係な行や別の設定でも同じ値になる。条件差としては報告しない。
- **プローブ (本実験後)**: 条件ごとに線形プローブを学習し、復号精度を条件内で比べる。統制は入力情報だけの予測器と、同一履歴の再生 (single-batch の台本を他条件の形式に流し込む)。各ドメイン 30 設定 × 5 条件では学習データが足りないので、本実験では各ドメイン 100 局 (設定 30 + 追加 70) を single-batch と multi-private について追加生成する。主張は「復号可能性」にとどめ、計画の因果は主張しない。

## 7. モデル計画

| 役割 | モデル | 理由 |
|---|---|---|
| 主系 (全条件、筋書き、プローブ) | gemma-4-31B-it (dense) | パイロット済み |
| 別系統 (中核 5 条件) | Qwen3.8-27B (dense, Apache 2.0) | 同規模の最新の別系統。vLLM 対応を確認済み。LLM 判定にも用いる (生成モデルと別系統) |
| 別サイズ (中核 5 条件) | gemma-4-12B-it | 同系列の別サイズとしての頑健性 |

全モデル temperature 0、バッチ不変モード、思考モード無効 (Qwen3.8 は `enable_thinking: false`)。chat template、停止列、最大トークン、revision、精度 (bf16)、推論ライブラリの版を header に記録する。「モデル横断」の主張は中核条件の現象の再現に限定し、筋書きとプローブの結論は主系に限る。

## 8. 議論と限界

- **分割と表現**: 差はプロンプトの目標・履歴の置き場所・結末の決め手・文脈の分割・情報量に帰属させる設計にしたが、stepped と online の差は「目標」と「置き場所」をまとめて含む (さらに分けるには online の役割文を batch の履歴置き場で使う条件が要る。将来課題)。
- **目的関数の違い**: single-batch は「整合的な架空の議論を書く」課題、multi-private は「与えられた情報で意思決定する」課題であり、文面を揃えても解消しない。本研究は会話としての質と情報の整合性を別々に記述し、意思決定の質は主張しない。
- **人間らしさの判定の限界**: 「人間の議論に見えるか」は評価者の読みに依存し、ドメイン差が大きい (共同生活では五分)。一斉の Skip / Over は single の機械らしさとして判定を下げる。人手評価は 225 対 × 2 名で、評価者 4 名の一致率を報告する。
- **漏洩検出の再現率**: 語の照合は言い換えを拾えない (パイロットで本物 2 件のうち 1 件を見逃し)。本実験では LLM による候補生成を加え、全候補を人手で確認して精度を報告する。人狼の全知指標 (占い師の初回命中) は再現率の問題がなく、主指標にする。
- **multi-public**: 診断用条件。人狼ではゲームの前提が変わる。
- **筋書き**: 生成モデル自身が設定から書く。効果の向きがドメインで変わる (パイロット) ので、本実験ではドメイン別に報告する。
- **非決定性**: バッチ不変モードで反復は同一だが、batch と stepped は prefill と decode の数値経路の差で近接確率の反転が起きる (logprob 差 0.06 以下)。「分割は効かない」は「数値解像度以下の差を除いて」と但し書きする。
- **一般性**: 5 人、英語、24 ペルソナと固定議題。評価者は研究室のメンバー。

## 9. 結論

生成の粒度の差を 5 つの要因に分解する統制基盤を構築し、一括生成が会話としての質 (人間らしさ、場面に応じた長さ、反復の少なさ、適切な譲り) で優れ、情報の整合性 (知らないはずの情報の不使用) で劣るという非対称なトレードオフを示す設計を提示した。パイロットでは差の最大の段はプロンプトの目標と履歴の置き場所にあり、分割自体は効かなかった。single の会話としての長所を、情報を揃えた席ごとの生成に移すことが今後の課題である。

---

## 付録 A: 条件の実装対応

| 条件 | 実行 | messages |
|---|---|---|
| single-batch | `run_single.py` | [system, user] 1 回 |
| single-batch-stepped | `run_multi.py --stepped` | vLLM `/tokenize` で [system, user] の生成プロンプトのトークン列を取り、書き手ビュー + 札のトークン列を連結して `/v1/completions` に渡す (1 行ごと)。TALK は次の台本要素で、票・行動は行末で停止 |
| single-online | `run_multi.py --writer` | [system(online), user = 書き手ビュー + 札] |
| multi-public | `run_multi.py --reveal` | [system(participant, 全員の人物欄 + 隠された情報), user = 席ビュー + 札] |
| multi-private | `run_multi.py` | [system(participant, 自席), user = 席ビュー + 札] |
| + plan | `--scenario auto --plan-granularity process|outcome|outline|turn` | system 末尾に `## Plan` |
| 評価 | `scripts/eval_metrics.py` (自動指標、候補一覧)、`scripts/render_judge_pairs.py` (対の描画、順序 2 通り、ラテン方格の割当)、`scripts/judge_summary.py` (勝率、順序効果、長さ、理由タグ) | |

game_id = `<setup>__<条件札>__<model_tag>__<ts>`。header に method / pipeline / condition / axes / scenario / sampling / model_info / vllm_version / hf_revision / chat_template_sha1 / config_sha1 / code_tree / option_perm。`scripts/verify_prompt_control.py` が 90 設定 × 全条件 × 全筋書き種で system の同一性を検証、`scripts/extract_hidden.py` が記録から隠れ状態を再生する。

## 付録 B: プロンプト全文 (candidate_selection_0001 で描画)

B.1 が single-batch の system 全文で、single-online と multi-public はこの先頭の役割段落だけが違う (B.3)。multi-private は `## Participants` と `## Hidden information` の代わりに自席の `## Your profile` を持つ (B.4)。筋書き条件は末尾に `## Plan` (B.6) が付く。

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
The talk proceeds in rounds. Each round has 4 turns; in each turn, every participant speaks once, in this fixed order: Servas, Midori, Kenji, Benjamin and Toshio. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this round). An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others.

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



## 付録 C: 対比較の判定指示文 (人手と LLM 判定に共通)

````
# Pairwise judgement: which transcript reads more like a discussion among real humans?

You will read pairs of transcripts. The two transcripts of a pair come from the same five-person discussion setting
(same topic, same participants and personalities, same hidden roles or private findings) but were produced in
different ways. Transcript grammar: `## Day n` / `## Round n` periods, `### Talk` with `#### Turn t of 4`,
one line per speaker `- **Name**: utterance`; `Skip` = the speaker passes this turn, `Over` = the speaker leaves
the round; `### Vote`, `### Action` (night actions or things looked into) and `## Result` are the record of the
session. Utterances are limited to 40 words by the rules of the session in both transcripts.

Question (answer it for each pair): **Which of the two reads more like a discussion among real humans?**

Judge the discussion as a conversation:
- do utterances respond to what was just said, or talk past it;
- do people speak when they have something to say and yield (Skip / Over) when they do not, or keep talking
  because turns remain;
- does the pace feel like people talking, or like filling a form;
- do the participants sound like distinct people who stay themselves.

Do **not** judge by length or by how much is said: a longer or more detailed transcript is not more human for
that reason, and a shorter one is not less human for that reason. Do not judge by the quality or correctness of
the final decision, by politeness, or by how well the game was played.

For each pair, answer with exactly one of `A`, `B`, `Tie`, then explain the judgement in 3–6 sentences pointing to
concrete places in the transcripts (period / turn / speaker). Write the explanation before you settle on the
answer if that helps, but report only the final answer.

Output: one JSON object per pair, written together as a JSON list to the output file given in your task:
```
[{"pair": "<file name without _o1/_o2.md>", "verdict": "A" | "B" | "Tie",
  "reasons": "<3-6 sentences>",
  "cues": ["<short tag>", ...]   // the kinds of evidence you used, e.g. "responds to previous speaker",
                                  // "yields when nothing to say", "formulaic closings", "repeats own point",
                                  // "distinct voices", "talks past others", "fills turns"
 }, ...]
```
Read only the files named in your task. Do not look for other files in the directory or elsewhere; do not modify
any file other than your output file.
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


## 付録 E: 外部レビューへの対応 (v2 → v3、2026-10-28)

| 指摘 | 対応 | 状態 |
|---|---|---|
| MC1 batch vs online の交絡 (目標・履歴・サーバ) | single-batch-stepped を追加し梯子で分離。主張を「要因の定量化」に | 実装済み |
| MC2 評価が良い議論を定義していない | 2 族 (会話としての質 / 情報の整合性) に分け、人手の問いを Samanta et al. の問い文に、長さに依存しない指標を選定 (v4) | 設計に反映 |
| MC3 逆方向の先行研究 | De Baer et al. を引用、仮説を非対称なトレードオフに、タイトル変更 | 反映 |
| MC4 分割は表現を変えない | その通りと認め、stepped を恒等性の検査に使う (cos 1.000 を実測)。プローブは補助分析に格下げ | 反映 |
| MC5 outcome plan は未来情報 | process plan を主系に、outcome は未来情報の効果として分離、multi-private + process | 実装済み |
| MC6 蒸留の情報不一致 | 別論文へ。基盤は情報を揃えた教師と漏洩率を確保 | 反映 |
| 統計・規模 | 効果量と CI、同等性マージン、ドメイン別、事前固定、検出力の計算 (v4) | 設計に反映 |
| 先出しの扱い | 選択肢の正式名・数詞など偶然一致しにくい情報と人手検証、人狼は占い師の初回命中 | 設計に反映 |
| 早期終了の交絡 | 長さで評価しない指示、長い方が勝った率の報告 (v4) | 設計に反映 |
| タスク精度 | 測らない (正解のない議題)。情報の整合性は別族として測る | 設計に反映 |

**モデル選定レビュー (2026-10-28)**: 選定は維持。gemma-4-12B は「同系列の別サイズ」と限定。Qwen3.8 は thinking の無効化と履歴の扱いを明示。全モデルで revision・精度・ライブラリ版を固定記録。

## 付録 F: 第三者レビューへの質問 (v4)

1. 評価を「会話としての質」と「情報の整合性」の 2 族に分けて合成しない設計は、「提案ありきの評価」という批判に耐えるか。借用 (Samanta の問い文、Bo の Non-repetition、PLACES の words per turn) と独自 (漏洩の 3 指標) の線引きは明確か。
2. 人手評価を「人間の議論に見えるか」の 1 問 + 理由の自由記述にし、6 軸採点をやめた判断は妥当か。問いを 2 つ (PLACES の Coherent を追加) にすべきか。
3. 規模 (各比較 45 対 × 2 名、評価者 4 名) は主張に対して十分か。C5 の同等性判定に 45 対は少ないが、限界として書くことで足りるか。
4. 予備評価で LLM 判定の向きが長さで逆転した経緯 (§4.5) を本文に書くことは、評価設計の動機として有効か、それとも弱点に見えるか。
5. 漏洩検出 (語の照合は精度 10%・再現率 50%) を LLM 候補生成 + 人手確認で補う計画は妥当か。人狼の「占い師の初回命中」を主指標にする扱いはどうか。
6. 一斉の Skip / Over を single の弱点として本文に書くことで、主張 (single は人間らしい) との整合は取れているか。
7. 隠れ状態の分析を評価から切り離し、恒等性の実証と条件内の復号可能性に限定した扱いは適切か。
8. 梯子の 5 条件で 5 要因の分離は成立しているか。stepped vs online に「目標」と「置き場所」が同居することの扱い。
9. モデル計画 (gemma-4-31B 主系、Qwen3.8-27B、gemma-4-12B) と「モデル横断」の主張範囲の限定は妥当か。
10. タイトルと貢献は設計から導ける範囲に収まっているか。
