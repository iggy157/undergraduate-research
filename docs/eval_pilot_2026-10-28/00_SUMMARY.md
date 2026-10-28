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
