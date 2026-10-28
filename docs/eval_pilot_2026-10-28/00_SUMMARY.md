# 評価設計の試運転 (パイロット 6、2026-10-28)

docs/paper_draft.md v4 §4 の評価設計を、パイロット 6 (log/_pilot6、72 局) に実際に適用した記録。数値と読みは草稿 §5 にある。

## 中身

| ファイル | 内容 | 生成 |
|---|---|---|
| metrics_summary.md / metrics_games.csv | 自動指標 (族 A: 語数、張りつき、Non-repetition、Skip/Over、全員パス; 族 B: 公開前の選択肢名、非公開情報の候補、人狼の占い師初回命中・Day 1 処刑) | `scripts/eval_metrics.py` (vllm-server の venv、MiniLM は CPU) |
| metrics_candidates.jsonl | 族 B の候補 (全件を人手確認、下記) | 同上 |
| JUDGE_INSTRUCTIONS.md | 対比較の指示文 (人手と LLM 判定に共通) | 手書き |
| judge_pairs.json / judge_assignments.json | 45 対 (9 設定 × C1〜C5) と、ラテン方格による 9 組の割当 (1 組 = 比較 5 種 × 別設定) | `scripts/render_judge_pairs.py` |
| judge_judgements.jsonl / judge_summary.md | Claude 系 2 モデル (Opus / Sonnet) × 2 順序 × 45 対 = 180 判定と集計 | Claude Code のサブエージェント 36 体 + `scripts/judge_summary.py` |

## 候補の人手確認 (族 B)

- 語の照合による非公開情報の候補 10 件: 本物 1 件 (shared_living_0001 single-batch-process R2T3 Misaki「fixed headcount の預かり金、抜けた人の分は残りが払う」。調べた Mio は R2T1 で「キャンセル条件が厳しい」としか言っていない)。偽陽性 9 件: 一般語の一致 (setting / takes、clear / window、actually / sleeping) 7 件、調べた本人が前のラウンドで言い換えて共有済み (candidate_selection_0003 George ← Benjamin「Mechanical costs are climbing sharply」) 2 件 (反復 2 局で同文)。
- 語の照合が拾えなかった本物 1 件: candidate_selection_0001 single-batch R3T2 Kenji「the repository is fast now」(Toshio だけが調べ、R2 では別のカードの内容しか話していない)。予備評価の判定者の指摘を人手で確認。
- 予備評価の判定者の誤り 2 件 (本物でない): 同設定の single-batch-process の Kenji (自分のカードの内容)、shared_living_0002 stepped の Shunichi (自分の 2 枚の内容、判定者は別カードと取り違え)。
- 公開前の選択肢名 (正式名の一致) 1 件: shared_living_0002 single-online R2T2 Asuka「a rotating location」(選択肢 Rotating Location)。語の一部の一致 (`lodge`、`drought`、`address`) は本文の指標にしない。
- 人狼: 全役職を知る条件 (single 3 条件、multi-public) は占い師の初回占いが 9/9 で人狼、multi-private は 0/3。

## 判定者の出力の注意

- Sonnet の 5 組は pair 名から比較の接尾辞 (`__C1`) を落として書いた。`judge_summary.py` が割当表から復元する (設定名は組の中で一意)。
- 1 件が Tie (Opus)。順序を入れ替えて勝者が反転した対は各判定者 8/45。

## 次

- 人手評価 (225 対 × 2 名) は本実験の台本で行う。指示文は JUDGE_INSTRUCTIONS.md をそのまま使う。
- 本実験では非公開情報の候補生成に LLM の問い (カードの所有表つき) を加え、全候補を人手確認して精度を報告する。

## 第 2 ラウンド (2026-10-28、表示と問いを変更)

ユーザの指摘: Skip / Over は人間の議論には存在しない記号で、判定者の読解に委ねるべきでない。ジャッジには発話だけを見せ、Skip / Over はルールで数えるだけにする。問いは「タスクの解決に向かって人間らしく議論できている方」にする (雑談などの具体的な観点は書かない)。

変更: `scripts/render_judge_pairs.py --view judge` (既定)。Day / Round 見出し + 発話 + 票 + 結果のみ。ターン見出し、Skip / Over、夜の行動、調査の行を落とす。指示文 round2/JUDGE_INSTRUCTIONS.md (Skip / Over の説明なし、問いは「real people discussing this matter and working their way to the decision they have to make」)。同じ 45 対、同じ 2 判定者 × 2 順序。

| 比較 | 第 1 条件 | round 1 (全記録 + 譲りの観点) | round 2 (発話のみ + 決定に向かう議論) | round 2 Opus / Sonnet |
|---|---|---|---|---|
| C1 | single-batch vs multi-private | 0.69 | **0.39** | 0.61 / 0.17 |
| C2 | single-batch vs single-online | 0.78 | **0.44** | 0.44 / 0.44 |
| C3 | single-online vs multi-public | 0.83 | 0.89 | 0.94 / 0.83 |
| C4 | multi-public vs multi-private | 0.15 | 0.25 | 0.28 / 0.22 |
| C5 | single-batch vs single-batch-process | 0.44 | **0.19** | 0.11 / 0.28 |

検証値: 判定者間一致 0.69 → 0.78。順序で反転 8/45 → 11/45 (Opus)、17/45 (Sonnet)。先に示した方の勝率 0.47 / 0.41 → 0.40 / 0.31 (後に示した方が勝ちやすい位置バイアスが出た)。長い方が勝った率 0.42 → 0.56 (Sonnet 0.61)。

読み: single を支えていた手がかり (譲る、ターンを埋めない) が表示から消え、問いが「決定に向かう議論」になったことで、判定者は multi の「段階的な積み上げ」「摩擦と譲歩」「人物の一貫性」を人間らしいと読み、single の短さを「薄い」「数行で決まる」と読んだ (理由の抜粋は round2/judge_judgements.jsonl)。これは round 1 の長さバイアスと同じ方向の読みが問いの枠で戻ってきたことを意味し、人間らしさの判定は**表示と問いの立て方に強く依存する**。C3 (online > public) と C4 (private > public) は両ラウンドで安定。筋書き (process) は round 2 で明確に有利 (0.81)。

設計への含意: (1) 人手評価の表示と問いは本実験前に 1 つに固定し、両方の版を論文に載せない (事後選択に見える)。(2) 族 A の主張は人手の対比較だけに頼らず、自動指標 (語数、張りつき、反復、Skip / Over) を同じ重みで置く。(3) 位置バイアスが出たので、人手でも順序の無作為化と順序効果の報告が必須。

## 第 3 ラウンド (2026-10-28、基準を具体化; 参考)

表示はラウンド 2 と同じ (発話のみ)。問いを「口頭の会話のように読めるか: 引き締まり、応答的で、余分がないか」にし、見る点を 4 つ (口頭のテンポ、冗長さなし、言うべきことに見合う長さ、応答して前に進む) 明記。「議論が多い・詳しいことは証拠にしない、同じことを少ない語で言える方が上。ただし票やスローガンだけになった記録も会話ではない」。round3/JUDGE_INSTRUCTIONS.md。

| 比較 | 第 1 条件 | round 1 | round 2 | round 3 |
|---|---|---|---|---|
| C1 | single-batch vs multi-private | 0.69 | 0.39 | **1.00** (36/36) |
| C2 | single-batch vs single-online | 0.78 | 0.44 | **1.00** |
| C3 | single-online vs multi-public | 0.83 | 0.89 | **1.00** |
| C4 | multi-public vs multi-private | 0.15 | 0.25 | 0.43 |
| C5 | single-batch vs single-batch-process | 0.44 | 0.19 | 0.78 |

検証値: 判定者間一致 0.90、順序で反転 4/45 と 3/45、位置の偏りなし (0.48 / 0.54)、**長い方が勝った率 0.13**。

読み: 基準を具体化すると判定は安定し (一致 0.90、反転 1 割未満)、Sonnet でも single を選ぶ。ただし勝者は 87% で短い方であり、判定は実質「語数・水増し・反復」の検出器になっている。つまり自動指標 (語数、張りつき率、Non-repetition) と同じものを測っており、独立した「質」の判定ではない。筋書き条件 (process) は発話数が増える (29 → 35) ぶん負ける。この形で人手評価を行うなら、論文では「読者が自動指標の差を知覚できることの確認」と位置づけ、「優劣」や「人間らしさ」の判定とは呼ばない。

ユーザの懸念 (生成側に口頭の会話らしさを指示していないのに評価で測るのは恣意的では): 両方式に同じルールを与えて何も指示していないので、差は方式の性質 (傾向) として記述できるが、優劣の主張にはならない。優劣や「人間らしさ」を言うには外部の基準 (人間の議論コーパスの発話長・反復・定型句の統計との距離) に接続する必要がある。
