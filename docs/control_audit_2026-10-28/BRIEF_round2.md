# 検閲 2 (第 2 ラウンド) のブリーフ — 2026-10-28 パイロット 6

第 1 ラウンド (00_SUMMARY.md、01〜06) の指摘に対して修正を入れ、パイロット 6 (log/_pilot6、72 局 + 筋書き 9 本) を回した。
第 2 ラウンドの目的は **「修正が効いているか」と「新たな退行が無いか」の確認**。範囲を広げる提案は不要。

判定の分類 (必ずこの 3 つに分ける): (a) 統制を壊す・実装バグ・記録の欠落 = 修正必須、(b) 報告 (論文の限界・指標) で扱う、(c) 採らない。
条件は凍結 (中核 5 条件 + process / outcome 筋書き)。追加条件の提案は (c) に入れる。

パイロット 6 の実行条件: gemma-4-31B-it、温度 0、`VLLM_BATCH_INVARIANT=1` (2 台: :8000 と :8010)、LEN=20480、UTIL=0.92、`--limit-mm-per-prompt {"image":0,"video":0}`。
single-batch は各 setup 2 回 (反復)。筋書きは厳格な process 規則で再生成 (scenarios/)。setup に option_perm (選択肢の表示順) を追加。
集計: docs/control_audit_2026-10-28/pilot6_inspect.txt (条件別、反復の一致、stepped の占い、ラベル採択、header)。
実装の変更点は 00_SUMMARY.md の「発見と対処」表と docs/DESIGN.md 末尾 (2026-10-28 の項) にある。

第 1 ラウンドの共通ブリーフ (BRIEF.md) の書式と出力先を使うこと。出力ファイル名は `1x_<名前>_round2.md` (例 11_prompts_conditions_round2.md)。150 行以内。
リポジトリのファイルは変更しない。手で確認したい計算は .venv/bin/python で実行してよい (読み取りのみ)。
