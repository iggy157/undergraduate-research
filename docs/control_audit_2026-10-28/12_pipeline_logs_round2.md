# 監査 B (第 2 ラウンド): 実行経路とログ — パイロット 6 (2026-10-28)

対象: log/_pilot6 (72 局、全 2730 llm_call) と現在のコード (server/base/{parse,game}.py、server/{aiwolf,candidate_selection}/logic.py、agent/base/seat.py、agent/aiwolf/__init__.py、common/{logwriter,transcript,llm_meta}.py、common/convert/single_markdown.py)。
pilot6_inspect.txt を読み、足りない検査は自前で実行した (token 単位の batch/stepped 比較、TALK 以外のビュー一致、票・調査の順序、raw_differs の内訳、chat template の照合、tests 201 本)。検査スクリプトは scratchpad の r2/ (div.py, div2.py, order.py, viewcheck.py, misc.py)。

## 結論 (3 行)

1. 第 1 ラウンドの修正は実ログで効いている: stepped の占いは 3/3 有効 (応答 ` Shizue (werewolf)` を名前と認め、翌朝の書き手ビューは `- divine: Benjamin -> Shizue (werewolf)`)、票・調査の問い合わせ (ts 順) と行は server 経路 45 局の全 97 ラウンドで発話順、batch の書き手 27 局も全て発話順、TALK 以外の 408 コール (VOTE 237 / INVESTIGATE 150 / DIVINE 17 / ATTACK 4) もログ由来のビューと一致、raw_differs は trailing_over だけ (stepped 0/262、stepped 応答は 405/405 が先頭スペース)。
2. single-batch の反復は 9/9 で token id・logprob・prompt token の全てが完全一致 (決定的)。batch と stepped の分岐 8 件は token 単位で (i) 同一接頭辞上の近接確率 4 件 (選択 token の logprob 差 0.000 / 0.038 / 0.057 / 0.060) と (ii) サーバの構造決定 4 件 (`Skip.` 正規化 1、`## Round` 前の空行 2、全員 Over 後の空ターン 1) に分かれ、依頼者の分類と一致する。同一 token 上の |Δlogprob| は median 0、p99 0.060、max 0.178 (2040 token) で、prefill / decode の数値経路差は実在し、(i) の 4 件はその範囲内。
3. 新たな退行は無い (error / truncated / timeout / ForceSkip 0、tests 201 passed)。残るのは記録の欠落 (有効な占いの raw が .log に無い、接続先ポートが無い) と潜在的な非対称 (夜 ≥ 1 の stepped 接頭辞に占い結果が無い、server / agent の名前照合の句読点差)。hf_revision の refs/main 解決は本実験に十分 (5 snapshot の template は system+user 経路で同一出力、現サーバの /tokenize は pilot6 の prompt_token_ids と一致)。

## 発見した問題 (深刻度順、分類 (a) 修正必須 / (b) 報告で扱う / (c) 採らない)

| # | 分類 | 項目 | 証拠 | 影響 | 修正案 |
|---|---|---|---|---|---|
| 1 | (a) Minor | 有効な占い・襲撃の行に `raw` が無い。書き手 (stepped) が述べた結果は jsonl の `response` にしか残らず、真値との不一致 (偽の結果を書いた場合) を .log から数えられない。00_SUMMARY #2 の「raw は保存」は jsonl のこと | server/aiwolf/logic.py:97 (valid 分岐に raw 無し) vs :99-100 (invalid は raw あり); log/_pilot6/aiwolf/single-batch-stepped/*/\*.log l.26 の extra は `{action,result,valid}` のみ; jsonl の DIVINE response は 3 局とも ` X (werewolf)` で真値 WEREWOLF と一致 (pilot6 では不一致 0) | 本実験で書き手が `(human)` と書き真値が werewolf の局が出ても、.log だけでは検出できない (蒸留データの正誤にも効く) | valid でも `raw=raw` を付け、括弧内を `stated` に取り、真値と違えば `divine_mismatch` (kind=deviation) を violations に出す |
| 2 | (a) Minor (潜在) | stepped の夜 ≥ 1: DIVINE の仮行が結果無し (`- divine: X -> Y`) のまま同じ夜の ATTACK の接頭辞に入る。batch の書き手は結果まで書く (format_aiwolf.jinja) ので、モデルと無関係に接頭辞が分岐する | agent/aiwolf/__init__.py:77-86 `divine_line(self.name, target, None)`; 結果は翌朝 `on_daily_init` で upsert (:33-37); pilot6 の stepped は 3 局とも rounds=2 で夜 ≥ 1 が無く未発現 (DIVINE 後の次コールは翌朝 TALK で、そこでは結果付き: 確認済み) | 2 日目以降まで続く局で stepped が必ず分岐。single-online の書き手ビューも同形 (batch と同一性の主張は無いが台本の形が違う) | writer_mode (reveal=True、役割表は system にある) では `ctx` の役割から species を付けて upsert する。情報量は変わらない |
| 3 | (b) | hf_revision の解決は refs/main 依存。キャッシュに 5 snapshot (chat_template.jinja は 2 系統 sha 8fa5…/ad0b…、tokenizer_config も 2 系統) があり、「vLLM がどれを読んだか」は起動時の Hub 照会で決まり、refs/main は起動後にも更新され得る (今回 2026-10-21 更新 → 842da37) | common/llm_meta.py:19-34; `_local_snapshot('google/gemma-4-31B-it')` = …/snapshots/842da37; served_info() が現サーバで hf_revision / chat_template_sha1 / config_sha1 を返すことを確認。5 本の template を jinja2 で描画すると system+user (multi 811 token、stepped prompt 部 1554 token) で同一文字列 → 本実験の経路では snapshot 差は token に出ない; 現サーバの `/tokenize`(messages) = pilot6 の prompt_token_ids (811/811) | pilot6 の header は None のまま (修正前に回したため、埋め直せない)。本実験では埋まる。論文の再現情報としては十分 | vLLM を snapshot パス (または `--revision`) で起動し `root` にパスを出すと推測が消える。pilot6 の header は「None、推定 842da37」と注記 |
| 4 | (b) | header に接続先 (base_url / port) とサーバ側 `--timeout` が無い。2 台 (:8000 / :8010) のどちらで回したかが残らない。`model_info.created` は要求時刻 (72 局で 72 値) で識別に使えない | scripts/run_multi.py:99、single/__main__.py:72 (header_extra に base_url 無し); 全 72 header の `created` を集計 | 2 台の起動引数が揃っている限り影響無し。揃っていなければ追えない | header_extra に `base_url` と server `--timeout` を追加 |
| 5 | (b) | 「近接確率の反転」の近接は直接測れていない: `tokens` は選択 token の logprob のみ。分岐 4 件の Δ は batch と stepped が各自選んだ token の logprob 差で、同一分布内の 1 位と 2 位の差ではない | div.py: aiwolf_0002 call 1 (r0 t1) tok 14 ` Maybe` −1.114 vs ` I` −1.152; aiwolf_0003 call 4 tok 3 ` for` −0.775 vs `.` −0.775; cs_0003 call 3 tok 5 ` decade` −0.636 vs ` weather` −0.696; sl_0001 call 17 tok 14 ` takes` −0.801 vs ` on` −0.858。同一 token 上の |Δlp| 2040 件: median 0.000、p90 0.010、p99 0.060、max 0.178、>0.06 が 23 件; call 先頭 token (prefill 直後、n=135) と後続 token で分布に差無し | 「数値解像度以下の反転」は |Δlp| の床 (p99 ≈ 0.06) と Δ ≤ 0.060 の整合で言えるが、間接証拠 | 本実験は `logprobs=2` で記録し 1-2 位差を直接示す (00_SUMMARY #5 の保留を解く)。cs_0002 は 55 コール 711 token 全一致で、恒等性の例として使える |
| 6 | (b) Minor (潜在) | 名前照合の server / agent 非対称: ` Shizue (werewolf).` は server 有効・agent None、`**Shizue** (werewolf)` は server None・agent 有効 | server/base/parse.py:39-43 (strip_edges → 括弧除去) と agent/base/seat.py:63 (括弧除去 → _EDGE); 自前で両関数を実行。pilot6 の DIVINE 応答は 3/3 とも素の形で未発現 | agent 側は仮行のみで記録には効かないが、stepped / online の次コールの接頭辞に `-> none` や空が出得る (#2 と同じ経路) | `match_candidate` を `match_name` に委譲して 1 本にする。test_server_base.py の test_match_name に括弧の例を足す (現状は FakeLLM の ` Name (human)` 経由でしか通らない) |
| 7 | (c) Minor | 文書の残り: DESIGN §13 表 l.475 は依然 `continue_final_message` (IMPLEMENTATION_NOTES l.101 は修正済み); DESIGN l.199「raw_differs は strip で変わった場合と空→Over の場合にだけ true」は旧定義 (現在は端の空白を無視、logwriter.py:63) | docs/DESIGN.md:475, 199 | 再現者の混乱のみ | 2 行を直す |
| 8 | (c) | single の llm_call `ts` は秒精度 (27 件)、multi は ms (第 1 ラウンド #6 の残り) | single/base/run.py | 分析に影響無し | 放置可 |

## 依頼事項への回答

1. **占いの修正**: `match_name` / `match_candidate` とも末尾の `(...)` を剥がす。pilot6 stepped 3 局の divine 行は `valid=true`、target と result は真値 (Shizue / Kenji / Mizuki = WEREWOLF)。書き手の述べた結果は jsonl にだけ残る (#1)。翌朝の書き手ビュー行は結果付きで正しい。他条件の名前照合に括弧付き応答は 0 件 (VOTE / ATTACK の応答に `(` を含むものは stepped DIVINE 3 件のみ) で、変更の影響は stepped の占いに限られる。票・調査・襲撃は全条件で無効 0。
2. **順序**: game.py:252-269 と candidate_selection/logic.py:81-96 は `speaking_order` で逐次に問い合わせ、行も同順。実ログ: 全 server 局の VOTE / INVESTIGATE コールは ts 順が発話順 (97/97 ラウンド)、行も発話順、翌朝の `vote_list` (seat ビューの `### Vote` 節) は行順と一致 (TALK ビューのバイト一致 45 局に含まれる)。batch の書き手は 27 局 (票 27 ラウンド・調査 18 ラウンド) とも発話順で、変換器 (single_markdown.py:479, 763: 書かれた順) と整合。これで pilot5 の cs_0002 / sl_0003 の調査行分岐は消え、cs_0002 は全文一致 (76/76 行、711 token)。
3. **raw_differs**: 定義変更後は trailing_over のみ true (multi-private 26、process 34、public 26、batch-process 10、他 0)。stepped の 405 TALK 応答は全て先頭スペースだが 0 件。jsonl の `response` は生のまま。意味の変化は無し。
4. **反復と分岐**: 上記 #5。依頼者の分類 (近接 4: aiwolf_0002 l.5 / aiwolf_0003 l.8 / cs_0003 l.7 / sl_0001 l.26; 構造 4: aiwolf_0001 `Skip.`、cs_0001 / sl_0003 の `## Round 2` 前の空行、sl_0002 の全員 Over 後 `#### Turn 3`) は token 単位で全て確認した。構造 4 件は分岐直前まで生成 token が全一致 (aiwolf_0001 は 11 コール 210 token、cs_0001 15 コール 228、sl_0002 10 コール 183、sl_0003 15 コール 221)。
5. **header**: pilot6 の 72 header は `vllm_version` あり、`model_root` / `hf_revision` / `chat_template_sha1` / `config_sha1` は None (modelroot が HF id)。修正後の `_local_snapshot` は現マシン (freccia、サーバも localhost) で 842da37 を返し、served_info() も全項目を返す。限界は #3、#4。`option_perm` は議論 42 局の header に記録済み (aiwolf は None で正しい)。

## 確認した範囲 (確認済み)

- 反復: 9 setup × 2 の single-batch で `tokens` の id 列・logprob 列・`prompt_token_ids` が完全一致。
- batch vs stepped: 9 setup で prompt 部のトークン列が batch と同一、分岐前の全コールで prefix = batch の生成 token、分岐点と Δlogprob を列挙 (div.py)。
- ビュー: TALK は pilot6_inspect の 45 局 (再実行せず記載を採用)、TALK 以外は自前で 408 コール (stepped は assistant 末尾のバイト一致、multi / online は user がビューを含む)。
- 順序: order.py (ts 順・行順・翌朝の Vote 節)。validity: 全条件の vote / divine / attack / investigate に無効 0。
- 環境: HF キャッシュの 5 snapshot の sha1、jinja2 描画の同一性、現サーバの /tokenize との一致、served_info() の実行。tests: `pytest -p no:cacheprovider tests/` 201 passed (46.9 s)。

## 確認していない範囲 (推測を含む)

- 「vLLM が 842da37 を読んだ」は refs/main と更新日時からの推測。template が同一出力なので本実験の token には影響しないが、重みの差 (config.json は 5 本とも同 sha) は確認していない (safetensors の sha は未計算)。
- #5 の「数値経路の差」は |Δlogprob| の分布から推論したもので、同一入力を同一経路 (batch を 2 回) で回した反復が一致することと合わせた間接証拠。1-2 位差は未記録のため測れない。
- #2 は code reading による (夜 ≥ 1 の stepped 局は pilot6 に無い)。筋書き・hidden states・評価は監査 A / C / D の範囲。
