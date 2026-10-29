# 論文シナリオ草稿 v8 (gemma-4-31B の本実行の結果を反映、2026-10-29)

> **位置づけ**: §5 の数値は **本実験の主系 (gemma-4-31B-it) の全 630 局** (3 ドメイン × 30 設定 × 7 条件) の実測で、注釈は Llama 3.3 70B (L) と gpt-oss-120b (G) の 2 者。パイロット 8 (設定 0001〜0003 の 63 局) の記録は 30 設定の一部としてそのまま使い (生成は決定的)、確証的な検定は残り 27 設定で行う (未実施)。§6 の隠れ状態は本実行の 630 局から取得し、線形プローブの第一結果を載せた (対照課題、全層、転移、k 手先の復号は未)。別系統 (Qwen3.8-27B) と別サイズ (gemma-4-12B) の中核 5 条件は順次実行し、結果が出るたびに §5.10 に追記する。v7 からの変更: §5 を本実行の数値に置き換え、応答性の読みを「multi が一貫して高い」に改めた (パイロットの「ドメインに依存」は小標本の読み)。content の上限の感度分析、人手検証、開示候補の人手確認、統計の細部は未。

---

## タイトル案

第一候補: **Same Content, a Third of the Words: Whole-Transcript versus Line-by-Line Generation of LLM Multi-Party Discussions**

第二候補: **One Call or One Line at a Time? Where Density, Mutual Response and Information Consistency Change between a Single Writer and Per-Seat Agents**

日本語仮題: 台本を一括で書く単一 LLM と席ごとの LLM による多人数議論生成の統制比較: 全文の生成目標が内容の密度を決め、情報アクセスが整合性を決める

## 概要

LLM に複数人の議論を生成させる方法には、1 つの LLM が台本全体を一括で書く方法 (single) と、参加者ごとに独立した LLM を置いて 1 発話ずつ対話させる方法 (multi) がある。両者はプロンプトや進行手続きが違うまま比べられてきた。本研究は、同一モデル・同一ルール文・同一台本文法・同一の情報公開スケジュールのもとで差分を設計した軸だけに絞った比較基盤を構築し、「誰が会話を生成し、どの情報を閲覧できるかは、発話の密度・相互応答・情報整合性にどう影響するか」を 3 ドメイン (人狼、候補者選定、共同生活の取り決め) × 各 30 設定 × 5 条件の梯子 (single-batch / single-batch-stepped / single-online / multi-public / multi-private) で測る。隣り合う段は「結末と構造の決め手」「生成目標と履歴の置き場所 (と役割文)」「文脈の分割 (と役割文)」「情報量」で異なる。評価は「会話としての質」と「情報の整合性」を別の族として測り、合成しない。前者は Bo et al. の Responsiveness / Rebuttal / Non-repetition と PLACES の長さ指標に加え、Becker et al. の「進展のない発話」を「発話が加える新しい内容の数」に拡張し、そこから密度 (1 つの新しい内容あたりの語数) と内容の総量を導く。後者は知りえない事実の開示、特権情報の利用、選択肢の先出しを条件 × 事象の違反率表で報告する。主系 (gemma-4-31B、630 局、注釈は Llama 3.3 70B と gpt-oss-120b) では、両端の single-batch と multi-private は位置を揃えた発話あたりの新しい内容の数が同程度 (1.0〜1.6) で、内容の総量は multi が 1.4〜1.5 倍、語数は 3.6 倍、1 内容あたりの語数は single 10〜15 語、multi 26〜40 語だった (90 設定すべて、両注釈者で single が低い。設定ごとの比の中央値 2.6〜2.8)。この差の最大の段は single の内部、「全文を 1 回で書く」から「次の 1 行を書く」に変わる段 (15 → 31 語) にあり、文脈の分割と情報量の段はその上に小さく足されるだけだった。応答性は multi が 20 ポイント高く、反論は 2 倍で、名指しの質問に本人が答える割合は single が高い。情報の整合性は情報アクセスで決まり、全役職を知る条件 (single の 4 条件と multi-public) では占い師が初回の占いで必ず人狼を当て (1.00)、自席の情報だけの multi-private では偶然の水準 (0.27) になる。生成直前の表現からの線形プローブでは、次の発話の語数と自分があと何回話すかが、全文を書く条件で最もよく復号できた (入力特徴の基準線からの上積み: 語数 +0.30 vs 1 行ずつ +0.16、multi +0.07)。本研究はこの「生成目標が密度を決め、情報アクセスが整合性を決める」という分解を示す。

## 1. はじめに

LLM を用いた多人数議論の生成は、社会シミュレーション、対話データの合成、ゲーム AI に使われる。生成の仕方には、1 回の生成で議論全体を書き下ろす中央集権的な方法と、各参加者を独立した LLM にして逐次に応答させる分散的な方法がある。前者は整合的な台本を書きやすく、後者は参加者が互いに反応する対話になりやすい、と言われるが、既存の比較は方式ごとにプロンプトや進行手続きが異なり、どの差がどの性質を生むのかを特定できない。面接対話では対話エージェント方式が一括生成より高く評価されたという報告 (De Baer et al., GEM 2025) もあり、「どちらが良いか」は設定と観点に依存する。

本研究の問いは「多人数議論において、誰が会話を生成し、どの情報を閲覧できるかは、発話の密度・相互応答・情報整合性にどう影響するか」である。自己回帰モデルでは、同じトークン列を一度に生成しても、1 行ずつ止めて同じ接頭辞から再開しても、greedy なら同じ続きが出る。したがって「一括か逐次か」の差は、生成を分割すること自体ではなく、(1) プロンプトの目標、(2) 履歴の置き場所、(3) 結末と構造の決め手、(4) 文脈の分割、(5) 情報量のどこかから生じる。本研究はこの 5 つを段階的に変えた条件の梯子を並べ、隣り合う段の差を記述することで、差がどこで生じるかを絞り込む。梯子の両端 (single-batch と multi-private) の差を見るだけでなく、段を 1 つずつ上がるときに各性質がどう動くかを追い、主要因の候補を挙げる。

本稿が主張したいことは次の 3 点で、評価設計はこれらを**別々に**測れるように組む (優劣の合成点は作らない)。

- **密度**: 一括生成と席ごとの生成は、議論が加える新しい内容 (論点・根拠・質問・提案・票の意思表示) の数では大差がない。一括生成は同じ内容をおよそ 3 分の 1 の語数で言い、言うことがなくなれば Skip / Over でターンを畳む。席ごとの生成は同じ内容を上限いっぱいの語数で言い、同じ発話の中の言い直しと定型の前置き・締めで埋める。この差は好みの判定に頼らず「1 つの新しい内容あたりの語数」で示せる。そして差の大半は「誰が書くか」ではなく「1 回の呼び出しで議論全体を書くか、次の 1 行を書くか」という生成目標の段で生じる (同じ全知の書き手でも、1 行ずつ書かせると密度は席ごとの生成に近づく)。
- **相互応答**: 他者の発言に応える率は、中身を見れば両方式で近い (ドメインによっては席ごとの生成が高い)。明示的な反論は席ごとの生成に多い。応答の種類 (質問に答える / 理由を足す / 反対する / 同意だけ) の分布も報告する。
- **情報の整合性**: 全員の秘密を知る生成 (一括生成の全条件と、全情報を開示した席ごとの生成) では、参加者が知らないはずの事実が発話に混ざり (開示)、占い先や投票先が特権情報で動く (利用)。これは生成方式ではなく情報アクセスの効果で、自席の情報だけを持つ席ごとの生成でだけ消える。

機構の仮説: 全文を 1 回で書く生成は議論全体 (誰が何を言い、どう決まるか) を持ったまま各行を書くので、1 行ごとに議論の中で果たす役割と長さが生成前に決まっており、長く話す必要がない。次の 1 行を書く生成 (同じ書き手でも、席ごとでも) は結末も次の展開も決めないまま書くので、不確実さを埋めるように長くなる。これは発話生成直前の内部表現から将来属性がどの程度復号できるかの差として検証できる (§6)。

いずれも両方式に同じルール文を与えたときの方式の性質 (傾向) として記述し、「良い」とは言わない。single の密度を、情報と応答性を保ったまま multi に移す (蒸留) ことは本稿の範囲外の今後の課題とし、基盤はそれを見据えて設計する。

**研究課題**

- RQ1 (密度と相互応答): 一括生成と席ごとの生成は、新しい内容の数・密度・譲り・応答性・反論のそれぞれでどう違うか。差は梯子のどの段 (結末の決め手 / 生成目標と置き場所 / 文脈の分割 / 情報量) で生じ、主要因の候補は何か。
- RQ2 (情報の整合性): 全員の秘密を知る生成はどの程度、知らないはずの情報を開示し、特権情報を利用するか。それは生成方式と情報アクセスのどちらで決まるか。
- RQ3 (機構と頑健性): 発話生成直前の表現から将来属性 (語数、残り発話数、結末) が復号できる度合いは方式でどう違うか。傾向はドメイン・モデル・筋書きの有無を変えても再現するか。

**貢献**: (1) 差分を設計した軸だけに絞った比較基盤 (共通ルール文・共通台本文法・席ビューと書き手ビューの決定的復元・違反と正規化の共通記録・推論エンジンが見たトークン id の記録・バッチ不変モードによる決定的な再現)。(2) 5 条件の梯子による段階的な絞り込みの設計と、分割自体が効かないこと (batch = stepped、表現も同一) の実証。(3) 先行研究の指標セットを発話単位の率として適用し、Lack of progress を「新しい内容の数」に拡張して密度を導く評価設計。「会話としての質」と「情報の整合性」を分けて報告し、LLM の対比較判定が表示と問いで向きを変えることの実証 (§4.5)。(4) 密度の差が生成目標の段で生じ、情報の整合性が情報アクセスの段で決まるという分解、および反論 (multi に多い) と質問への返答 (single が成立しやすい) の記述。

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
| single-batch-stepped vs single-online | 生成目標 (全文か次の 1 行か) + 履歴の置き場所 (assistant の続きか user の貼り直しか) + 役割文の 1 文 (「1 行ずつ書く」)。この 3 つは同居する (さらに分けるには online の役割文を batch の履歴置き場で使う条件が要る。将来課題) |
| single-online vs multi-public | 1 つの全知の文脈か、席ごとに分割された文脈か (他席の夜の行動・調査の可視性を含む) + 役割文 (「議論の書き手」から「参加者 X」へ; 三人称で書くか一人称で演じるか)。両方を「書き手」に揃えるのは席ごとの生成として不自然なので、この同居は受け入れ、限界に記す |
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

### 3.5 共通ルール文の 2 文

共通ブロック `## Discussion format` には、議論という活動の定義と、形式の道具の説明として次の 2 文を置く (両方式に同文。量や形式の指定、評価指標に直結する語は入れない。失敗モードの列挙や「短く話せ」のような指示は、指示に従った議論の比較になるので入れない)。

1. 「The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.」(話し合いは参加者どうしの会話であり、互いに応答し、決定はそのやり取りから出る)
2. 「A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said.」(@名前 で他の参加者に直接、質問・返答・同意・反対ができる)

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
| A | Responsiveness (原定義) | 直前の 1 発話に取り組んだか | Bo et al. (2026) | LLM 注釈 + 人手検証 |
| A | Responsiveness-W (resp) + resp_to | 自分の前の発話以降に言われた特定の発話に取り組んだか (答える・同意・問う・積み上げる・反対)。応えた発話の id を同時に出す | 本研究の補助定義 (Bo の指標の窓を、5 人の順番発話に合わせて「自分の前の発話以降」に広げたもの)。原定義と並べて報告する | LLM 注釈 + 人手検証 |
| A | Rebuttal (rebut) | それに明示的に反対したか | Bo et al. (2026) | LLM 注釈 + 人手検証 |
| A | 応答の種類、質問への返答 (追加分析) | 応答 1 の発話を answer (質問に答える) / add (理由を足す) / object (反対) / agree (同意だけ) に分類。名指しの質問に本人が応えた割合を resp_to から導く | 本研究 (補助の導出) | 同じ注釈で |
| B | 開示 | 発話者が知りえない事実 (他者の調査結果の内容、他者の役職) を発話した件数 | 独自 | 機械候補 + LLM 候補 + 人手確認 |
| B | 利用 | 占い先・投票先が特権情報で動いた: 占い師の初回占いが人狼を当てる率 (偶然 0.25)、Day 1 に人狼が処刑される率 | 独自 (全知の書き手の縮退) | 自動 |
| B | 先出し | 公開前の選択肢名の出現 (Round 1〜2 に正式名) | 独自 | 自動 |
| 検証 | 注釈者間一致 (κ)、人手標本との一致、判定モデルの系統差 | | Samanta et al. (2026) の判定器検査の手順に倣う |

手続き指標 (違反率・正規化率、トークン数・呼び出し回数・時間) は別表で報告する。MARBLE の Communication Score (Zhu et al., 2025) は原著手順で算出した参照値として付録に置く。v5 にあった Evidence usage / Stance / Distinct-N は条件差がなく (パイロット 6)、落とした。

### 4.2 発話単位の注釈

- **材料**: 各局の記録を期間の見出し、発話 (順序どおり、id つき)、票、結果だけの形に描画する。ターン見出し、Skip / Over (人間の議論に存在しない手続きの記号。ルールで数えるだけ)、夜の行動と調査の行 (読者が見ない秘密情報) は落とす。
- **問い**: 発話ごとに content (0 / 1 / 2)、resp (窓つき) + resp_to、resp_type、rebut、padded を付ける。原定義の Responsiveness は resp_to が直前の発話かどうかから導く。各項目は 1 文の定義 + 境界の例で指示し (付録 C)、長さ・丁寧さ・正しさで判断しないこと、迷ったら 0 (content は低い方) を明記する。好みや優劣は問わない。
- **注釈者**: 手元で配信する Llama 3.3 70B Instruct (bf16) と gpt-oss-120b (MXFP4、公式の唯一の形式) の 2 者、どちらも temperature 0、同じ指示文。バッチ不変モードは生成にだけ適用し、判定には適用しない (決定的である必要がなく、gpt-oss の MoE カーネルは対応もしない)。外部 API は使わず、生成モデル (gemma-4 / Qwen3.8) とは系統を分ける。両者の一致 (κ) と、同一入力での反復の自己一致を報告する。
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

## 5. 結果: 主系 (gemma-4-31B-it、630 局)

実行: gemma-4-31B-it、temperature 0、バッチ不変モード、現行プロンプト (2 文入り)、3 ドメイン × 30 設定 × 7 条件 (5 条件 + single-batch-process + multi-private-process) = 630 局。設定 0001〜0003 の 63 局はパイロット 8 の記録 (同じ手順)。注釈は Llama 3.3 70B (L) と gpt-oss-120b (G)、同じ指示文 (付録 C)、temperature 0。single-batch の反復はパイロットで 9/9 設定で全文一致 (決定的)、single-batch と stepped は接頭辞が一致する区間の後、近接確率の反転で分岐する。

### 5.1 長さと譲り (自動指標、7 条件、3 ドメイン平均)

| 条件 | 発話数/局 | 語数/発話 | 語数/局 | 上限張りつき | Non-repetition | Skip / Over | 全員パスのターン |
|---|---|---|---|---|---|---|---|
| single-batch | 37.0 | 14.0 | 520 | 0.00 | 0.70 | 3.0 / 8.3 | 2.0 |
| single-batch-stepped | 37.6 | 13.8 | 522 | 0.00 | 0.70 | 3.0 / 8.0 | 2.0 |
| single-online | 47.5 | 26.7 | 1263 | 0.06 | 0.63 | 1.4 / 3.6 | 0.7 |
| multi-public | 47.2 | 32.9 | 1545 | 0.42 | 0.60 | 1.1 / 5.6 | 0.6 |
| multi-private | 54.9 | 33.9 | 1861 | 0.49 | 0.61 | 0.2 / 2.7 | 0.0 |
| single-batch-process | 43.3 | 15.8 | 684 | 0.00 | 0.70 | 1.9 / 8.1 | 1.6 |
| multi-private-process | 55.1 | 35.3 | 1942 | 0.63 | 0.59 | 0.0 / 1.6 | 0.0 |

読み: 梯子を上がるほど発話は長くなり、上限に張りつき、Skip / Over を使わなくなる。batch と stepped は一致する (分割自体は効かない)。最大の段差は stepped → online (語数/発話 13.8 → 26.7、語数/局 522 → 1263、Over 8.0 → 3.6)。multi-public → multi-private (情報量) は張りつき率を 0.42 → 0.49 に上げる。

### 5.2 密度: 新しい内容の数と 1 内容あたりの語数 (中心の結果)

局あたりの合計 (条件平均)。content は注釈者の判定 (L / G)。

| 条件 | 語数/局 | 新しい内容の数/局 (L / G) | 1 内容あたりの語数 (L / G) | 進展なし発話の語の割合 % (L / G) | 水増し発話 % (L / G) |
|---|---|---|---|---|---|
| single-batch | 520 | 34 / 50 | 15.1 / 10.4 | 11 / 2 | 2 / 6 |
| single-batch-stepped | 522 | 36 / 51 | 14.6 / 10.2 | 11 / 2 | 3 / 6 |
| single-online | 1263 | 41 / 63 | 31.1 / 20.0 | 16 / 5 | 7 / 8 |
| multi-public | 1545 | 38 / 66 | 40.4 / 23.5 | 24 / 9 | 9 / 12 |
| multi-private | 1861 | 47 / 73 | 40.0 / 25.5 | 19 / 9 | 9 / 13 |
| single-batch-process | 684 | 40 / 61 | 17.3 / 11.3 | 10 / 2 | 3 / 6 |
| multi-private-process | 1942 | 47 / 73 | 41.0 / 26.8 | 20 / 9 | 8 / 9 |

(1 内容あたりの語数は局の合計から; 発話あたりの率は 100 発話あたりの局平均。)

読み:
- **内容の総量は近く、語数は 3.6 倍**: multi-private は single-batch より新しい内容が 1.4〜1.5 倍多い (設定ごとの比の中央値 L 1.38、G 1.47; multi が多いのは 77 / 75 設定) が、語数は 3.6 倍 (1861 vs 520)。1 つの新しい内容あたりの語数は single 10〜15 語、multi 26〜40 語で、**90 設定すべて、両注釈者で single が低い** (設定ごとの比の中央値 L 2.76、G 2.61; 範囲 1.1〜5.2)。ドメイン別の中央値も 2.2〜2.9 でそろう。gpt-oss は内容を多く数え (発話あたり 1.35 vs 0.88)、進展なしを少なく付けるが、条件の順序は変えない。
- **梯子**: 密度の最大の段差は stepped → online (L 14.6 → 31.1 語、G 10.2 → 20.0) で、長さと同じ段にある。online → multi-public (分割) で 40 / 24、multi-public → multi-private (情報量) で 40 / 26 と、段ごとに少しずつ下がる。密度の差の大半は、同じ全知の書き手の内部で「全文を 1 回で書く」から「次の 1 行を書く」に変わるときに生じる。
- **進展なし発話 (content 0) の語の割合**は single 11% / 2%、multi 19% / 9%。発話あたりの率は人狼で single と multi が近い (23 vs 19、L) が、語で重みづけると multi の無駄のほうが大きい。
- **水増し**は single 2〜6%、multi 9〜13% (2 注釈者の一致は低く、記述にとどめる。§5.6)。
- 筋書き (process) は single-batch の内容の総量を増やし (34 → 40 / 50 → 61)、密度は少し下げる (15 → 17 / 10 → 11)。

### 5.3 位置を揃えた比較 (切り上げの生存バイアスの切り分け)

ラウンド・ターン位置ごとの発話あたりの新しい内容の数 (L / G 合算、3 ドメイン、人狼の Day 0 は省略)。

| 位置 (ラウンド, ターン) | single-batch | multi-private | single-online | multi-public |
|---|---|---|---|---|
| R1 T1 | 1.40 | 1.32 | 1.38 | 1.48 |
| R1 T2 | 1.14 | 1.12 | 1.03 | 1.03 |
| R1 T3 | 1.08 | 0.97 | 0.95 | 0.89 |
| R1 T4 | 0.88 | 0.73 | 0.78 | 0.81 |
| R2 T1 | 1.63 | 1.48 | 1.59 | 1.73 |
| R2 T2 | 1.05 | 1.18 | 1.14 | 1.23 |
| R2 T3 | 1.07 | 1.16 | 1.13 | 1.15 |
| R2 T4 | 0.89 | 1.02 | 0.98 | 0.91 |
| R3 T1 | 1.35 | 1.28 | 1.26 | 1.28 |
| R3 T2 | 1.01 | 1.08 | 1.01 | 0.82 |
| R3 T3 | 0.87 | 0.99 | 0.96 | 0.69 |
| R3 T4 | 0.57 | 0.82 | 0.72 | 0.58 |

読み: 同じ位置では発話あたりの新しい内容の数は single と multi で同程度 (差は ±0.15 以内が大半。R3 T4 だけ multi が 0.25 高い)。single が発話を減らすのはターン 3〜4 (Over) で、multi でも内容が落ちる位置である。single は「内容のある位置を切り上げている」のではなく「内容が尽きる位置で譲っている」。multi の内容の総量が 1.4 倍多いのは、主にターン 3〜4 の発話数が多いことによる。事前に置いた同等性マージン (±0.1) は R1〜R2 のターン 1〜3 で満たし、R3 T4 では満たさない。

### 5.4 相互応答 (Responsiveness-W / Rebuttal、応答の種類、質問への返答)

100 発話あたり (L / G)。

| 条件 | Responsiveness-W (L / G) | Rebuttal (L / G) | 応答の種類 answer / add / object / agree (%、L; G) |
|---|---|---|---|
| single-batch | 52 / 47 | 9 / 8 | 3 / 39 / 24 / 34; 8 / 57 / 17 / 19 |
| single-batch-stepped | 53 / 49 | 10 / 7 | |
| single-online | 60 / 63 | 11 / 9 | 1 / 39 / 23 / 37; 8 / 55 / 14 / 23 |
| multi-public | 68 / 70 | 12 / 11 | 1 / 34 / 20 / 45; 4 / 52 / 13 / 30 |
| multi-private | 73 / 74 | 19 / 18 | 0 / 36 / 30 / 34; 2 / 51 / 23 / 24 |
| single-batch-process | 54 / 50 | 12 / 9 | 2 / 40 / 26 / 32; 6 / 59 / 18 / 17 |
| multi-private-process | 76 / 79 | 22 / 20 | 0 / 37 / 31 / 32; 1 / 53 / 24 / 22 |

ドメイン別 (single-batch vs multi-private、L / G): Responsiveness-W は人狼 67 / 65 vs 77 / 78、候補者選定 44 / 36 vs 69 / 67、共同生活 46 / 39 vs 73 / 76。Rebuttal は人狼 14 / 17 vs 22 / 22、候補者選定 5 / 2 vs 16 / 13、共同生活 8 / 4 vs 20 / 18。

質問への返答 (resp_to と resp_type = answer から導出。「?」を含む発話を質問、@Name を含むものを名指しの質問とし、同じ期間内に名指しされた本人が answer で応えた割合):

| 条件 | 質問/局 | 名指しの割合 | 誰かが答えた (L / G) | 名指しされた本人が答えた (L / G) |
|---|---|---|---|---|
| single-batch | 3.9 | 0.47 | 0.16 / 0.25 | 0.23 / 0.34 |
| single-batch-stepped | 4.1 | 0.49 | 0.18 / 0.32 | 0.28 / 0.40 |
| single-online | 5.6 | 0.32 | 0.05 / 0.27 | 0.12 / 0.28 |
| multi-public | 6.1 | 0.63 | 0.04 / 0.17 | 0.04 / 0.12 |
| multi-private | 8.1 | 0.64 | 0.01 / 0.07 | 0.01 / 0.05 |
| single-batch-process | 4.8 | 0.51 | 0.11 / 0.23 | 0.18 / 0.29 |
| multi-private-process | 7.3 | 0.66 | 0.01 / 0.06 | 0.00 / 0.01 |

読み:
- 応答性 (窓つき) は **multi が一貫して高い** (全体で 21〜27 ポイント、3 ドメインとも multi; 両注釈者とも)。段ごとには stepped → online で +7〜14、online → multi-public で +7〜8、multi-public → multi-private で +4〜5 と、密度とは違って段ごとに積み上がる。応答の中身は、multi は反対 (object) と同意だけ (agree) が多く、single は理由を足す (add) が多い。反論は multi が 2 倍 (9 vs 19)、筋書きを与えると両方式で増える。
- 質問への返答は向きが逆で、single の方が答える: multi は質問を 2 倍出す (8.1 vs 3.9/局) が、その多くは発話末の「@X, どう思う?」型の締めで、名指しされた本人が答える割合は 0.01〜0.05。single は質問が少なく、出した質問には本人が 0.23〜0.34 で答える (両注釈者とも single > multi)。水準は注釈者が answer をどれだけ使うかに依存する (応答の 0〜8% しか answer にせず add に寄せる) ので、率そのものではなく向きだけを読む。resp_type に依存しない定義 (名指しされた本人の次の発話の resp_to が質問の id か) での再計算は未。
- 注釈者が割れるのは Round 3 の「合唱」(1 人の提案に全員が自分の理由を付けて同調する行) で、Bo の定義では応答とも並列とも読める。

### 5.5 情報の整合性 (族 B、情報アクセス × 生成方式の違反率表)

| 情報アクセス | 条件 | 利用: 占い師の初回占いが人狼 (偶然 0.25) | 利用: Day 1 に人狼が処刑 | 先出し: 公開前の選択肢名 (件/局、自動) | 開示: 語照合の候補 (件/局、未確認) |
|---|---|---|---|---|---|
| 全員の秘密 | single-batch | 1.00 | 1.00 | 0.48 | 0.13 |
| 全員の秘密 | single-batch-stepped | 1.00 | 1.00 | 0.48 | 0.08 |
| 全員の秘密 | single-online | 0.90 | 1.00 | 0.55 | 0.23 |
| 全員の秘密 | multi-public | 1.00 | 1.00 | 0.60 | 0.13 |
| 自席のみ | multi-private | 0.27 | 0.40 | 0.00 | 0.17 |
| 全員の秘密 | single-batch-process | 1.00 | 1.00 | 0.42 | 0.12 |
| 自席のみ (+ 筋書き) | multi-private-process | 0.23 | 0.47 | 0.03 | 0.10 |

読み: 「利用」は情報アクセスで決まる。全役職を知る条件では、生成方式 (single の 4 条件、席ごとの multi-public) によらず占い師が初回の占いでほぼ必ず人狼を当て (0.90〜1.00)、Day 1 に必ず処刑される。自席の情報だけの multi-private は偶然の水準 (0.27、Day 1 処刑 0.40) にある。これは「single の副作用」ではなく「知っていて知らないふりをする課題に、どの生成方式も失敗する」ことの定量化であり、梯子の上では multi-public → multi-private (情報量) の段の効果である。筋書きを与えた multi-private-process も偶然の水準 (0.23) で、process 筋書きからの結末の漏洩は見られない (公開情報だけの筋書き対照は未)。「先出し」(Round 1〜2 の正式な選択肢名) は全知の条件で 0.4〜0.6 件/局、multi-private で 0。「開示」の語照合の候補は 212 件で人手確認は未 (パイロットでは精度 0.25、本物は single のみ)。

### 5.6 注釈者間の一致

29,016 発話を Llama 3.3 70B と gpt-oss-120b が注釈した。κ (Cohen) と content (0 / 1 / 2) の完全一致率:

| 項目 | Responsiveness-W | Rebuttal | content 0 か否か | padded | content 完全一致 |
|---|---|---|---|---|---|
| Llama vs gpt-oss | 0.62 | 0.60 | 0.33 | 0.23 | 0.50 |

読み: Responsiveness-W と Rebuttal は系統をまたいで κ 0.6 で、Samanta et al. の対比較 (人間同士 0.29) より高い。content 0 か否かは 0.33 で、gpt-oss が内容を多く数え進展なしを少なく付ける (進展なし 7% vs 20%) 水準差が主因。水準差があっても条件の順序 (密度、内容の総量、譲り、応答、反論) は両者で一致する。padded は 0.23 で記述にとどめる。人手標本との一致で content の定義を守り、人手との一致が高い注釈者を主に据える (未実施)。

### 5.7 コスト

| 条件 | 呼び出し/局 | プロンプトトークン/局 | 生成トークン/局 |
|---|---|---|---|
| single-batch | 1 | 2k | 1.2k |
| single-batch-stepped | 57 | 159k | 0.9k |
| single-online | 61 | 184k | 1.7k |
| multi-public | 59 | 192k | 2.1k |
| multi-private | 65 | 157k | 2.5k |
| single-batch-process | 1 | 2k | 1.5k |
| multi-private-process | 65 | 169k | 2.6k |

### 5.8 段ごとの変化と主要因の候補

梯子を 1 段ずつ上がるときの各性質の変化 (3 ドメイン平均。注釈は L)。

| 段 | 変わるもの | 語数/発話 | 1 内容あたりの語数 | Over/局 | Responsiveness-W | Rebuttal | 占い師初回命中 |
|---|---|---|---|---|---|---|---|
| single-batch → stepped | 結末と構造の決め手 | 14.0 → 13.8 | 15.1 → 14.6 | 8.3 → 8.0 | 52 → 53 | 9 → 10 | 1.00 → 1.00 |
| stepped → single-online | 生成目標 + 履歴の置き場所 + 役割文の 1 文 | 13.8 → 26.7 | 14.6 → 31.1 | 8.0 → 3.6 | 53 → 60 | 10 → 11 | 1.00 → 0.90 |
| single-online → multi-public | 文脈の分割 + 役割文 (書き手 → 参加者) | 26.7 → 32.9 | 31.1 → 40.4 | 3.6 → 5.6 | 60 → 68 | 11 → 12 | 0.90 → 1.00 |
| multi-public → multi-private | 情報量 | 32.9 → 33.9 | 40.4 → 40.0 | 5.6 → 2.7 | 68 → 73 | 12 → 19 | 1.00 → 0.27 |

読み (主要因の候補):
- **分割自体は効かない** (第 1 段): すべて変わらない。negative control として成立。
- **密度と譲りは生成目標の段で決まる** (第 2 段): 語数が 2 倍、密度が半分、Over が半分以下になる。この段は生成目標・履歴の置き場所・役割文の 1 文が同居する。
- **文脈の分割はさらに密度を下げ、応答を増やす** (第 3 段): 席ごとに分かれると語数が 2 割増え、密度が 4 分の 3 になり、応答性が +8。役割文の変化 (書き手 → 参加者) を含む。
- **情報量は整合性を決め、反論を増やす** (第 4 段): 占い師の初回命中が 1.00 → 0.27 に落ち、反論が 12 → 19 に増える (自席の情報だけだと他者の主張に反対する余地が生まれる)。密度はほぼ変わらない。
- 両端の差 (single-batch vs multi-private) は「生成目標の段」(密度・譲り) と「分割 + 情報量の段」(応答・反論・整合性) の足し合わせとして読める。

### 5.9 結論 (主系)

(a) single-batch と multi-private は、位置を揃えた発話あたりの新しい内容の数が同程度で、内容の総量は multi が 1.4〜1.5 倍。語数は multi が 3.6 倍で、1 内容あたりの語数は single 10〜15 語、multi 26〜40 語 (90 設定すべて)。single は内容が尽きる位置で譲る。(b) この差の大半は生成目標の段 (stepped → online) で生じ、文脈の分割と情報量はその上に小さく足される。分割自体は効かない (batch = stepped)。(c) 応答性は multi が一貫して高く (+21〜27)、反論は 2 倍。名指しの質問への本人の返答は single で成立しやすい。(d) 情報の整合性は情報アクセスで決まり、自席の情報だけの multi-private だけが保つ。(e) (a)〜(d) の向きは 2 注釈者で一致し、注釈者間一致は Responsiveness-W κ 0.62、Rebuttal 0.60、content 0 か否か 0.33。確証的な検定 (27 設定) は未。

### 5.10 別系統: Qwen3.8-27B (720 局) と、全文の目標を席ごとに移植した条件

Qwen3.8-27B は線形注意のハイブリッドで vLLM のバッチ不変モードが使えないため、1 リクエストずつ (batch size 1、接頭辞キャッシュなし) 配信し、設定ごとに全条件を同じサーバインスタンスで生成した (インスタンス間では自動チューニングの差で丸めが変わる)。single-batch の同一インスタンスでの反復は 90/90 設定で全文一致。中核 5 条件に加え、**multi-private-stepped** (各席が自席の参加者プロンプトと自席ビューのまま、single-batch と同じ全文の要求で続きを書き、サーバは自席の 1 行だけを採る)、その筋書きあり版、全知版 (multi-public-stepped) を各 90 設定で生成した。注釈は L / G。

| 条件 (Qwen) | 語数/発話 | 1 内容あたりの語数 (L / G) | Over/局 | Responsiveness-W (L / G) | Rebuttal (L / G) | 名指しの質問に本人の次の発話が応えた (L / G) | 占い師の初回命中 |
|---|---|---|---|---|---|---|---|
| single-batch | 10.1 | 12.0 / 8.5 | 4.4 | 41 / 38 | 7 / 4 | 0.65 / 0.61 | 0.77 |
| single-batch-stepped | 10.2 | 11.8 / 8.3 | 3.7 | 43 / 36 | 7 / 4 | 0.58 / 0.54 | 0.83 |
| single-online | 18.9 | 24.7 / 16.2 | 0.2 | 67 / 68 | 14 / 10 | 0.42 / 0.44 | 0.43 |
| multi-public | 21.6 | 28.2 / 16.9 | 0.1 | 70 / 72 | 18 / 15 | 0.36 / 0.36 | 0.57 |
| multi-private | 21.5 | 27.3 / 14.7 | 0.2 | 75 / 76 | 24 / 20 | 0.34 / 0.37 | 0.23 |
| **multi-private-stepped** | **12.2** | **15.1 / 9.5** | 1.9 | **42 / 38** | **8 / 4** | **0.63 / 0.61** | **0.27** |
| multi-private-stepped-process | 14.8 | 17.6 / 9.9 | 1.3 | 45 / 42 | 11 / 8 | 0.53 / 0.50 | 0.17 |
| multi-public-stepped | 11.7 | 14.1 / 8.9 | 2.4 | 43 / 40 | 7 / 5 | 0.53 / 0.49 | 0.83 |

読み:
- **梯子の形は gemma と同じ**: batch = stepped、密度と長さの最大の段差は stepped → online、分割と情報量の段は小さい。1 内容あたりの語数の比 (multi-private / single-batch) は設定ごとの中央値 L 2.36 / G 1.85 で、single が低いのは 90/90 / 88/90 設定。Qwen は全体に短く、差は gemma (2.6〜2.8) より小さい。
- **全文の目標の移植**: multi-private-stepped は、情報を自席のみに保ったまま、密度 (比の中央値 L 1.28 / G 1.12)、長さ、譲り、Non-repetition、名指しの質問への返答のすべてで single-batch の水準に戻る。占い師の初回命中は偶然の水準 (0.27) のまま。つまり **密度・譲り・質問への返答は生成目標で決まり、情報の整合性は情報アクセスで決まる** という分解が、席ごとの生成の内部でも成り立つ。
- **応答性と反論も目標で決まる**: multi-private-stepped の Responsiveness-W (42 / 38) と Rebuttal (8 / 4) は single-batch と同じ水準に下がる。multi の「直前の発言への受けと反論」は、席ごとに分かれていることではなく、次の 1 行を書く目標から出ている。
- **筋書きの上乗せは小さい**: multi-private-stepped-process は内容の総量がやや増え (L 44 → 47)、発話が少し長く (12 → 15 語)、反論が少し増えるが、密度は目標なしの multi-private (27 / 15) から遠く、目標ありの multi-private-stepped (15 / 10) に近い。
- **全知 + 全文の目標** (multi-public-stepped) は密度で single と区別がつかず (14 / 9)、占い師の命中は 0.83 と全知の水準。single-batch-stepped との差が「1 人が書くか席ごとに書くか」の効果で、どの指標でも小さい。
- 判定者間一致 (38,067 発話): Responsiveness-W κ 0.78、Rebuttal 0.51、content 0 か否か 0.44、padded 0.19。

gemma-31B の stepped 系 3 条件と gemma-4-12B (8 条件 × 90 設定) は実行中。結果が出たらここに追記する。

## 6. 補助分析: 発話前表現からの将来属性の復号可能性 (密度仮説の機構)

隠れ状態は議論の質の評価には使わない。用途は、(i) 「分割自体は表現を変えない」ことの表現レベルの実証、(ii) 密度の差が生成目標の段で生じることの機構の検証である。鍵の比較は single-batch vs single-online: 両者は同じ全情報を持つので、復号可能性の差は情報ではなく「全文を書く目標か次の 1 行を書く目標か」の効果になる (§5.8 の第 2 段に対応)。stepped は batch と同一表現で、分割自体の効果がないことの対照。

- **取得**: 記録済みのプロンプトのトークン id と生成トークン id を同じモデル (bf16) に流し込む再生で、全層 4 層おき + 最終層の表現を保存する。位置は `gen_point` (その行の最初のトークンを予測する位置)。推論エンジンのトークン数との一致を全呼び出しで検査する (パイロット 2,730 / 2,730)。
- **恒等性 (実測)**: single-batch と single-batch-stepped は同じトークン列なので、台本が一致する区間で gen_point の表現が全層で cos 1.000 (バッチ不変モード)。
- **条件間の生の類似度は解釈しない**: batch と online / multi の gen_point は別のトークン上にあり、最終層の cos 0.1〜0.4 は無関係な行でも同じ値になる。
- **復号する属性**: (1) これから書く発話の語数、(2) この発話者が次に Over を言うまでの残り発話数、(3) このラウンドと議論全体の残り発話数、(4) 最終の投票先・採択・処刑、(5) 次の発話者が応答するか反対するか。予想: (1)〜(3) は batch で高く online で低い (目標の効果)、(4) は batch と online で同程度に高く multi-private で低い (情報の効果)。統制は入力の特徴 (位置、ラウンド、ターン、話者、それまでの語数) だけの予測器を置き、それに対する上積みで比べる。標的は条件内で標準化するか順位相関で評価し (batch の語数は 14 語前後に集中するので、分布の単純さだけで復号できてしまう)、同一履歴の再生と層ごとの結果も示す。
- **主張の範囲**: 「全文を書く目標で生成すると各行の長さと役割が生成前に決まっている度合いが高く、それが密度を説明する」に限定し、復号可能性は因果ではないと但し書きする。Dong et al. (2025) はプローブの手法として引く。規模: 各ドメイン 100 局 (設定 30 + 追加 70) を single-batch / single-online / multi-private で追加生成する。
- **第一結果 (主系 630 局、`scripts/probe_hidden.py`)**: 線形 (ridge) プローブ、設定で 5 分割交差検証、入力特徴 (ラウンド、ターン、話者、それまでの発話数と語数) だけの基準線つき。層 0, 16, 32, 48, 60 の最良値:

| 復号する属性 | single-batch | stepped | single-online | multi-public | multi-private |
|---|---|---|---|---|---|
| 次の発話の語数 (R²; 基準線) | **0.69** (0.39) | 0.68 (0.40) | 0.48 (0.31) | 0.59 (0.22) | 0.37 (0.30) |
| この話者がこの期間にあと何回話すか (R²; 基準線) | **0.89** (0.79) | 0.89 (0.79) | 0.87 (0.91) | 0.81 (0.85) | 0.89 (0.93) |
| 局全体の残り発話数 (R²; 基準線) | 0.95 (0.85) | 0.95 (0.88) | 0.97 (0.93) | 0.95 (0.93) | 0.94 (0.93) |
| 次の行が Skip / Over か (正答率; 基準線) | 0.99 (0.83) | 0.99 (0.83) | 0.98 (0.91) | 0.96 (0.88) | 0.98 (0.97) |

  読み: 同じ全情報を持つ batch と online の比較で、次の発話の長さは batch で 0.69、online で 0.48 (基準線からの上積み 0.30 vs 0.16)、multi-private で 0.37 (0.07)。自分があと何回話すかは batch だけが基準線を上回る (+0.10)。batch と stepped は同じ。予想 (1)〜(3) の向きと整合する。注意: multi-public が語数で 0.59 と高めで解釈が要る。勝敗は全知条件で村が必ず勝つため自明で、結末の属性は投票先・採択案に替える。条件ごとに標的の分散が違うので基準線からの上積みで読み、本番では順位相関と条件内標準化、対照課題 (ラベルのシャッフル、未学習モデル)、全 16 層、線形と MLP、条件間の転移、k 行先の復号、設定単位のブートストラップを足す。single-batch の 18 局は台本と記録の行の対応が取れず除外した (要修正)。

## 7. モデル計画

| 役割 | モデル | 理由 |
|---|---|---|
| 生成・主系 (全条件、筋書き、プローブ) | gemma-4-31B-it (dense) | パイロット済み |
| 生成・別系統 (中核 5 条件) | Qwen3.8-27B (dense, Apache 2.0) | 同規模の最新の別系統 |
| 生成・別サイズ (中核 5 条件) | gemma-4-12B-it | 同系列の別サイズ |
| 注釈者 (主) | Llama 3.3 70B Instruct (bf16, tensor parallel 2) | 生成モデルと別系統、手元で配信。temperature 0、バッチ不変なし (パイロットの注釈のみバッチ不変で実行) |
| 注釈者 (副) | gpt-oss-120b (MoE 117B、MXFP4 が公式の唯一の形式) | 生成モデルとも主注釈者とも別系統。temperature 0、バッチ不変なし。反復の自己一致を報告する |

生成モデルと注釈モデルは系統を完全に分ける (Qwen を注釈に使わない)。全モデル temperature 0、思考モード無効 (gpt-oss は推論チャネルを使うが出力は最終回答のみ)。バッチ不変モードは生成モデルに適用し、判定モデルには適用しない (判定は決定的である必要はなく、temperature 0 で十分とする)。chat template、停止列、最大トークン、revision、精度、推論ライブラリの版を header に記録する。「モデル横断」の主張は中核条件の現象の再現に限定し、筋書きとプローブの結論は主系に限る。

## 8. 議論と限界

- **梯子の解釈**: stepped → online の段は「生成目標」「履歴の置き場所」「役割文の 1 文」を、online → multi-public の段は「文脈の分割」と「役割文 (書き手 → 参加者)」をまとめて含む。役割文を両方とも「書き手」に揃えるのは席ごとの生成として不自然なので、この同居は受け入れる。梯子は要因を分離する装置ではなく、段ごとの差を記述して絞り込む装置であり、1 本の経路なので段差の大きさは順序と交互作用に依存しうる。タスクの性質 (「整合的な議論を書く」vs「与えられた情報で意思決定する」) の違いは文面を揃えても解消しない。本研究は性質を別々に記述し、意思決定の質は主張しない。
- **密度の定義**: 「新しい内容の数」は注釈者の判定に依存する。本実験では人手標本 (約 1,200 発話 × 2 名) との一致で守り、content 0 か否かの κ、0 / 1 / 2 の一致を報告する。密度の主張は「1 内容あたりの語数」で行い、水増し (padded、一致 κ 0.57) は記述にとどめる。
- **応答性の定義**: 本研究の Responsiveness-W は Bo et al. の窓 (直前の 1 発話) を「自分の前の発話以降」に広げた補助定義で、先行研究の値とは比べられない。原定義を一次指標として並べ、窓内の発話数で正規化した率も示す。儀礼的な受けも合唱 (提案への同調の連鎖) も 1 と数えうる点は原定義と共通で、注釈者間の不一致はここに集中する。質問への返答率は resp_type に依存しない定義で出し直す。
- **注釈者**: 注釈は Llama 3.3 70B と gpt-oss-120b の 2 者で、content 0 か否かの一致は κ 0.38 にとどまる。人手標本との一致を各注釈者について報告し、人手との一致が高い方を主に据える。content の上限 (2) が長い発話に不利に働きうる点は、上限を外した再注釈と「議論にとって新しい」版の併記で感度分析する。
- **漏洩検出の再現率**: 語の照合は言い換えを拾えない (パイロットの精度 0.25)。LLM 候補 + 人手確認で補い、非候補の無作為標本で再現率を推定する。人狼の利用指標は再現率の問題がない。
- **multi-public**: 診断用条件。人狼ではゲームの前提が変わる。
- **非決定性**: バッチ不変モードで反復は同一だが、batch と stepped は prefill と decode の数値経路の差で近接確率の反転が起きる。「分割は効かない」は「数値解像度以下の差を除いて」と但し書きする。
- **採らない比較**: multi に「短く話せ」と指示する比較 (指示つき条件になりベースラインが崩れる)、2 × 2 の全セル (条件が倍になる)、役割文を両方式で揃える条件 (不自然)。
- **一般性**: 5 人、英語、24 ペルソナと固定議題。各ドメイン 30 設定。

## 9. 結論

生成の粒度の差を 5 つの要因に沿って段階的に絞り込む統制基盤を構築し、先行研究の指標セットを発話単位の率として適用し、Lack of progress を「新しい内容の数」に拡張して密度を導くことで、一括生成が席ごとの生成と同程度の内容を 3 分の 1 の語数で言い、内容が尽きる位置で譲ることを示す設計を提示した。主系の 630 局では、この差の大半は「1 回の呼び出しで議論全体を書くか、次の 1 行を書くか」という生成目標の段で生じ、文脈の分割と情報量の段はその上に小さく足されるだけで、分割自体は効かなかった。情報の整合性は生成方式ではなく情報アクセスで決まり、自席の情報だけを持つ席ごとの生成だけが保つ。反論は席ごとの生成に多く、名指しの質問への返答は一括生成で成立しやすい。生成目標が密度を決める機構を発話前表現からの将来属性の復号可能性で検証し、一括生成の密度を情報と応答性を保ったまま席ごとの生成に移すことが今後の課題である。

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


**v5 → v6 (外部レビューと自己検証、2026-10-28 夜)**: レビューの指摘 (要因の分離の過大主張、発話数の交絡、情報関連指標の混在、応答性の定義、統計、ペルソナの妥当性) を仕分けし、書き方 (梯子は段階的な絞り込み、stepped は negative control、ペルソナは共通集団の統制)、分析 (位置を揃えた比較、語で重みづけた冗長さ)、族 B の 3 分類、統計 (主要比較 5 つ、階層モデル) で対応した。パイロット 8 の読み直しで、single と multi の差が「中身」ではなく「同じ内容を言う語数」にあることを確認し、Becker の Lack of progress を「新しい内容の数」に拡張して密度を導く設計に改めた。応答性には resp_to と応答の種類を加え、質問への返答率を導出した (v5 の「single は呼びかけても答えない」は逆だった)。判定モデルを生成モデルと系統で分け (Llama 3.3 70B / gpt-oss-120b)、設計確認用の別系統の注釈者との向きの一致を確認した。採らなかった提案: multi への「短く話せ」指示、2 × 2 の全セル、Evidence usage / Stance / Distinct-N の継続。

**v6 → v7 (ARR 形式の自己査読への対応、2026-10-28 夜)**: 密度の最大の段差が single の内部 (stepped → online) にあることと主張の帰属がずれていた → 中心の主張を「生成目標」に帰属させ、題名と概要を「全文 vs 1 行ずつ」の対比に変更。「人間の会話らしく読める」の知覚の主張を落とす。梯子の表に役割文の変化を明記。情報の整合性を情報アクセスの効果として書く。Responsiveness-W を補助定義として明示。段ごとの変化の表 (§5.8) を追加。設計確認に使った他系統の注釈者の数値を本文から外す。共通ルール文の経緯を削除。content の上限の感度分析、人手検証の手続き、統計の細部は本実験後に決める。

**v7 → v8 (主系の本実行、2026-10-29)**: gemma-4-31B の 630 局 (90 設定 × 7 条件) を生成し、Llama 3.3 70B と gpt-oss-120b で注釈、hidden states を取得。§5 を本実行の数値に置き換え、応答性の読みを「multi が一貫して高い (+21〜27)、反論 2 倍」に改めた。§6 に線形プローブの第一結果を追加。実行の記録と事故 (削除ミスによる 3 局の再生成、NFS 遅延による重複、注釈出力名のずれ、hidden states のメモリ不足) は docs/main_gemma31b/README.md。

## 付録 F: 第三者レビューへの質問 (v8)

1. 中心の主張を「生成目標 (全文か 1 行ずつか) が密度と譲りを決め、情報アクセスが整合性を決める」に置き、題名を「全文 vs 1 行ずつ」の対比にしたことは、梯子の結果 (§5.8) と整合し、設計から導ける範囲に収まっているか。
2. 「新しい内容の数」(Becker の Lack of progress の 0 / 1 / 2 への拡張) と、そこから導く密度・内容の総量は、独自指標として守れているか (人手検証 約 1,200 発話 × 2 名を予定。Llama vs gpt-oss の content 0 か否かの κ は 0.38)。上限 2 の打ち切りの感度分析と「議論にとって新しい」版の併記は十分な守りか。
3. 位置を揃えた比較 (§5.3) は、切り上げによる生存バイアスの切り分けとして十分か。
4. Responsiveness-W を Bo の指標の補助定義として明示し原定義と並べる扱い、および resp_to から質問への返答率を導く扱い (§5.4) は許容されるか。
5. 族 B の 3 分類 (開示 / 利用 / 先出し) の違反率表は読みやすいか。開示の検出 (語の照合の精度 0.25 + LLM 候補 + 人手全件確認) は十分か。
6. 梯子を「分離」ではなく「段階的な絞り込み」と書き、stepped を negative control とし、段ごとに役割文も変わることを明記した書き方は、要因の同居 (とくに online → multi-public の役割文) の扱いとして十分か。
7. 判定モデル (Llama 3.3 70B bf16 / gpt-oss-120b MXFP4) と生成モデル (gemma-4 / Qwen3.8) を系統で分けた計画は十分か。2 者の content の一致が低いことを、人手標本との一致で補う計画は妥当か。
8. 隠れ状態の分析を密度仮説の機構 (生成前に各行の長さと役割が決まっている度合い) の検証として位置づけた扱いは、過大主張にならないか。
9. 統計 (主要比較 5 つ、設定単位の階層モデル、同等性マージン) は適切か。
10. タイトルと貢献は設計から導ける範囲に収まっているか。
