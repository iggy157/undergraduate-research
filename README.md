# Single-agent vs multi-agent discussion generation (3 domains)

卒業研究用リポジトリ。1つの LLM が議論全文を書く **single** と、席ごとに独立した LLM が1発話ずつ生成する **multi** を、
同じ設定ファイル・同じルール文・同じログ形式で比較する。ドメインは `aiwolf` / `candidate_selection` / `shared_living`。

- 仕様: `docs/DESIGN.md`。実装契約: `docs/IMPLEMENTATION_NOTES.md`。
- 構成: `common/` (プロトコル・ログ・設定・レンダリング)、`server/` (進行役、3ドメイン共通の Python websocket サーバ)、
  `agent/` (multi の LLM クライアント)、`single/` (single の生成と変換)、`data/` (ペルソナ・役職・ルール・インスタンス)、
  `setups/` (対局ごとの固定設定)、`config/` (モデル・実験)、`scripts/`、`tests/`、`log/`。

## セットアップ

```bash
export PATH="$HOME/.local/bin:$PATH"
uv sync
.venv/bin/python -m pytest -q
```

## 使い方

```bash
.venv/bin/python scripts/make_setups.py                    # setups/<domain>/<setup_id>.json を生成 (決定論的)
.venv/bin/python scripts/verify_prompt_control.py          # single / multi の共通ブロックがバイト一致するか検証
.venv/bin/python scripts/run_multi.py  --setup aiwolf_0001 # サーバ + 5 エージェント (vLLM が必要、--fake で疎通確認)
.venv/bin/python scripts/run_single.py --setup aiwolf_0001 # 1 回の生成 + Markdown → 共通ログ変換 (--dry-run でプロンプトのみ)
.venv/bin/python scripts/convert_logs.py                   # log/ 以下の違反会計
```

モデルは `config/models.yml` の `models.default.model` に設定する (single と multi で同じモデルを使う)。
