# 論文シナリオ草稿 v6 (密度仮説版、2026-10-28 夜)

> **位置づけ**: 本実験前の草稿。§5 の数値はパイロット 8 (現行プロンプト、gemma-4-31B-it、3 ドメイン × 3 設定 × 7 条件 = 63 局) の実測で、規模が小さいため「仮の結果」である。注釈は手元の Llama 3.3 70B と gpt-oss-120b (論文に載せる注釈者) に加え、設計確認として Claude Opus / Sonnet (載せない) の 4 者で行い、向きの一致を確かめた。本実験ではこの 9 設定の記録を 30 設定の一部としてそのまま使い (生成は決定的)、指標の定義を固定した後に残り 27 設定を生成したと明記する。v5 からの主な変更: (1) 中心の主張を「single と multi は議論の中身 (新しい内容の数) では大差がなく、single は同じ内容を 3 分の 1 の語数で言い、言うことがなくなれば譲る」という**密度仮説**に置き換えた。(2) 評価指標を確定した (§4.1): Becker の Lack of progress を「新しい内容の数 (0 / 1 / 2)」に拡張し、そこから密度 (1 内容あたりの語数) と内容の総量を導く。Bo の Responsiveness には応えた発話の id と応答の種類を付ける。Evidence usage / Stance / Distinct-N は落とす。(3) 情報の整合性を「開示 / 利用 / 先出し」の 3 分類の違反率表にした。(4) 隠れ状態の分析を密度仮説の機構 (全文を書く目標で生成すると各行の長さと役割が生成前に決まっている) の検証として位置づけた (§6)。(5) 判定モデルを生成モデルと系統で分けた (判定 Llama 3.3 70B / gpt-oss-120b、生成 gemma-4 / Qwen3.8)。判定は temperature 0 で、バッチ不変モードは Llama のみ (gpt-oss の MXFP4 MoE カーネルはこの GPU でバッチ不変モードに対応しない)。(6) 書き方: 梯子は要因の「分離」ではなく段階的な絞り込みの装置、stepped は negative control、ペルソナは共通集団からの統制、と書く。v5 の §10 改訂方針メモは本文に反映して削除した。

---

## タイトル案

第一候補: **Same Content, a Third of the Words: Why a Single Writer's Multi-Party Discussion Reads Like Conversation**

第二候補: **Who Writes and Who Knows: Density, Mutual Response and Information Consistency in LLM-Generated Multi-Party Discussions**

日本語仮題: 台本を一括で書く単一 LLM と席ごとの LLM による多人数議論生成の統制比較: 内容の密度・相互応答・情報整合性

## 概要

LLM に複数人の議論を生成させる方法には、1 つの LLM が台本全体を一括で書く方法 (single) と、参加者ごとに独立した LLM を置いて 1 発話ずつ対話させる方法 (multi) がある。両者はプロンプトや進行手続きが違うまま比べられてきた。本研究は、同一モデル・同一ルール文・同一台本文法・同一の情報公開スケジュールのもとで差分を設計した軸だけに絞った比較基盤を構築し、「誰が会話を生成し、どの情報を閲覧できるかは、発話の密度・相互応答・情報整合性にどう影響するか」を 3 ドメイン (人狼、候補者選定、共同生活の取り決め) × 各 30 設定 × 5 条件 (single-batch / single-batch-stepped / single-online / multi-public / multi-private) で測る。評価は「会話としての質」と「情報の整合性」を別の族として測り、合成しない。前者は Bo et al. の Responsiveness / Rebuttal / Non-repetition と PLACES の長さ指標に加え、Becker et al. の「進展のない発話」を「発話が加える新しい内容の数」に拡張し、そこから密度 (1 つの新しい内容あたりの語数) と内容の総量を導く。後者は知りえない事実の開示、特権情報の利用、選択肢の先出しを条件 × 事象の違反率表で報告する。パイロット (各ドメイン 3 設定、63 局) では、single-batch と multi-private は位置を揃えた発話あたりの新しい内容の数がほぼ同じ (0.9〜1.2) で、局あたりの内容の総量は multi が 1.2〜1.4 倍だったのに対し、語数は multi が 3.9 倍で、1 内容あたりの語数は single 14 語、multi 40〜47 語だった (9 設定すべてで single が低い)。水増し (同じ発話内の言い直し・定型の前置きと締め) は single 1〜2%、multi 31〜33% の発話にあった。応答性は人狼と候補者選定で同等、共同生活で multi が高く、反論は multi に多い。情報の整合性では、全役職を知る条件の占い師が初回の占いで必ず人狼を当て (1.00 vs 0.00)、他者の調査結果の開示は single にのみ見られた。本研究は、single が「人間の会話らしく読める」のは内容が多いからでも応答が多いからでもなく、同じ内容を短く言い、言うことがなければ譲るからだと示し、その機構を発話生成直前の表現から将来属性 (語数、残り発話数、結末) が復号できる度合いの差として検証する。

## 1. はじめに

LLM を用いた多人数議論の生成は、社会シミュレーション、対話データの合成、ゲーム AI に使われる。生成の仕方には、1 回の生成で議論全体を書き下ろす中央集権的な方法と、各参加者を独立した LLM にして逐次に応答させる分散的な方法がある。前者は整合的な台本を書きやすく、後者は参加者が互いに反応する対話になりやすい、と言われるが、既存の比較は方式ごとにプロンプトや進行手続きが異なり、どの差がどの性質を生むのかを特定できない。面接対話では対話エージェント方式が一括生成より高く評価されたという報告 (De Baer et al., GEM 2025) もあり、「どちらが良いか」は設定と観点に依存する。

本研究の問いは「多人数議論において、誰が会話を生成し、どの情報を閲覧できるかは、発話の密度・相互応答・情報整合性にどう影響するか」である。自己回帰モデルでは、同じトークン列を一度に生成しても、1 行ずつ止めて同じ接頭辞から再開しても、greedy なら同じ続きが出る。したがって「一括か逐次か」の差は、生成を分割すること自体ではなく、(1) プロンプトの目標、(2) 履歴の置き場所、(3) 結末と構造の決め手、(4) 文脈の分割、(5) 情報量のどこかから生じる。本研究はこの 5 つを段階的に変えた条件の梯子を並べ、隣り合う段の差を記述することで、差がどこで生じるかを絞り込む。

本稿が主張したいことは次の 3 点で、評価設計はこれらを**別々に**測れるように組む (優劣の合成点は作らない)。

- **密度**: 一括生成と席ごとの生成は、議論が加える新しい内容 (論点・根拠・質問・提案・票の意思表示) の数では大差がない。一括生成は同じ内容をおよそ 3 分の 1 の語数で言い、言うことがなくなれば Skip / Over でターンを畳む。席ごとの生成は同じ内容を上限いっぱいの語数で言い、同じ発話の中の言い直しと定型の前置き・締めで埋める。読んで一括生成が人間の会話らしく感じられるのは、内容の密度が高く読む負担が小さいからであり、これは好みの判定に頼らず「1 つの新しい内容あたりの語数」で示せる。
- **相互応答**: 他者の発言に応える率は、中身を見れば両方式で近い (ドメインによっては席ごとの生成が高い)。明示的な反論は席ごとの生成に多い。応答の種類 (質問に答える / 理由を足す / 反対する / 同意だけ) の分布も報告する。
- **情報の整合性 (副作用)**: 一括生成の書き手は全員の秘密を知っているため、参加者が知らないはずの事実を発話に混ぜ (開示)、占い先や投票先が特権情報で動く (利用)。情報を揃えた席ごとの生成ではこれが消える。

機構の仮説: 一括生成の書き手は議論全体 (誰が何を言い、どう決まるか) を持ったまま各行を書くので、1 行ごとに議論の中で果たす役割と長さが生成前に決まっており、長く話す必要がない。席ごとの生成の各席は結末も次の展開も知らないので、不確実さを埋めるように長くなる。これは発話生成直前の内部表現から将来属性がどの程度復号できるかの差として検証できる (§6)。

いずれも「指示なし」で両方式に同じルール文を与えたときの方式の性質 (傾向) として記述し、「良い」とは言わない。single の密度を、情報と応答性を保ったまま multi に移す (蒸留) ことは本稿の範囲外の今後の課題とし、基盤はそれを見据えて設計する。

**研究課題**

- RQ1 (密度と相互応答): 一括生成と席ごとの生成は、新しい内容の数・密度・譲り・応答性・反論のそれぞれでどう違うか。差は梯子のどの段 (結末の決め手 / 目標と置き場所 / 文脈の分割 / 情報量) で生じるか。
- RQ2 (情報の整合性): 全知の書き手はどの程度、知らないはずの情報を開示し、特権情報を利用するか。情報を揃えた席ごとの生成 (multi-private) でそれは消えるか。
- RQ3 (機構と頑健性): 発話生成直前の表現から将来属性 (語数、残り発話数、結末) が復号できる度合いは方式でどう違うか。傾向はドメイン・モデル・筋書きの有無を変えても再現するか。

**貢献**: (1) 差分を設計した軸だけに絞った比較基盤 (共通ルール文・共通台本文法・席ビューと書き手ビューの決定的復元・違反と正規化の共通記録・推論エンジンが見たトークン id の記録・バッチ不変モードによる決定的な再現)。(2) 5 条件の梯子による段階的な絞り込みの設計と、分割自体が効かないこと (batch = stepped、表現も同一) の実証。(3) 先行研究の指標セットを発話単位の率として適用し、Lack of progress を「新しい内容の数」に拡張して密度を導く評価設計。「会話としての質」と「情報の整合性」を分けて報告し、LLM の対比較判定が表示と問いで向きを変えることの実証 (§4.5)。(4) 密度 (single) と反論 (multi) のトレードオフ、および全知の書き手による情報の開示と利用の定量化。

## 2. 関連研究

**LLM マルチエージェント議論・ゲーム**: 複数 LLM の討論による推論の改善 (Du et al., 2023)、役割分担による協調 (Li et al., 2023, CAMEL)、生成エージェントによる社会シミュレーション (Park et al., 2023)。人狼については LLM エージェントの経験学習 (Xu et al., 2023) と人狼知能大会 (AIWolf / aiwolf-nlp)。

**single と multi の比較**: 面接対話で一括生成と 2 エージェント対話を比べ、LLM 判定では対話方式が高く、トークン数は約 6 倍だった研究 (De Baer et al., GEM 2025)。最後通牒ゲームでの single と multi の人間行動再現の比較 (Sreedhar & Chilton, HICSS 2025)。multi-agent debate の優位が single-agent ベースラインに対して不安定であることを示した研究 (Zhang et al., 2025)、議論の構造的・認知的要因を操作した統制研究 (Wu et al., 2025)。Cui et al. (Findings of ACL 2026) は single-agent 生成が multi-agent より意味的多様性で勝ることを示し、情報の可視性を扱う点で本研究に近い。本研究は多人数の自然言語対話の生成を対象に、密度・相互応答・情報整合性を扱い、5 つの要因を段階的に絞り込む点で異なる。

**多人数対話の評価指標**: Bo et al. (AAMAS 2026) はプロンプトの部品で対話の振る舞いを制御できることを示すために、Responsiveness (直前の発話に取り組んだか、発話単位の二値、LLM 判定)、Rebuttal (明示的に反対したか)、Non-repetition (自分の直前発話との非重複、埋め込み)、Evidence usage、Stance の 5 指標を定義した。良し悪しの向きは定めない記述的指標である。PLACES (Chen et al., 2023) は合成会話を人間収集データと比べるために words per turn、turns per conversation、Distinct-N を報告し、人手で Natural / Coherent / Interesting / Consistent と多人数固有の Comprehensible / Balanced engagement を 1〜5 で評価した。Becker et al. (EACL Findings 2026) は多エージェント討論の逸脱を専門家 8 名が 170 抜粋に誤りの型 (Lack of progress、Low-quality feedback、Low-quality engagement、Knowledge gap 等) を付けて分類した。本研究は Bo の Responsiveness / Rebuttal / Non-repetition と PLACES の長さ指標を採り、Becker の Lack of progress を発話単位の「新しい内容の数」に拡張する。

**LLM 判定のバイアス**: Samanta et al. (ACL 2026) は多人数対話の対比較 (Naturalness / Engagingness / Overall) で、人間同士の κ が 0.29、人間と LLM の κ が 0.11〜0.18 にとどまり、LLM 判定が冗長な発話を好み、Tie を避け、発話順の破壊を罰しないことを示した。本研究は予備評価で同じ現象を観測し (§4.5)、好みを問う対比較を主結果から外した。

**隠れ状態の解析**: 発話生成直前の表現から将来属性を復号する研究 (Dong et al., 2025) に倣い、方式間の復号可能性を比べる (§6)。

## 3. 比較基盤

### 3.1 ドメインと設定

3 ドメイン、いずれも 5 人。議題は設計上「正解のない」もので、タスク精度は測らない (カードの有利不利は候補ごとに合計 0、人狼は自己対戦)。

| ドメイン | 内容 | 非公開情報 | ラウンド構造 | 決定 |
|---|---|---|---|---|
| 人狼 (aiwolf) | 5 人村 (占い師 1、人狼 1、狂人 1、村人 2) | 役職 | Day 0 (投票なし) → Day 1, 2, … | 毎日投票・処刑、夜に占い/襲撃 |
| 候補者選定 (candidate_selection) | 国の助成金など、提案 4 件から 1 件を選ぶ審査 | 各自の関心事 + 調査結果 | Round 1 → 調査 → Round 2 → 選択肢公開 → Round 3 → 投票 | 最多票の候補 |
| 共同生活 (shared_living) | 同居者・部員の取り決め 3 案から 1 案を選ぶ | 同上 | 同上 | 同上 |

各ラウンド 4 ターン、固定の発話順、1 発話 1〜40 語、`Skip` (そのターンをパス) / `Over` (そのラウンドから離脱)。議論ドメインでは Round 1 終了時に各自が 10 件の「調べられる事柄」(題名は公開、本文は非公開) から 2 件を選び、結果は本人だけに知らされる。ペルソナは全ドメイン共通の 24 人の集団から 5 人を引く統制であり (ドメインごとの妥当性は変数ではない)、設定ファイルで固定する。選択肢の表示順は設定ごとに決定的に並べ替える。各ドメイン 30 設定。

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

梯子は「5 要因を分離する」装置ではなく、隣り合う段で変わるものを明示して段ごとの差を記述し、差がどこで生じるかを段階的に絞り込む装置である。タスクの性質が違う以上 (single-batch は「整合的な議論を書く」課題、multi-private は「与えられた情報で意思決定する」課題)、完全な統制は不可能で、本研究は段ごとに「何が変わり、何が変わらないか」を記述する。

| 比較 | 変わるもの |
|---|---|
| single-batch vs single-batch-stepped | 結末と構造の決め手 (書き手 vs サーバ) だけ。接頭辞のトークン列は同一で、greedy ならサーバが差し替えない限り同じ発話が出る。**分割自体が効かないことの negative control** で、推論エンジンの数値的な非決定性の大きさもここで測る |
| single-batch-stepped vs single-online | プロンプトの目標 (全文か次の 1 行か) + 履歴の置き場所 (assistant の続きか user の貼り直しか)。この 2 つは同居する (さらに分けるには online の役割文を batch の履歴置き場で使う条件が要る。将来課題) |
| single-online vs multi-public | 1 つの全知の文脈か、席ごとに分割された文脈か (他席の夜の行動・調査の可視性を含む) |
| multi-public vs multi-private | 情報量 (全員の秘密か自席の秘密か) |

single-batch と multi-public と single-online の system は役割段落だけが違い (付録 B.3)、single-batch-stepped は single-batch と同一の system と user を使う (検証スクリプトが 90 設定で確認)。multi-public は「自然なマルチエージェント」ではなく情報アクセスを操作した診断用条件であり、人狼では「知っていて知らないふりをする」ことでゲームの前提が変わることを明示する。主要比較は 5 つに絞る: 梯子の 4 対 + single-batch vs multi-private (両端)。

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
| process (主系) | 各期間の公開の筋 (話題・論点・意見の傾き) + 席ごとの立場の推移。**票・処刑・採択・夜の行動・勝敗・選択肢名・被疑者名・役職語を含まない** | 全条件 (multi-private を含む) |
| outcome | 票・処刑 (採択)・夜の行動・勝敗だけ | public 条件 |
| outline | process + outcome | public 条件 |
| turn | outline + 各ターン各席の発言要旨 (上限条件) | public 条件 |

生成は turn を 1 本だけ作り、他は削って派生する (入れ子の統制)。検証はルールで機械的に再生 (票 → 同票規則 → 処刑 → 勝敗、対象の生存、発言単位の整合) し、公開の筋と席の筋に結末語・選好語・選択肢名・(人狼では) 他者名と役職語がないことも確認する。両方式とも system の末尾に `## Plan` として同文で置き (付録 B.6)、進行は強制せず、乖離を両方式共通の検出で記録する。process plan は全知の生成物から結末語を消したものなので、公開情報だけから生成した筋書きを 1 種追加して対照にする (筋書き 90 本の再生成のみ。single-batch と multi-private に与える)。

### 3.5 共通ルール文の 2 文 (2026-10-28 に追加)

移植元の研究で single の「お手本」を作ったプロンプトは、「4 つの失敗モード (情報の抱え込み・早期収束・同調・語彙の単調) を克服する良い議論を示せ」「大半の発話は短く、問い返しを」と明示しており、そのお手本は名指し (他者の名前を呼ぶ発話) が 5 割、語数 21〜22 の対話的なものだった。本基盤は統制のためにこの指示を両方式から削ったが、その結果 single-batch は各自が持ち場を順に報告する並列の独白になった (名指し 1%)。失敗モードの列挙を戻すと「指示に従った議論」の比較になりベースラインでなくなるので、代わりに**議論という活動の定義と形式の道具**として次の 2 文を共通ブロック `## Discussion format` に加えた (両方式に同文。量や形式の指定、評価指標に直結する語は入れない)。

1. 「The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.」(話し合いは参加者どうしの会話であり、互いに応答し、決定はそのやり取りから出る)
2. 「A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said.」(@名前 で他の参加者に直接、質問・返答・同意・反対ができる)

2 文は両方式に同じ向きに効き (single-batch の応答性 42〜50 → 59〜63、名指し 1% → 19%; multi-private 62〜70 → 72〜76、10% → 36%; パイロット 6 → 8)、2 文を入れる前の結果も同じ記録に残す (docs/eval_pilot_2026-10-28/)。

## 4. 評価設計

### 4.1 指標

評価は 2 族に分け、合成しない。族 A「会話としての質」は方式の性質を複数の観測で記述し、族 B「情報の整合性」は single の副作用を数える。族 A は先行研究の指標を採り、独自の指標は先行指標からの導出 (密度、内容の総量) と記述統計に限る。定義と主要比較は本実験の前に固定し、パイロットは設計の確認にのみ用いたと明記する。

| 族 | 指標 | 定義 | 出所 | 取り方 |
|---|---|---|---|---|
| A | 発話数/局、語数/発話 | Skip / Over を除く発話の数、1 発話の語数 | PLACES (Chen et al., 2023) | 自動 |
| A | 上限張りつき率、Skip + Over /局 | 35 語以上の発話の割合、譲った回数 | 本研究 (記述) | 自動 |
| A | Non-repetition | 自分の連続する 2 発話の非重複度 (1 − max(Jaccard, cos MiniLM)) | Bo et al. (2026) | 自動 |
| A | **新しい内容の数** (content) | 発話が加える新しい情報・判断・質問・提案の数 (0 / 1 / 2 以上)。挨拶・締めの定型句、自分の既出の点の言い直し、既に示した同意の繰り返しは 0。票の意思表示・立場の変更は新しい判断として 1。**0 = Becker の Lack of progress** | Becker et al. (2026) の拡張 | LLM 注釈 + 人手検証 |
| A | **密度** | 1 つの新しい内容あたりの語数 (局の総語数 / 新しい内容の総数)。進展なし発話 (content 0) に費やした語の割合も併記 | 本研究 (導出) | 導出 |
| A | 内容の総量 | 局あたりの新しい内容の総数 (「切り上げても内容を失っていない」の確認) | 本研究 (導出) | 導出 |
| A | 水増し (padded) | 同じ発話の中の言い直し、判断・質問・情報を運ばない前置きと締め、点に付いた一般的な感情表現があり、明らかに少ない語数で同じことが言える発話 | 本研究 (移植元ルーブリック由来、記述) | LLM 注釈 |
| A | Responsiveness (resp) + resp_to | 自分の前の発話以降に言われた特定の発話に取り組んだか (答える・同意・問う・積み上げる・反対)。応えた発話の id を同時に出す | Bo et al. (2026)。「直前の 1 発話」を「自分の前の発話以降」に広げた (5 人の順番発話への適応。本実験で原定義との一致も報告) | LLM 注釈 + 人手検証 |
| A | Rebuttal (rebut) | それに明示的に反対したか | Bo et al. (2026) | LLM 注釈 + 人手検証 |
| A | 応答の種類 (追加分析) | 応答 1 の発話を answer (質問に答える) / add (理由を足す) / object (反対) / agree (同意だけ) に分類 | 本研究 (分析) | 同じ注釈で |
| B | 開示 | 発話者が知りえない事実 (他者の調査結果の内容、他者の役職) を発話した件数 | 独自 | 機械候補 + LLM 候補 + 人手確認 |
| B | 利用 | 占い先・投票先が特権情報で動いた: 占い師の初回占いが人狼を当てる率 (偶然 0.25)、Day 1 に人狼が処刑される率 | 独自 (全知の書き手の縮退) | 自動 |
| B | 先出し | 公開前の選択肢名の出現 (Round 1〜2 に正式名) | 独自 | 自動 |
| 検証 | 注釈者間一致 (κ)、人手標本との一致、判定モデルの系統差 | | Samanta et al. (2026) の判定器検査の手順に倣う |

手続き指標 (違反率・正規化率、トークン数・呼び出し回数・時間) は別表で報告する。MARBLE の Communication Score (Zhu et al., 2025) は原著手順で算出した参照値として付録に置く。v5 にあった Evidence usage / Stance / Distinct-N は条件差がなく (パイロット 6)、落とした。

### 4.2 発話単位の注釈

- **材料**: 各局の記録を期間の見出し、発話 (順序どおり、id つき)、票、結果だけの形に描画する。ターン見出し、Skip / Over (人間の議論に存在しない手続きの記号。ルールで数えるだけ)、夜の行動と調査の行 (読者が見ない秘密情報) は落とす。
- **問い**: 発話ごとに content (0 / 1 / 2)、resp + resp_to、resp_type、rebut、padded を付ける。各項目は 1 文の定義 + 境界の例で指示し (付録 C)、長さ・丁寧さ・正しさで判断しないこと、迷ったら 0 (content は低い方) を明記する。好みや優劣は問わない。
- **注釈者**: 本実験では手元で配信する Llama 3.3 70B Instruct (bf16) と gpt-oss-120b (MXFP4、公式の唯一の形式) を用い (外部 API は使わない。生成モデル gemma-4 / Qwen3.8 とは系統を分ける。temperature 0。バッチ不変モードは Llama のみで、gpt-oss の MoE カーネルは対応しない)、両者の一致 (κ) を報告する。パイロットでは Claude 系 2 モデル (Opus / Sonnet) と Llama 3.3 70B、gpt-oss-120b を同じ指示で走らせ、系統間の一致を確かめた (§5.6)。
- **人手検証**: 各条件 2 局 × 3 ドメイン (約 1,200 発話、条件とドメインで層化) を研究室のメンバー 2 名が同じ指示で注釈し、LLM 注釈との一致 (項目別 κ) と人間同士の一致を報告する。一致が低い項目は主張に使わない。
- **集計**: 100 発話あたりの率を局ごとに取り、設定で平均する (長さに依存しない)。密度と内容の総量は局ごとの合計から導く。ラウンド・ターン位置を揃えた比較 (位置ごとの content の平均) で、切り上げによる生存バイアスを切り分ける。

### 4.3 族 B の手順

- 開示は 3 段階: (1) 語の照合 (発話者が調べていないカードの特徴語が 2 語以上、または数詞) で候補を出す。(2) LLM に「この発話は、発話者が知りえない調査結果を使っているか」をカードの所有表つきで問い、候補を足す。(3) 候補の全件を人手で確認し、調べた本人がそれ以前に言い換えて共有済みのものを除いて本物だけを数える。非候補からも無作為標本を確認して再現率を推定する。
- 先出しは正式名の単語境界一致のみ。語の一部の一致は候補として記録し、本文の指標にはしない。
- 利用 (占い師の初回命中、Day 1 の人狼処刑) は再現率の問題がなく、主指標にする。
- 3 分類を条件 × 事象の違反率表 1 枚にまとめる。

### 4.4 統計

検定単位は設定。率指標は対応のある比較の paired bootstrap (95% 信頼区間)、二値指標は McNemar。主要比較は 5 つ (梯子の 4 対 + 両端) に絞って多重比較を補正し、ドメイン別は「どの議論で差が出るか」の分析として報告する (ドメイン × 条件の交互作用は設定を単位にした階層モデルで確認)。「ほぼ同じ」の主張には同等性マージン (率指標 ±5 ポイント、位置を揃えた content の平均 ±0.1) を事前に置く。batch = stepped は台本が一致する区間と分岐後を分けて報告する。一次指標 (語数/発話、密度、内容の総量、Responsiveness、Rebuttal、族 B の 3 分類) を本実験前に固定し、他は探索的分析とする。

### 4.5 設計の経緯: 対比較判定を主結果にしない理由

v3〜v4 では、条件を伏せた 2 局の対比較で「どちらが人間の議論らしいか」を問う人手評価を主結果に置く予定だった。パイロット 6 の 45 対を LLM 2 系統で判定したところ、同じ対でも表示と問いで向きが変わった: 全記録を見せて「人間の議論らしいか」(譲りの観点つき) では single-batch が multi-private に 0.69 で勝ち、発話だけを見せて「決定に向かう議論として人間らしいか」では 0.39 で負け、基準を「口頭の会話のテンポ・冗長さなし・見合う長さ」と具体化すると 1.00 で勝った (36/36)。最後の設定では判定者間一致 0.90 だが勝者の 87% は短い方で、判定は語数の検出器になっていた。これは Samanta et al. (2026) の報告 (人間同士 κ 0.29、LLM は冗長さに反応) と整合する。好みを問う限り「人間らしい」の中身は判定者に委ねられるので、本研究は好みを問わず、定義した事象を数える設計に改めた。経緯と 3 ラウンドの数値は docs/eval_pilot_2026-10-28/ に記録してある。

## 5. パイロット結果 (仮)

実行: gemma-4-31B-it、temperature 0、バッチ不変モード、現行プロンプト (2 文入り)。パイロット 8 = 3 ドメイン × 3 設定 × 7 条件 (5 条件 + single-batch-process + multi-private-process) = 63 局。注釈は Claude Opus / Sonnet (O / S) と Llama 3.3 70B (L)、gpt-oss-120b (G) の 4 注釈者、同じ指示文 (付録 C)、temperature 0。パイロット 6 (2 文を入れる前、72 局) で single-batch の反復 2 回は 9/9 設定で全文一致 (決定的)、single-batch と stepped は 1 設定で全文一致、他 8 設定は 5〜26 行目で分岐し、原因は近接確率の反転 (logprob 差 0.06 以下) とサーバの構造矯正に限られた。

### 5.1 長さと譲り (自動指標、7 条件、3 ドメイン平均)

| 条件 | 発話数/局 | 語数/発話 | 語数/局 | 上限張りつき | Non-repetition | Skip / Over | 全員パスのターン |
|---|---|---|---|---|---|---|---|
| single-batch | 36.1 | 13.6 | 492 | 0.00 | 0.72 | 2.6 / 8.9 | 2.1 |
| single-batch-stepped | 35.7 | 14.0 | 499 | 0.00 | 0.70 | 2.8 / 9.3 | 2.2 |
| single-online | 49.4 | 26.5 | 1300 | 0.07 | 0.64 | 0.7 / 2.7 | 0.2 |
| multi-public | 48.1 | 32.2 | 1534 | 0.37 | 0.59 | 1.0 / 5.9 | 0.3 |
| multi-private | 57.2 | 33.9 | 1937 | 0.46 | 0.60 | 0.4 / 2.8 | 0.1 |
| single-batch-process | 41.6 | 15.8 | 653 | 0.00 | 0.70 | 1.7 / 8.4 | 1.9 |
| multi-private-process | 56.0 | 35.4 | 1986 | 0.66 | 0.58 | 0.0 / 1.6 | 0.0 |

読み: 梯子を上がるほど発話は長くなり、上限に張りつき、Skip / Over を使わなくなる。batch と stepped は一致する (分割自体は効かない)。最大の段差は stepped → online (語数/発話 14.0 → 26.5、語数/局 499 → 1300、Over 9.3 → 2.7) で、プロンプトの目標と履歴の置き場所が主因である。multi-public → multi-private (情報量) は張りつき率を 0.37 → 0.46 に上げる。

### 5.2 密度: 新しい内容の数と 1 内容あたりの語数 (中心の結果)

局あたりの合計 (条件平均)。content は注釈者の判定 (O / S / L / G)。

| 条件 | 語数/局 | 新しい内容の数/局 (O / S / L / G) | 1 内容あたりの語数 (O / S / L / G) | 進展なし発話の語の割合 % (O / S / L / G) | 水増し発話 % (O / S / L / G) |
|---|---|---|---|---|---|
| single-batch | 492 | 35 / 32 / 33 / 46 | 14.0 / 15.2 / 15.0 / 10.7 | 15 / 15 / 14 / 2 | 2 / 1 / 4 / 4 |
| single-batch-stepped | 499 | 36 / 33 / 35 / 47 | 14.0 / 15.0 / 14.1 / 10.5 | 15 / 16 / 12 / 2 | 2 / 4 / 4 / 7 |
| single-online | 1300 | 44 / 39 / 42 / 60 | 29.7 / 33.7 / 31.0 / 21.8 | 26 / 29 / 17 / 8 | 17 / 21 / 11 / 9 |
| multi-public | 1534 | 41 / 35 / 36 / 54 | 37.5 / 43.3 / 42.3 / 28.3 | 28 / 33 / 29 / 14 | 30 / 34 / 12 / 13 |
| multi-private | 1937 | 49 / 41 / 44 / 67 | 39.3 / 46.7 / 44.5 / 29.1 | 30 / 34 / 24 / 9 | 33 / 31 / 8 / 7 |
| single-batch-process | 653 | 42 / 36 / 37 / 52 | 15.7 / 17.9 / 17.7 / 12.6 | 14 / 17 / 14 / 4 | 2 / 4 / 1 / 8 |
| multi-private-process | 1986 | 50 / 41 / 42 / 67 | 39.5 / 48.4 / 47.2 / 29.5 | 26 / 34 / 27 / 8 | 26 / 23 / 10 / 12 |

(1 内容あたりの語数は局の合計から; 発話あたりの率は 100 発話あたりの局平均。)

読み:
- **内容の総量は近く、語数は 4 倍**: multi-private は single-batch より新しい内容が 1.3〜1.5 倍多い (注釈者により 49 vs 35、41 vs 32、44 vs 33、67 vs 46) が、語数は 3.9 倍 (1937 vs 492)。1 つの新しい内容あたりの語数は single 11〜15 語、multi 29〜47 語で、**9 設定すべて、4 注釈者すべてで single が低い** (設定ごとの比 2.2〜4.5 倍; Llama 2.4〜3.9)。ドメイン別でも同じ (Llama: 人狼 16 vs 47、候補者選定 18 vs 46、共同生活 13 vs 44)。注釈者の水準差 (gpt-oss は内容を多く数え、進展なしを少なく付ける) は条件の順序を変えない。
- **水増し**は single 1〜4%、multi 7〜34% の発話にある (Claude 系は multi に 3 割、Llama / gpt-oss は 1 割弱と水準が割れるが、向きは同じ)。multi の典型は「もっともな点ね、Mio。でも…」型の受けと「…だと思う。みんなはどう?」型の締めで、同じ発話内で同じ点を 2 度言う。single の発話は 1 つのことを 1 度言う。
- **進展なし発話 (content 0) の語の割合**は single 2〜15%、multi 9〜34% (注釈者により水準は違うが、どの注釈者でも multi が single の 1.7〜4 倍)。発話あたりの率 (§5.3) では人狼で single と multi が同じ (28 vs 27) だが、語で重みづけると single の無駄は 1 件 7 語の相づちで、multi の無駄は 1 件 37 語の儀礼であることが分かる。
- **梯子**: 密度の最大の段差は stepped → online (14〜15 → 30〜34 語; gpt-oss 10.5 → 21.8) で、長さと同じ段にある。online → multi-public (分割) で 38〜43 (gpt-oss 28)、multi-public → multi-private (情報量) で 39〜47 (29) と、段ごとに少しずつ下がる。筋書き (process) は single-batch の内容の総量を増やし (35 → 42)、密度は少し下げる (14 → 16〜19)。

### 5.3 位置を揃えた比較 (切り上げの生存バイアスの切り分け)

ラウンド・ターン位置ごとの発話あたりの新しい内容の数 (O / S 合算、3 ドメイン)。

| 位置 (ラウンド, ターン) | single-batch | multi-private | single-online | multi-public |
|---|---|---|---|---|
| R1 T1 | 1.17 | 0.94 | 1.27 | 1.24 |
| R1 T2 | 0.95 | 0.94 | 0.74 | 0.88 |
| R1 T3 | 0.90 | 0.83 | 0.67 | 0.51 |
| R1 T4 | 0.46 (n=24) | 0.42 (n=80) | 0.47 | 0.36 |
| R2 T1 | 1.85 | 1.57 | 1.88 | 1.95 |
| R2 T2 | 0.92 | 1.05 | 1.03 | 0.93 |
| R2 T3 | 0.75 | 0.80 | 0.83 | 0.70 |
| R2 T4 | 0.22 (n=18) | 0.47 (n=80) | 0.52 | 0.48 |
| R3 T1 | 1.22 | 1.38 | 1.10 | 1.02 |
| R3 T2 | 0.78 | 0.52 | 0.68 | 0.48 |
| R3 T3 | 0.74 | 0.62 | 0.30 | 0.25 |
| R3 T4 | 0.06 (n=18) | 0.10 (n=60) | 0.48 | 0.00 |

読み: 同じ位置では発話あたりの新しい内容の数は single と multi で同程度 (差 ±0.3 以内、ターン 1 で 1.2〜1.9、ターン 4 で 0〜0.5)。single が発話を減らすのはターン 3〜4 (Over) で、そこは multi でも内容が 0.1〜0.5 に落ちている位置である。つまり single は「内容のある位置を切り上げている」のではなく、「内容が尽きる位置で譲っている」。multi の内容の総量が 1.3 倍多いのは、主にターン 3〜4 の発話数が多いことによる (1 発話あたりでは同じ)。

### 5.4 相互応答 (Responsiveness / Rebuttal、応答の種類、質問への返答)

100 発話あたり (O / S)。

| 条件 | Responsiveness (O / S / L / G) | Rebuttal (O / S / L / G) | 応答の種類 answer / add / object / agree (%、O; L) |
|---|---|---|---|
| single-batch | 63 / 59 / 50 / 42 | 10 / 7 / 6 / 7 | 11 / 49 / 15 / 25; 4 / 40 / 21 / 36 |
| single-batch-stepped | 60 / 57 / 52 / 57 | 9 / 6 / 7 / 6 | 11 / 49 / 15 / 25 |
| single-online | 68 / 67 / 58 / 61 | 9 / 7 / 8 / 4 | 16 / 42 / 12 / 30 |
| multi-public | 71 / 75 / 59 / 65 | 12 / 9 / 7 / 6 | 11 / 38 / 13 / 38 |
| multi-private | 72 / 76 / 61 / 54 | 15 / 12 / 12 / 10 | 9 / 43 / 20 / 28; 1 / 44 / 25 / 30 |
| single-batch-process | 64 / 65 / 54 / 51 | 14 / 10 / 11 / 7 | 10 / 47 / 22 / 21 |
| multi-private-process | 76 / 82 / 77 / 85 | 26 / 21 / 21 / 13 | 6 / 43 / 33 / 18; 0 / 43 / 29 / 28 |

ドメイン別 (single-batch vs multi-private、O / S / L): Responsiveness は人狼 82 / 81 / 68 vs 84 / 82 / 79、候補者選定 61 / 59 / 55 vs 64 / 70 / 45、共同生活 47 / 37 / 27 vs 68 / 76 / 59。Rebuttal は人狼 23 / 16 / 10 vs 23 / 19 / 14、候補者選定 2 / 0 / 2 vs 6 / 5 / 6、共同生活 6 / 5 / 8 vs 15 / 13 / 14。

質問への返答 (resp_to と resp_type = answer から導出。「?」を含む発話を質問、@Name を含むものを名指しの質問とし、同じ期間内に名指しされた本人が answer で応えた割合):

| 条件 | 質問/局 | 名指しの割合 | 誰かが答えた (O / S / L / G) | 名指しされた本人が答えた (O / S / L / G) |
|---|---|---|---|---|
| single-batch | 3.8 | 0.50 | 0.53 / 0.56 / 0.18 / 0.29 | 0.53 / 0.65 / 0.18 / 0.24 |
| single-online | 6.9 | 0.37 | 0.56 / 0.53 / 0.08 / 0.29 | 0.61 / 0.57 / 0.09 / 0.35 |
| multi-public | 6.2 | 0.46 | 0.50 / 0.46 / 0.00 / 0.11 | 0.15 / 0.15 / 0.00 / 0.00 |
| multi-private | 9.4 | 0.65 | 0.26 / 0.28 / 0.02 / 0.08 | 0.13 / 0.07 / 0.04 / 0.04 |
| single-batch-process | 5.2 | 0.64 | 0.51 / 0.57 / - / 0.26 | 0.63 / 0.70 / - / 0.23 |
| multi-private-process | 7.1 | 0.72 | 0.27 / 0.28 / - / 0.03 | 0.04 / 0.04 / - / 0.00 |

読み:
- 応答性は multi が高い (全体で 9〜12 ポイント差、4 注釈者とも)。ドメイン別では人狼と候補者選定で同等か逆転 (Llama は候補者選定で single 55 vs multi 45)、共同生活で multi が高い。応答の中身を見ると、multi の応答には「同意だけ」(agree) が多く (multi-public 38〜42%)、single-batch は「理由を足す」(add) が半分を占める。反論は multi に多く (4 注釈者とも)、筋書きを与えると両方式で増える (object 22 → 33%)。
- 質問への返答は向きが逆で、single の方が答える: multi は質問を 2.5 倍出す (9.4 vs 3.8/局) が、その多くは発話末の「@X, どう思う?」型の締めで、名指しされた本人が答える割合は 0.00〜0.15 にとどまる。single は質問が少なく、出した質問には本人が 0.18〜0.65 で答える (4 注釈者とも single > multi)。v5 の「single は呼びかけても本人が答えない」という読みは、応答性の率を発話数で見たことによる誤りで、質問の対応関係 (resp_to) で追うと逆になる。ただし水準は注釈者が answer をどれだけ使うかに強く依存する (Llama / gpt-oss は応答の 1〜9% しか answer にせず add に寄せる) ので、率そのものではなく向きだけを読む。multi のターン 4 の質問は同じ期間内に答えられない。追加分析にとどめる。
- 注釈者が割れるのは Round 3 の「合唱」(1 人の提案に全員が自分の理由を付けて同調する行) で、Bo の定義では応答とも並列とも読める。

### 5.5 情報の整合性 (族 B、条件 × 事象の違反率表)

| 条件 | 利用: 占い師の初回占いが人狼 (偶然 0.25) | 利用: Day 1 に人狼が処刑 | 開示: 他者の調査結果 (人手確認で本物、件/9 局) | 先出し: 公開前の選択肢名 (件/9 局) |
|---|---|---|---|---|
| single-batch | 1.00 | 1.00 | 1 | 1 (「a coastal lodge」、境界例) |
| single-batch-stepped | 1.00 | 1.00 | 1 (batch と同文) | 0 |
| single-online | 1.00 | 1.00 | 0 (境界例 1) | 1 |
| multi-public | 1.00 | 1.00 | 0 | 0 |
| multi-private | 0.00 | 0.00 | 0 | 0 |
| single-batch-process | 1.00 | 1.00 | 1 | 0 |
| multi-private-process | 0.00 | 0.33 | 0 | 0 |

読み: 全役職を知る条件では占い師が初回の占いで必ず人狼を当て、Day 1 に必ず処刑される。multi-private だけが偶然の水準にある (process を与えた multi-private でも初回命中は 0)。開示は single にのみある: 共同生活 0003 の single-batch で Rin が Shion だけが調べた「設定が落ち着くまで数日かかる」を Shion が話す前に言い (stepped も同文)、共同生活 0002 の single-batch-process で Asuka が May だけが調べた「場所を変えるたびに届けが要る」を May が言っていないのに言った。single-online の「non-refundable deposit」は、調べた本人が「遅れて抜けると残りが払う」と趣旨を共有した後の発話で、境界例とした。語の照合の候補 12 件のうち本物は 3 件 (精度 0.25)。multi-private の候補 4 件はすべて一般語の偶然の一致だった。

### 5.6 注釈者間の一致

2,917 発話を 4 注釈者 (Opus / Sonnet / Llama 3.3 70B / gpt-oss-120b) が注釈した。κ (Cohen) と content (0 / 1 / 2) の完全一致率:

| 対 | Responsiveness κ | Rebuttal κ | content 0 か否か κ | padded κ | content 完全一致 |
|---|---|---|---|---|---|
| Opus vs Sonnet | 0.78 | 0.77 | 0.74 | 0.57 | 0.80 |
| Llama vs Opus | 0.66 | 0.62 | 0.50 | 0.20 | 0.67 |
| Llama vs Sonnet | 0.66 | 0.60 | 0.49 | 0.22 | 0.70 |
| gpt-oss vs Llama | 0.65 | 0.51 | 0.38 | 0.24 | 0.59 |
| gpt-oss vs Opus | 0.58 | 0.54 | 0.36 | 0.22 | 0.63 |
| gpt-oss vs Sonnet | 0.60 | 0.58 | 0.33 | 0.26 | 0.56 |

読み: Responsiveness と Rebuttal は系統をまたいでも κ 0.5〜0.66 で、Samanta et al. の対比較 (人間同士 0.29) より高い。content 0 か否かは Llama と Claude 系で 0.5、gpt-oss は内容を多く数え進展なしを少なく付ける (発話あたり 1.21、進展なし 9%) ため 0.33〜0.38 にとどまる。padded はどの対でも 0.2 前後で、「明らかに少ない語数で言える」の閾値が注釈者ごとに違う。本実験では水増しは記述にとどめ、主張は密度 (content から導出。注釈者の水準差があっても条件の順序は 4 注釈者で一致) で行い、人手標本との一致で content の定義を守る。

### 5.7 コスト (パイロット 6)

| 条件 | 呼び出し/局 | プロンプトトークン/局 | 生成トークン/局 |
|---|---|---|---|
| single-batch | 1 | 2.0k | 1.1k |
| single-batch-stepped | 54 | 140k | 0.7k |
| single-online | 59 | 167k | 1.5k |
| multi-public | 60 | 184k | 2.0k |
| multi-private | 65 | 145k | 2.3k |

### 5.8 仮の結論

(a) single-batch と multi-private は、位置を揃えた発話あたりの新しい内容の数が同程度で、内容の総量も近い (multi が 1.3 倍)。語数は multi が 4 倍で、1 内容あたりの語数は single 14 語、multi 40〜47 語。single は内容が尽きる位置で譲る。差の最大の段は「プロンプトの目標と履歴の置き場所」(stepped → online) にある。(b) 応答性は中身を見れば両方式で近く (2 ドメインで同等)、multi の応答には同意だけの受けが多い。反論は multi に多い。質問への返答は single の方が成立する。(c) 情報の整合性は multi-private だけが保つ。(d) 分割自体は効かない (batch = stepped)。(e) 密度・反論・質問への返答の向きは 4 注釈者 (Claude 系 2、Llama、gpt-oss) で一致し、注釈者間一致は Responsiveness / Rebuttal で κ 0.5〜0.78、content 0 か否かで 0.33〜0.74。主張の向きは本実験で確定する。

## 6. 補助分析: 発話前表現からの将来属性の復号可能性 (密度仮説の機構)

隠れ状態は議論の質の評価には使わない。用途は、(i) 「分割自体は表現を変えない」ことの表現レベルの実証、(ii) 密度仮説の機構の検証である。鍵の比較は single-batch vs single-online: 両者は同じ全情報を持つので、復号可能性の差は情報ではなく「全文を書く目標か次の 1 行を書く目標か」の効果になる。stepped は batch と同一表現で、分割自体の効果がないことの対照。

- **取得**: 記録済みのプロンプトのトークン id と生成トークン id を同じモデル (bf16) に流し込む再生で、全層 4 層おき + 最終層の表現を保存する。位置は `gen_point` (その行の最初のトークンを予測する位置)。推論エンジンのトークン数との一致を全呼び出しで検査する (パイロット 2,730 / 2,730)。
- **恒等性 (実測)**: single-batch と single-batch-stepped は同じトークン列なので、台本が一致する区間で gen_point の表現が全層で cos 1.000 (バッチ不変モード)。
- **条件間の生の類似度は解釈しない**: batch と online / multi の gen_point は別のトークン上にあり、最終層の cos 0.1〜0.4 は無関係な行でも同じ値になる。
- **復号する属性**: (1) これから書く発話の語数、(2) この発話者が次に Over を言うまでの残り発話数、(3) このラウンドと議論全体の残り発話数、(4) 最終の投票先・採択・処刑、(5) 次の発話者が応答するか反対するか。予想: (1)〜(3) は batch で高く online で低い (目標の効果)、(4) は batch と online で同程度に高く multi-private で低い (情報の効果)。統制は入力情報だけの予測器、同一履歴の再生、層ごとの結果。
- **主張の範囲**: 「全文を書く目標で生成すると各行の長さと役割が生成前に決まっている度合いが高く、それが密度を説明する」に限定し、復号可能性は因果ではないと但し書きする。Dong et al. (2025) はプローブの手法として引く。規模: 各ドメイン 100 局 (設定 30 + 追加 70) を single-batch / single-online / multi-private で追加生成する。

## 7. モデル計画

| 役割 | モデル | 理由 |
|---|---|---|
| 生成・主系 (全条件、筋書き、プローブ) | gemma-4-31B-it (dense) | パイロット済み |
| 生成・別系統 (中核 5 条件) | Qwen3.8-27B (dense, Apache 2.0) | 同規模の最新の別系統 |
| 生成・別サイズ (中核 5 条件) | gemma-4-12B-it | 同系列の別サイズ |
| 注釈者 (主) | Llama 3.3 70B Instruct (bf16, tensor parallel 2) | 生成モデルと別系統、手元で配信 |
| 注釈者 (副) | gpt-oss-120b (MoE 117B、MXFP4 が公式の唯一の形式) | 生成モデルとも主注釈者とも別系統。MoE カーネルがこの GPU でバッチ不変モードに対応しないため、判定は temperature 0 のみで走らせる |

生成モデルと注釈モデルは系統を完全に分ける (Qwen を注釈に使わない)。全モデル temperature 0、思考モード無効 (gpt-oss は推論チャネルを使うが出力は最終回答のみ)。バッチ不変モードは生成モデルと Llama に適用し、gpt-oss は非対応のため判定のみ非不変で走らせる (判定は決定的である必要はなく、temperature 0 で十分とする)。chat template、停止列、最大トークン、revision、精度、推論ライブラリの版を header に記録する。「モデル横断」の主張は中核条件の現象の再現に限定し、筋書きとプローブの結論は主系に限る。

## 8. 議論と限界

- **梯子の解釈**: stepped と online の差は「目標」と「置き場所」をまとめて含む。梯子は要因を分離する装置ではなく、段ごとの差を記述して絞り込む装置であり、タスクの性質 (「整合的な議論を書く」vs「与えられた情報で意思決定する」) の違いは文面を揃えても解消しない。本研究は性質を別々に記述し、意思決定の質は主張しない。
- **密度の定義**: 「新しい内容の数」は注釈者の判定に依存する。本実験では人手標本 (約 1,200 発話 × 2 名) との一致で守り、content 0 か否かの κ、0 / 1 / 2 の一致を報告する。密度の主張は「1 内容あたりの語数」で行い、水増し (padded、一致 κ 0.57) は記述にとどめる。
- **応答性の定義**: Bo et al. の Responsiveness は儀礼的な受けも、合唱 (提案への同調の連鎖) も 1 と数えうる。判定者間の不一致はここに集中する。応答の種類と resp_to から導く質問への返答率で定義の感度を示すが、answer / add の境界と期間末の質問の扱いに限界がある。原定義 (直前の 1 発話) との一致も報告する。
- **共通ルール文の 2 文**: 議論の定義と形式の道具の説明で、失敗モードの列挙や量の指示は含まない。2 文は両方式に同じ向きに効いたが、@ の道具は multi のほうが多く使う。2 文を入れる前の結果 (パイロット 6) も同じ記録に残す。
- **注釈者**: 本実験の注釈は Llama 3.3 70B と gpt-oss-120b で、人手標本との一致で守る。パイロットの Claude 系の数値は設計の確認に限る。
- **漏洩検出の再現率**: 語の照合は言い換えを拾えない (パイロットの精度 0.25)。LLM 候補 + 人手確認で補い、非候補の無作為標本で再現率を推定する。人狼の利用指標は再現率の問題がない。
- **multi-public**: 診断用条件。人狼ではゲームの前提が変わる。
- **非決定性**: バッチ不変モードで反復は同一だが、batch と stepped は prefill と decode の数値経路の差で近接確率の反転が起きる。「分割は効かない」は「数値解像度以下の差を除いて」と但し書きする。
- **採らない比較**: multi に「短く話せ」と指示する比較 (指示つき条件になりベースラインが崩れる)、2 × 2 の全セル (条件が倍になる)。
- **一般性**: 5 人、英語、24 ペルソナと固定議題。各ドメイン 30 設定。

## 9. 結論

生成の粒度の差を 5 つの要因に沿って段階的に絞り込む統制基盤を構築し、先行研究の指標セットを発話単位の率として適用し、Lack of progress を「新しい内容の数」に拡張して密度を導くことで、一括生成が席ごとの生成と同程度の内容を 3 分の 1 の語数で言い、内容が尽きる位置で譲ること、応答性は中身を見れば近く反論は席ごとの生成に多いこと、情報の整合性は席ごとの生成だけが保つことを示す設計を提示した。パイロットでは密度の差の最大の段はプロンプトの目標と履歴の置き場所にあり、分割自体は効かなかった。一括生成が人間の会話らしく読めるのは内容や応答が多いからではなく、同じ内容を短く言うからである。その機構を発話前表現からの将来属性の復号可能性で検証し、single の密度を情報と応答性を保ったまま席ごとの生成に移すことが今後の課題である。


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



## 付録 C: 発話単位の注釈指示文 v2 (LLM 注釈者と人手検証に共通)

`````
# Utterance-level annotation of discussion transcripts (v2)

You will read transcripts of five-person discussions (a Werewolf game, a grant review panel, or a household /
club decision). Each record shows the discussion period by period (`## Day n` / `## Round n`), one line per
utterance in the order spoken, prefixed by an id in brackets: `- [17] **Name**: utterance`. Votes and the outcome
follow each period. A participant who did not speak at a given chance has no line. Participants may address one
another with `@Name`.

For **every utterance** in the file, give the following. Judge each utterance against the record only (what was
actually said before it), not against what you think the participants should have known. Do not judge by length,
politeness or who is right.

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

Rules: judge each utterance independently; use 1 (or a count above 0) only when the evidence is in the text; when
unsure about `rebut` or `padded`, use 0; when unsure about `content`, prefer the lower count. For every utterance
where `rebut` or `padded` is 1, or `content` is 0, add a `note` of at most one short sentence pointing to the
evidence (e.g. "repeats [12]", "closing pleasantry").

Output: a JSON list with one object per utterance, in order, written to the output file given in your task:
```
[{"seq": 17, "speaker": "Name", "content": 0|1|2, "resp": 0|1, "resp_to": 12|null,
  "resp_type": "answer"|"add"|"object"|"agree"|null, "rebut": 0|1, "padded": 0|1, "note": "..."}, ...]
```
Include every utterance of the file exactly once. Read only the files named in your task; modify nothing but your
output file.
`````


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


**v5 → v6 (外部レビューと自己検証、2026-10-28 夜)**: レビューの指摘 (要因の分離の過大主張、発話数の交絡、情報関連指標の混在、応答性の定義、統計、ペルソナの妥当性) を仕分けし、書き方 (梯子は段階的な絞り込み、stepped は negative control、ペルソナは共通集団の統制)、分析 (位置を揃えた比較、語で重みづけた冗長さ)、族 B の 3 分類、統計 (主要比較 5 つ、階層モデル) で対応した。パイロット 8 の読み直しで、single と multi の差が「中身」ではなく「同じ内容を言う語数」にあることを確認し、Becker の Lack of progress を「新しい内容の数」に拡張して密度を導く設計に改めた。応答性には resp_to と応答の種類を加え、質問への返答率を導出した (v5 の「single は呼びかけても答えない」は逆だった)。判定モデルを生成モデルと系統で分け (Llama 3.3 70B / gpt-oss-120b)、Claude 系との一致を確認した。採らなかった提案: multi への「短く話せ」指示、2 × 2 の全セル、Evidence usage / Stance / Distinct-N の継続。

## 付録 F: 第三者レビューへの質問 (v6)

1. 中心の主張を密度仮説 (同じ内容を 3 分の 1 の語数で言い、内容が尽きる位置で譲る) に置いたことは、v5 の「二重のトレードオフ」より明確で、設計から導ける範囲に収まっているか。
2. 「新しい内容の数」(Becker の Lack of progress の 0 / 1 / 2 への拡張) と、そこから導く密度・内容の総量は、独自指標として守れているか (人手検証 約 1,200 発話 × 2 名、注釈者間 κ 0.74〜0.80)。
3. 位置を揃えた比較 (§5.3) は、切り上げによる生存バイアスの切り分けとして十分か。
4. 応答性に resp_to と応答の種類を加え、質問への返答率を導出する扱い (§5.4) は、Bo の指標の「借用した上での変更」として許容されるか。原定義との一致も報告する。
5. 族 B の 3 分類 (開示 / 利用 / 先出し) の違反率表は読みやすいか。開示の検出 (語の照合の精度 0.25 + LLM 候補 + 人手全件確認) は十分か。
6. 梯子を「分離」ではなく「段階的な絞り込み」と書き、stepped を negative control とした書き方は、レビューの指摘に答えているか。
7. 判定モデル (Llama 3.3 70B bf16 / gpt-oss-120b MXFP4) と生成モデル (gemma-4 / Qwen3.8) を系統で分けた計画は十分か。gpt-oss をバッチ不変モードなし (temperature 0 のみ) で走らせることは問題か。
8. 隠れ状態の分析を密度仮説の機構 (生成前に各行の長さと役割が決まっている度合い) の検証として位置づけた扱いは、過大主張にならないか。
9. 統計 (主要比較 5 つ、設定単位の階層モデル、同等性マージン) は適切か。
10. タイトルと貢献は設計から導ける範囲に収まっているか。
