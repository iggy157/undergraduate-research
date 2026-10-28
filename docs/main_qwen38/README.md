# 別系統の本実行 (Qwen3.8-27B、2026-10-29 08:11 開始)

## 配信の設定 (gemma との違い)

- Qwen3.8-27B は線形注意 (Gated DeltaNet) と通常注意のハイブリッド (`full_attention_interval: 4`) で、vLLM のバッチ不変モード (`VLLM_BATCH_INVARIANT=1`) が非対応 (`batch_invariant mode is not supported for GDN_ATTN`)。
- 代わりに **バッチを 1 件に固定** (`--max-num-seqs 1`) し、**接頭辞キャッシュを切る** (`--no-enable-prefix-caching`) ことで、同じ入力が常に同じ計算経路を通るようにした (He et al. 2025 が特定した非決定性の原因 = バッチの組成を固定する素朴な統制)。思考モードはサーバの `--default-chat-template-kwargs {"enable_thinking":false}` で無効化。temperature 0、LEN 20480、1 台 1 局ずつ 6 台。
- **決定性の検証 (事前)**: 3 設定 (aiwolf_0001, candidate_selection_0001, shared_living_0001) × {single-batch, multi-private} を 2 回ずつ生成し、6/6 で全行一致 (`log/_det_qwen_1`, `_2`)。本実行後に single-batch を全 90 設定で 2 回目を生成し、一致率を記録する (`log/main_qwen38_rep`)。
- hidden states の再構成の検査 (`scripts/extract_hidden.py --check-only`) は Qwen の記録 6 局で失敗 0。

## 実行

- 中核 5 条件 × 90 設定 = 450 局 → `log/main_qwen38/`。process 条件は主系のみ。注釈は Llama 3.3 70B と gpt-oss-120b (temperature 0、バッチ不変なし)、hidden states は `hidden/main_qwen38/` (層 every4 + 最終層)。
