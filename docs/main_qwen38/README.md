# 別系統の本実行 (Qwen3.8-27B、2026-10-29 08:11 開始)

## 配信の設定 (gemma との違い)

- Qwen3.8-27B は線形注意 (Gated DeltaNet) と通常注意のハイブリッド (`full_attention_interval: 4`) で、vLLM のバッチ不変モード (`VLLM_BATCH_INVARIANT=1`) が非対応 (`batch_invariant mode is not supported for GDN_ATTN`)。
- 代わりに **バッチを 1 件に固定** (`--max-num-seqs 1`) し、**接頭辞キャッシュを切る** (`--no-enable-prefix-caching`) ことで、同じ入力が常に同じ計算経路を通るようにした (He et al. 2025 が特定した非決定性の原因 = バッチの組成を固定する素朴な統制)。思考モードはサーバの `--default-chat-template-kwargs {"enable_thinking":false}` で無効化。temperature 0、LEN 20480、1 台 1 局ずつ 6 台。
- **決定性の検証 (事前)**: 3 設定 (aiwolf_0001, candidate_selection_0001, shared_living_0001) × {single-batch, multi-private} を 2 回ずつ生成し、6/6 で全行一致 (`log/_det_qwen_1`, `_2`)。本実行後に single-batch を全 90 設定で 2 回目を生成し、一致率を記録する (`log/main_qwen38_rep`)。
- hidden states の再構成の検査 (`scripts/extract_hidden.py --check-only`) は Qwen の記録 6 局で失敗 0。

## 実行

- 中核 5 条件 × 90 設定 = 450 局 → `log/main_qwen38/`。process 条件は主系のみ。注釈は Llama 3.3 70B と gpt-oss-120b (temperature 0、バッチ不変なし)、hidden states は `hidden/main_qwen38/` (層 every4 + 最終層)。

## 決定性の検証 (本実行後、2026-10-29 10:40)

- single-batch を全 90 設定で 2 回生成 (`log/main_qwen38` と `log/main_qwen38_rep`、どちらも 6 台のうち空いたサーバに割り当て)。**同じサーバインスタンスで生成した 23 設定は 23/23 で全行一致、別インスタンスで生成した 67 設定は 67/67 で不一致** (分岐は 1 行目〜32 行目)。
- 原因: 線形注意 (Gated DeltaNet) の Triton カーネルが `@triton.autotune` (12 構成、キー H/K/V/BT) でプロセスごとにベンチマークして構成を選ぶため、インスタンスが違うとブロックサイズや warp 数が変わり、浮動小数点の加算順序が変わる。バッチ 1 件固定・接頭辞キャッシュなしで「同じインスタンス内の決定性」は成り立つが、「インスタンス間の同一性」は成り立たない。事前検証 (6/6 一致) は同じインスタンスで 2 回流していたので、この差を検出できなかった。
- 含意: 中核 5 条件の結果 (密度など) は各局が「そのインスタンスの決定的な出力」であり、条件間の比較に偏りは生じない (どの条件も同じ混在)。ただし batch = stepped の negative control は、同じ設定の 2 条件が別インスタンスで生成されると丸めの差で分岐するので、**同じインスタンスで対にして**評価する必要がある。`scripts/run_queue.py --pin-by-setup` (設定ごとに同じサーバへ割り当て) を追加した。
- 対処の候補: (1) Triton の自動チューニング結果をプロセス間で共有する (キャッシュ) ことでインスタンスを同一化し、全 450 局を再生成する。(2) 再生成せず、negative control だけ同一インスタンスの対 (single-batch + stepped、90 設定) を別途生成する。
