# 検閲 2 (2026-10-28) のまとめ: パイロット 5 (5 条件 + process 筋書き) と実装

対象: パイロット 5 (63 局、gemma-4-31B-it、greedy; ログは ../../../undergraduate_research_archive/2026-10-28_pilot5/log_pilot5/ に退避)、筋書き v1 (同 archive の pilot5_scenarios_v1_leaky)、hidden states 実機取得 (aiwolf_0001 × 5 条件)。第 2 ラウンドの対象 (パイロット 6) は log/_pilot6。
報告: 01 プロンプトと条件 (A)、02 実行経路とログ (B)、03 筋書き (C)、04 結果と hidden states (D)、05 横断 (E)、06 自己検閲。
検閲は読み取りのみ。修正は検閲後に行い、本ファイルの「対処」に記す。pilot5_inspect.txt は集計 (再実行済みの完全版)。

## 結論

- 統制の機構は動いている: 共通ブロックのバイト一致、server 経路 45 局の TALK / VOTE / ACTION の user がログ由来のビューとバイト一致、prompt_token_ids = usage.prompt_tokens (2688/2688)、single-batch-stepped の接頭辞トークン列が single-batch と同一 (9/9 setup)、hidden states の恒等性 (同一区間で cos ≥ 0.9998)。
- **Critical 2 件** (いずれも修正済み、再実行待ち): (1) process 筋書き 9 本すべてが結末・選好・選択肢名・被疑者名を含み、multi-private-process が実質 public だった。(2) single-batch-stepped の人狼で占いが全て無効 (書き手が `Shizue (werewolf)` と結果まで書き、名前照合が弾いた)。
- **Major**: 梯子の段に混入する差の明記 (stepped→online は目標 + 置き場所、online→multi-public は役割文 + 文脈の分割 + 他席の夜の行動・調査の可視性)、vLLM の非決定性の床が未測定、議論ドメインでラベル A が 42 局中 34 局で採択 (ラベル順の偏り)、評価が未設計で条件が台本から識別できる (長さ)、header に推論環境の記録が無い、サーバの票・調査行の順序 (席順) が batch の書き手 (発話順) と違い stepped が必ず分岐、stepped の `raw_differs` が先頭スペースで全発話 true、先出し検出の偽陽性と主張の向きの逆転 (online 20 件 > batch 1 件)。

## 発見と対処

| # | 深刻度 | 発見 (報告) | 対処 (2026-10-28) |
|---|---|---|---|
| 1 | Critical | process 筋書きが結末・秘密を含む (A, C, D, E, 06) | `common/scenario.py` `_validate_prose` を強化: 結末・選好の語、選択肢名、素材に無い選択肢語、選択肢ラベル参照、人狼では公開の筋と席の筋の他者名を禁止 (ターン行は対象外)。生成要求文を同じ規則に。旧 9 本は ../undergraduate_research_archive/2026-10-28_pre_pilot6/log_pilots/pilot5_scenarios_v1_leaky/ に退避、再生成と process 条件の再実行 (パイロット 6) |
| 2 | Critical | stepped の占いが無効 (A, B, D) | `server/base/parse.py match_name` と `agent/base/seat.py match_candidate` が末尾の括弧を許容 (raw は保存)。FakeLLM が ` Name (human)` を返しテストで再現 |
| 3 | Major | 票・調査行の順序 (サーバ席順 vs 書き手発話順) で stepped が分岐 (B, D) | サーバの VOTE / INVESTIGATE を発話順に。変換器も書かれた順を保持 (fixed モードは発話順) |
| 4 | Major | ラベル順の偏り (E) | setup に `option_perm` (seed からの決定的順列) を追加 (既存 60 setup に移行)。`ctx.options()` が表示順に A, B, … と付け直し `orig_label` を保持、header に記録 |
| 5 | Major | 非決定性の床が未測定、batch と stepped を同時投入 (D, E) | パイロット 6 で `VLLM_BATCH_INVARIANT=1` を試し、single-batch を 2 回回して反復の一致を測る。top-k logprob の記録は保留 |
| 6 | Major | online→multi-public に他席の夜の行動・調査の可視性の差 (E, A の Findings/Options も同根) | DESIGN §13 に明記。論文では「1 人の全知の文脈 vs 席ごとの文脈 (他席の動的な秘密は見えない)」と書く。追加条件は作らない |
| 7 | Major | 評価未設計、条件が長さで識別可能 (E, D) | 評価設計 (別途): 一次軸と対、長さの共変量、盲検の監査。本検閲の範囲外 |
| 8 | Major | 先出し検出の偽陽性 ('Campus', 'Location') と主張の逆転 (D, E) | 素材語に議題タイトルを追加。語彙の偶然一致と区別するため候補名・数値・人手検証を評価設計に。論文の「batch に固有」は撤回 |
| 9 | Major | `raw_differs` が stepped で全発話 true (B) | 端の空白を無視 (全条件共通) |
| 10 | Major | header に vLLM 版・revision・精度・chat template が無い (B, E, D) | `common/llm_meta.py`: vllm_version、model_root、hf_revision、chat_template_sha1、config_sha1 を両方式の header に |
| 11 | Major | 札トークンの機能差: online / multi の `**:` は文末記号を予測する位置 (D) | extract_hidden の index に `gen_point` を追加 (条件間比較はこの位置)。DESIGN §14 に記載 |
| 12 | Major | 人狼の筋書き 3 本が同型 (0 夜に人狼を当て 1 日目終局)、結末ラベルに分散なし (C, E) | 設計の限界として記録。筋書きの多様性は本実験の筋書き生成後に確認。aiwolf の結末分散は評価軸の選択で扱う |
| 13 | Major | process では乖離検出が空 (C) | process 条件の筋書き追従は「話題・立場の一致」など別の指標で測る (評価設計へ) |
| 14 | Major | 修復を後付けした筋書きの記録不整合 (C, A) | 生成記録に messages / sampling / token id、修復は生成時に適用し各 attempt に記録。空ターンも修復。旧ファイルは退避 |
| 15 | Minor | 文書の矛盾・古い記述 (DESIGN §13 の「筋書きは必ず public」、IMPLEMENTATION_NOTES の continue_final_message) | 修正 |
| 16 | Minor | GPU 予約の開始前に使用 (06) | 運用規則として明記: 予約開始を待つ |
| 17 | Minor | batch の出力形式にだけある制約文 (A) | 台本の妥当性要件として論文に列挙 (変更しない) |

## 本実験に進む前の必須事項 (E の優先順位と合わせて)

1. パイロット 6 で (1)(2)(3)(4)(5)(9)(10) の効果を確認する: process 筋書きの漏洩ゼロ、stepped の占い成立、batch と stepped の一致区間の延び、反復の一致率、ラベル採択の分散。
2. 評価設計 (一次軸、対、盲検、長さの共変量、人手評価の規模) を決めてから本実験を回す。
3. 論文 v4: タイトル (「Generation Granularity」は主張と矛盾)、貢献の弱め、梯子の各段に混入する差の明記、先出しの向き。

## 確認した範囲 / していない範囲

各報告の末尾を参照。評価の妥当性、Qwen3.8 / gemma-4-12B での動作、筋書きの outline / turn 条件は未確認。

---

## 第 2 ラウンド (パイロット 6、2026-10-28 09:00〜10:00 JST): 報告 11〜15

結論: **Critical 2 件は解消** (process 筋書きの漏洩: 9/9 検証通過・Plan ブロックのバイト一致・multi-private-process の先出し 27 → 1 件; stepped の占い 3/3 有効)。退行なし (ビュー一致 45/45 局、テスト 201 本)。**5 本とも「本実験に進んでよい」** で、残る (a) は記録と運用規則の小物。評価設計は本実験の前に行う (方針どおり)。

| # | 分類 | 指摘 (報告) | 対処 |
|---|---|---|---|
| R1 | (a) 済 | 筋書きの `source` にコード版・実効設定・推論環境が無い (C) | gen_scenarios: `code_sha1` (生成に関わる 4 ファイル)、`max_tokens` / `max_attempts` / `granularity`、`served`、`code_tree` を記録 |
| R2 | (a) 済 | 有効な占い・襲撃の行に `raw` が無く、書き手の述べた結果を .log から数えられない (A, B) | server/aiwolf/logic.py: 常に `raw` を記録 |
| R3 | (a) 済 | stepped の夜 ≥ 1 で占いの仮行に結果が無く、batch (夜に結果まで書く) と必ず分岐する (B) | 書き手ビューは占い結果を夜のうちに書く (書き手は全役職を知る; view_from_rows の seat None も同じ) |
| R4 | (a) 済 | 言い換えの結末語 (`yields to the team's need`) (A) と、人狼の筋書きが「占い師が Day 1 に公表」を固定し結末を反転させる (A, C, E) | `_validate_prose` に言い換え句と、人狼では役職・名乗り・占いの語を禁止 (生成規則として決着、本実験の 90 本から適用) |
| R5 | (a) 済 | header に接続先・サーバのタイムアウト・サーバ設定 (バッチ不変フラグ、GPU、max len、prefix caching) が無い (B, D) | header に `endpoint`、`server_timeout_s`、`server_config` (start.sh が running/<port>.json を書き、llm_meta が読む)、`code_tree` (コード一式の sha1) |
| R6 | (a) 済 | 近接確率の「近さ」を直接示す記録が無い (B, D, E) | 全呼び出しで次点トークン (`alt`: top-2) を記録 |
| R7 | (a) 済 | 名前照合の server / agent 非対称 (B) | 両方とも括弧の後の句読点を許容 |
| R8 | (a) 運用規則 | batch と stepped が別 GPU で走った (D): 分岐の帰属が「GPU の差」と混ざる。反復は温度 0 + バッチ不変では「決定性の確認」にすぎない (D, E) | 本実験の実行規則: 同じ setup の全条件は同じサーバで回す。反復は single-batch 全部 (安い) + stepped / multi-private を各ドメイン 3 setup + 3 setup のサーバ間一致確認。報告は一致率と最初の分岐 |
| R9 | (b) | 元の A 案が表示順に関わらず 48 局中 34 局で採択 (中身の偏り) (E, D) | 採択分布を報告し、結末が均等であることを前提にした指標・ラベルは使わない。議題は作り直さない |
| R10 | (b) | hidden states の条件間 cos (最終層 0.2〜0.4、中間層 0.96) は無関係な行や別 setup でも同じ値で、条件差として解釈できない (D) | 論文では条件間の生の cos は示さず、条件内の復号可能性と同一履歴の再生で比較 |
| R11 | (b) | 全知条件の人狼は 15/15 で 0 夜に人狼を当てて Day 1 終局 (E) | 全知の帰結として報告。結末ラベルの分散が無いことをプローブの限界に |
| R12 | (b) | 筋書きの言い換え漏洩は語彙規則では完全には防げない (C) | 評価設計で「筋書きから結末を当てられるか」の判定 (LLM / 人手) を 1 回入れる |
| R13 | (b) | パイロット 5 と 6 の single-batch が同一プロンプトで分岐 (サーバ設定差) (D) | 「再現性はサーバ設定を固定した上で」と明記; header の `server_config` で固定を示す |
| R14 | (c) | 追加条件、筋書きの多様性制約、top-k の全記録 | 採らない |

本実験前にやること (順): (1) git 管理の導入 (ユーザ判断待ち)、(2) 評価の事前仕様 1 ページ (一次軸、対、同等性マージン、描画、盲検の監査、長さの共変量、除外規則)、(3) 実行規則 1 ページ (サーバ割当、反復、サーバ間確認)、(4) 90 本の筋書き生成 (新規則、記録つき)、(5) 本実験。予備評価 (サブエージェントの読み比べ) は (2) の前に行う。
