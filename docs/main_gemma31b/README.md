# 本実行 (gemma-4-31B-it、2026-10-28 20:49 〜 2026-10-29 03:00)

## 生成

- 3 ドメイン × 30 設定 × 7 条件 = 630 局。`log/main_gemma31b/` (git 管理外)。設定 0001〜0003 の 63 局はパイロット 8 の記録をそのまま使い (生成は決定的)、設定 0004〜0030 の 567 局を `scripts/run_queue.py` で生成 (gemma-4-31B-it を 6 台、temperature 0、`VLLM_BATCH_INVARIANT=1`、1 台 4 局並列)。開始時のコードは git tag `main-run-gemma31b-start`。
- process 筋書き 90 本 (`scenarios/`): 設定 0004〜0030 の 81 本を本実行中に生成 (gemma-4-31B、greedy、試行 4〜8 回)。人狼の 3 本 (0016, 0022, 0028) は「ターンを 0 から数える」癖で検証に落ち、0022 は試行 8 回で通り、0016 と 0028 は機械的な修復 (0 始まりのターン番号を 1 始まりに付け直す。`common/scenario.py` の `repair_plan`、ファイルに `repairs` として記録) を加えて通した。
- 事故: 22:20 に重複ディレクトリの掃除で走行中の single-batch-process 3 局 (aiwolf_0013, aiwolf_0019, candidate_selection_0006) のディレクトリを消してしまい、再生成した (決定的なので同じ記録になる)。NFS のディレクトリキャッシュ遅延で完了判定を誤り stepped 8 局を重複生成しかけたが、重複分は削除し、完了判定をキャッシュ更新つきに直した。
- 全 630 局に result 行があることを確認。

## 注釈 (発話単位、指示文 v2)

- 判定者: Llama 3.3 70B Instruct (bf16, TP=2, temperature 0, バッチ不変なし) と gpt-oss-120b (MXFP4, temperature 0, バッチ不変なし)。`scripts/annotate_llm.py`、描画は `scripts/render_annotation.py --stable-names --only-complete`。
- 事故: 出力ファイル名が局一覧の位置番号だったため、途中で 136 局が加わった時点で番号がずれ、98 局が未注釈・98 局が重複になった。出力名を局名ベースに直し、未注釈の局を埋めた。
- 結果: annotation/ (summary.md, qa_summary.md, out/, raw/, games.json, games/)。

## hidden states

- `hidden/main_gemma31b/<game_id>.npz` + `.index.json` (git 管理外、8.4 GB)。`scripts/extract_hidden.py`、記録済みの prompt_token_ids と生成トークン id の再生、gemma-4-31B-it (snapshot 842da379)、bf16、層 0,4,8,…,60 (16 層)、位置は label / prompt (gen_point つき)。
- 630 局、検査の失敗 0、飛ばした呼び出し 0。位置数: single-batch 5,185 (gen_point 5,185)、stepped 5,140、single-online 10,900 (5,450)、multi-public 10,632 (5,316)、multi-private 11,702 (5,851)、single-batch-process 5,540、multi-private-process 11,644 (5,822)。
- 事故: 2 万トークン級の局で全位置の logits (語彙 26 万) を作って GPU メモリ不足になり 2 バッチが落ちた。最終位置の logits だけ計算するように直して再試行した。

## 自動指標

- metrics_summary.md / metrics_games.csv / leak_candidates.jsonl (`scripts/eval_metrics.py`、630 局)。開示候補 212 件は未確認 (人手確認は別途)。

## 結果の要点 (630 局、注釈は Llama (L) / gpt-oss (G)、2026-10-29 03:05 集計)

| 項目 (single-batch vs multi-private) | L | G |
|---|---|---|
| 語数/局 | 520 vs 1861 | 同左 |
| 新しい内容の数/局 | 34.4 vs 46.6 | 49.8 vs 73.1 |
| 1 内容あたりの語数 | 15.1 vs 40.0 | 10.4 vs 25.5 |
| 設定ごとの比 (multi / single) | 中央値 2.76、90/90 設定で single が低い | 中央値 2.61、90/90 |
| 内容の総量の比 (multi / single) | 中央値 1.38 (77/90 設定で multi が多い) | 1.47 (75/90) |
| 進展なし発話 (content 0) の率 / 語の割合 | 15.7% / 10.6% vs 20.9% / 19.0% | 4.0% / 2.0% vs 9.6% / 8.6% |
| 水増し発話 | 2.3% vs 8.9% | 6.3% vs 12.8% |
| Responsiveness-W | 52.0 vs 72.9 | 46.7 vs 73.6 |
| Rebuttal | 9.0 vs 19.2 | 7.9 vs 17.5 |
| 名指しの質問に本人が答えた率 | 0.23 vs 0.01 | 0.34 vs 0.05 |
| 占い師の初回命中 / Day 1 の人狼処刑 (自動) | 1.00 / 1.00 vs 0.27 / 0.40 | 同左 |

- 梯子 (L、1 内容あたりの語数): batch 15.1 → stepped 14.6 → online 31.1 → multi-public 40.4 → multi-private 40.0。最大の段差は stepped → online で、パイロットと同じ。
- 位置を揃えた発話あたりの新しい内容 (L+G 合算): R1 T1 1.40 vs 1.32、R1 T2 1.14 vs 1.12、R2 T1 1.63 vs 1.48、R3 T1 1.35 vs 1.28、R3 T4 0.57 vs 0.82。同じ位置では同程度、終盤のターンで multi がやや多い。
- 応答性は本実行では multi が 20 ポイント高く (パイロットの 9〜12 より大きい)、ドメインでは候補者選定 44 vs 69、共同生活 46 vs 73、人狼 67 vs 77 (L)。反論も multi が 2 倍。
- 判定者間一致 (29,016 発話): Responsiveness-W κ 0.62、Rebuttal 0.60、content 0 か否か 0.33、padded 0.23、content 0/1/2 の完全一致 0.50。gpt-oss は内容を多く数える (発話あたり 1.35 vs 0.88)。
- gpt-oss の 2 局 (shared_living_0014 single-batch、shared_living_0018 multi-private-process) で数発話の注釈が欠けている (再実行は未)。
- 確証的な検定 (27 設定のみ) と、content の上限の感度分析、人手検証、開示候補 212 件の確認は未実施。
