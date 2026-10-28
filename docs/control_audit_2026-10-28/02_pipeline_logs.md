# 監査 B: 実行経路とログ (server / agent / single の手続きと記録) — 2026-10-28

対象: server/base/{game,parse}.py, server/{aiwolf,candidate_selection}/logic.py, agent/base/{seat,llm,discussion,registry}.py, agent/aiwolf, agent/__main__.py,
common/{transcript,normalize,violations,logwriter}.py, common/convert/single_markdown.py, single/base/{run,llm}.py, scripts/run_multi.py,
docs/IMPLEMENTATION_NOTES.md, DESIGN §3/§4.6/§4.7/§7.4/§8/§13/§14、log/_pilot5 (63 局) の生ログ。検査スクリプトは再実行し、自前の検査 (トークン列・VOTE/ACTION ビュー) を足した。

## 結論 (3 行)

1. 手続き・正規化・記録は 5 条件でほぼ対称で、全 39 局 (server 経路) の TALK / VOTE / ACTION の user は共通ログから復元したビューとバイト一致した。
2. ただし **single-batch-stepped は aiwolf で占い (DIVINE) が 4/4 件無効** (応答 " X (werewolf)" をサーバが名前と認めない) で、条件として壊れている (Critical)。
3. batch と stepped の同一区間は 4〜21 行 (全 64〜97 行) に留まり、原因の半分はサーバ側の決定 (票・調査行の**席順** vs 書き手の**発言順**、Skip. の正規化、全員 Over 後の空ターン) で、数値非決定性だけではない。論文の「同じトークン列」主張は限定が要る (Major)。

## 発見した問題 (深刻度順)

| # | 深刻度 | 項目 | 証拠 | 影響 | 修正案 |
|---|---|---|---|---|---|
| 1 | Critical | stepped の DIVINE 応答がサーバで無効になる。batch の出力形式 (`- divine: Seer -> Target (human\|werewolf)`) をそのまま続け書くので応答は ` Shizue (werewolf)`; `match_name` は括弧付きを拒否、agent 側 `match_candidate` も不一致で書き手ビューは `-> none` | single/prompts/format_aiwolf.jinja l.11; server/base/parse.py:35-43; agent/base/seat.py:60-72, 286-290; log/_pilot5/aiwolf/single-batch-stepped/*/\*.log の divine 行: 4/4 が `valid=false, raw=' X (werewolf)'` (他条件は 0 件失敗) | stepped の aiwolf は占い師が一度も占えない (他 4 条件は占える) = 設計外の条件差。Day 0 の Action 節で batch から必ず分岐する。書き手が自称した結果 (aiwolf_0003 r1 `Mizuki (human)` は偽) も記録されない | parse.match_name (と seat.match_candidate) で末尾の `\((human\|werewolf)\)` を剥がして照合し、書かれた結果を `raw` に残して真値と違えば `divine_mismatch` 相当で記録。または stepped の DIVINE の stop に ` (` を足す。修正後に aiwolf 3 局を再実行 |
| 2 | Major | 票・調査行の順序: batch の書き手は**発言順** (3/3 discussion, aiwolf_0001 で確認)、サーバは**席順** (`living_seats()` / `g.seats()`) で問い合わせ・記録。format spec は順序を指定しない | server/base/game.py:253-258; server/candidate_selection/logic.py:229-233; single/prompts/format_discussion.jinja l.12 "(one line per participant)"; batch transcript candidate_selection_0002 l.17-21, 75-79 は Servas, Asuka, Minako, Mio, Toshio (発言順) で席順は Minako, Toshio, Asuka, Servas, Mio; 再実行 inspect: cs_0002 / sl_0003 の分岐点が調査行 (l.17) | stepped は Vote/Action 節で batch と必ず分岐 (DESIGN §14 l.497 は把握済みだが「設計した差」ではない)。online / multi のビューと batch の台本でも票・調査行の並びが系統的に違う (蒸留データ・hidden states の対応付けにも効く) | サーバの VOTE / INVESTIGATE を `speaking_order` で問い合わせて記録し、DAILY_INITIALIZE の `vote_list` も同順にする (両方式対称)。代替: format spec に "in seat order" を明記 (書き手の負担増) |
| 3 | Major | batch と stepped の同一性の実態: 同一行数 aiwolf 11/12/8, cs 4/16/4, sl 21/15/16 (全 64〜97 行)。原因 (a) 近接確率の反転: cs_0001 は**第 1 発話**の token 21 で `\n` (lp −0.6487) vs ` I` (−0.6483); aiwolf_0001 は 7 発話目 (−0.665 vs −0.728); (b) サーバ正規化 `Skip.`→`Skip` (aiwolf_0002 l.13); (c) サーバの構造決定: 全員 Over 後の空ターンを置かない (sl_0001 l.22, sl_0002 l.16: batch は `#### Turn 4` + Skip 行を書く)、#2 の順序、#1 の占い失敗 | 自前検査: prompt トークン列は 9/9 setup で batch と同一 (例 1554=1554)、分岐前の全 call で接頭辞トークン列 = batch の生成トークン列 (再トークン化の境界ずれなし); inspect 再実行の "batch vs stepped" 行 | paper_draft l.84/168 「接頭辞のトークン列は同一で…同じ発話」「表現が一致」は分岐前区間にしか成り立たない。stepped は「分割自体は効かない」の実証ではなく、分割 + サーバの構造決定 + 数値非決定性の合算になる | 主張を「同一接頭辞の区間では一致 (恒等性の検査)、以降は条件として別物」に限定。(b)(c) は #1 #2 の修正で縮む。空ターンは batch 側の違反 (format spec "has no line in the later turns" を書き手が守らない、`pass_after_over` で記録済み) なので、分岐率を条件の指標として報告する |
| 4 | Major | `raw_differs` が stepped で全 talk true (272/272)。続き書きの応答の先頭スペースをサーバが strip するため。batch 0, online 0, multi 17〜24 (trailing_over 由来) | common/logwriter.py:63; agent/base/llm.py:172 (`choice.text` そのまま); game.py:235; 応答先頭スペース 412/413 TALK call; DESIGN §3.1 l.98 の定義と不一致 | `raw_differs` を指標や除外条件に使うと条件札と完全相関 | logwriter で `raw.strip() != text` にする (jsonl の response は生のまま残る)。DESIGN §3.1 を更新 |
| 5 | Minor | 文書と実装の不一致: stepped は `continue_final_message` (chat) ではなく `/v1/completions` に token id を渡している。§14 と paper l.211 は正しい | docs/IMPLEMENTATION_NOTES.md l.101; DESIGN §13 表 l.473; 実装 agent/base/llm.py:144-180 | 再現者が別 API で再実装する | 2 箇所を §14 の記述に合わせる |
| 6 | Minor | 再現情報の欠落: header に vLLM 版・dtype/GPU・chat template (tokenizer_config) の sha1・サーバ起動引数・server `--timeout` (660 s) が無い (`model_info` は id/root/max_model_len のみ)。§14 が「vLLM greedy は非決定的」と認める以上、環境の記録が要る。single の llm_call `ts` は秒精度 (multi は ms)、`model` は config 名 (multi は応答の `r.model`; 今回は同値) | scripts/run_multi.py:357-367, 416; single/base/run.py:95-98; agent/base/seat.py:305 | 第三者が同じ分岐率を再現できるか判定できない | run_multi / single で `GET /version` (vLLM) と tokenizer_config の sha1、`--timeout` を header_extra に入れる |
| 7 | Minor | 変換器の構造項目 (`_Converter.v`, kind 未指定) と `llm_error` に `kind` が無い。消費側 (inspect, convert_logs) は violation 扱いに既定化 | common/convert/single_markdown.py:181-186; single/base/run.py:146 | pilot5 では該当 0 件。発生時に集計表の列が揺れる | `v()` の既定 kind を `"violation"` に |
| 8 | Minor (潜在) | 変換器とサーバの微差: 発話内の `- item` 箇条書き行は multi では発話の一部 (stop は `\n- **` のみ) だが変換器は `unknown_name` / `unrecognised line` で捨てる; `\n## ` は multi で切断、変換器は見出し | single_markdown.py:357-369; agent/base/llm.py:39 | pilot5 の改行入り発話は全条件 0 件で未発現 | 変換器で `- ` 始まりの非ラベル行も直前発話に連結する |
| 9 | Minor | エラー・タイムアウトの非対称 (方式の必然): multi/online/stepped はコール単位で forced Skip / 無効票 / 行動なしに退化し進行 (`error` と `raw="ForceSkip"` が残る)、server timeout 660 s > agent 600 s; single-batch はエラーで全損 (`text=""` → `parse_error` + `llm_error`, outcome `{}`) で header.outcome の形も違う (multi は `winner: NONE, reason`) | agent/base/seat.py:321-324; game.py:243-246; single/base/run.py:145-146; run_multi.py:430 | pilot5 は error / timeout / truncation 0 件。分析時の除外基準が未定 (前回 C3 と同じ) | 「error / truncated / forced を含む局は除外」を DESIGN §11 に明記 |
| 10 | 情報 | 渡された pilot5_inspect.txt は view check が aiwolf の multi-private 6 局で切れ、batch vs stepped 節が無かった。再実行で全 39 局・全 TALK 一致と分岐表を得た (現在のファイルは更新済み) | docs/control_audit_2026-10-28/pilot5_inspect.txt | — | 実行ログは stderr も保存する |

## 判定の観点への回答

- **統制**: 手続き (要求列・正規化・記録) は 5 条件で同じコードを通る。設計外の差は #1 (stepped の占い失敗)、#2 (行の順序)、#4 (raw_differs)。multi-private に対する席順逐次化と `executed_agent` の影響は無し (下記確認)。
- **正しさ**: 正規化は両方式とも `common.normalize.normalize_talk` 1 本 (server/base/parse.py:26-28; single_markdown.py:438) で、pass 行の `raw` / `norm` の付け方も同形。共通違反コードは両方とも `find_violations(rows)` + `find_truncations` (単体はさらに構造コードを `merge_violations` で合流)。ログは入出力を忠実に残す (messages / response 生、tokens、prompt_token_ids == usage.prompt_tokens 2688/2688)。文書の不一致は #5。
- **査読耐性**: Critical #1 は「stepped 条件が人狼で機能していない」と一目で指摘される。#3 は「stepped ≒ batch」の主張の根拠が弱い (同一区間が短い) と指摘される。#2 は蒸留・hidden states の対応付けで突かれる。
- **再現性**: setup_sha1 / rules_hash / models_yml_sha1 / sampling / stop 列 / token id は揃う。欠けるのは #6 の環境情報。

## 確認した範囲 (確認済み)

- **(1) stepped の呼び出し**: messages = [system(batch), user(batch), assistant = 書き手ビュー + 札]; prompt = `/tokenize`(messages[:2], add_generation_prompt) + `/tokenize`(prefix, add_special_tokens=False) を `/v1/completions` へ。prompt 部は batch の prompt_token_ids と 9/9 setup で同一; 分岐前の全 call で prefix のトークン列 = batch の生成トークン列 (境界ずれなし)。stop: TALK = `["\n- **","\n####","\n###","\n##"]`、VOTE/ACTION = `["\n"]`。応答は先頭スペース付き (#4)。`prompt_ids` / `prefix_ids` は長さ (id 列ではない) で、`prompt_token_ids` が連結列。
- **(2) 正規化の同一性**: 上記。対応表 — 共通 10 コード (over_cap, name_label, multi_utt, pass_punct, trailing_over, speak_for_others, format_noise, early_reveal(_partial), truncated) は同一関数; 正規化ノート (pass_punct / format_noise:wrap / name_label:self / trailing_over / multi_utt) は normalize_talk が両方に付ける; 単体のみの構造コードは DESIGN §8 どおり。
- **(3) 席順逐次 VOTE / INVESTIGATE と `executed_agent`**: 票はパケットに載らないので逐次化で内容は変わらない; `executed_agent` は `writer_mode` でのみ使用 (seat.py:270)。実ログで VOTE / ACTION の user が席ビューと一致: multi-private 83/83, multi-private-process 78/78, multi-public 78/78; 書き手ビュー: stepped 83/83, online 78/78。TALK は 39 局全 call 一致 (inspect 再実行)。
- **(4) ログの項目**: llm_call に ts (UTC)、latency_ms、usage、model、finish_reason、error、truncated、stop、tokens (id + logprob)、prompt_token_ids; header に condition / axes / pipeline / sampling / model_info / models_yml_sha1 / scenario; violations に kind (violation / normalized / deviation)。欠落は #6、#7。
- **(5) over_cap**: 両方式とも語数を切り詰めず、`count_words(text)` で同じ判定 (server は game.py:233-235、単体は write_game → find_violations)。multi 平均 32.5 語 / batch 13.2 語の差は生成の差で手続きの差ではない (評価・監査 A の範囲)。
- **(6) タイムアウト・エラー**: #9。pilot5 では発生なし (err 0, trunc 0, timeout 0, forced 0)。
- 時間: multi TALK 中央値 2.0 s、online 1.4 s、stepped 0.76 s、batch 53 s/局; 局の壁時計 multi 93〜138 s、batch 42〜60 s。

## 確認していない範囲 (推測を含む)

- `tests/` は実行していない (test_conditions.py が stepped / writer のバイト一致を FakeLLM で検査していることはコードで確認)。
- multi-public の system / パケットの文面差、筋書きブロックの文面、hidden states 抽出 (`scripts/extract_hidden.py`)、`find_scenario_deviations` の正しさは見ていない (監査 A / C の範囲)。
- #3 (a) の「近接確率の反転」は logprob 差 < 0.1 の観測から vLLM のバッチ構成差と推測した (DESIGN §14 と同じ見立て)。同一入力の再実行で再現率を測ってはいない。
- #2 の「発言順で書く」は batch 4 局の目視 (3 discussion + aiwolf_0001) に基づく。90 setup 全体の傾向は未確認。
