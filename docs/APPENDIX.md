# Appendix material (generated 2026-10-31 by `scripts/build_appendix.py`)

Everything that may go into a paper appendix, in one place: conditions and settings (A), prompts (B), judging (C), metrics (D), detailed results (E), reproducibility notes (F). Result sections are copies of the result documents named under each heading; those documents and the logs stay the source.

## A. Conditions, models and settings

### A.1 Names

| presentation name | condition (code / logs) | writer | information | generation goal |
|---|---|---|---|---|
| シングル・全文 | single-batch | one LLM | all (omniscient) | whole script in one call |
| (control) | single-batch-stepped | one LLM | all | the whole-script request, continued one line per call |
| シングル・1 発話 | single-online | one LLM | all | next line only |
| マルチ・全文 | multi-private-stepped (multi-batch) | one LLM per seat | own seat | whole-script request, the seat's next line only is kept |
| マルチ・1 発話 | multi-private (multi-online) | one LLM per seat | own seat | next line only |
| (omniscient seats) | multi-public, multi-public-stepped | one LLM per seat | all | next line / whole-script request |
| (plan) | *-process | as the base condition | + a process plan without the outcome | as the base |


Few-shot conditions (DESIGN §16): single-batch and multi-private with 3 discussion examples of the model's own (short = its single-batch games, long = its multi-private games; other setups of the same domain, the first 3 in setup order, the target setup excluded), logs under `log/fewshot/<model>__ex-<short|long>/`. Goal swap: recorded states re-generated under the other goal (`log/goal_swap/`); examples vs history: long-history states with 3 short examples (`log/goal_swap_ex/`).

### A.2 Design document

_Source: `docs/DESIGN.md`_

### 設計文書: 単体エージェント vs マルチエージェントによる議論生成 (3ドメイン)

作成 2026-10-26。**v0.4** (v0.2 = 独立レビュー2本の反映。v0.3 = §10 の最終未決を確定。v0.4 = 2026-10-27、3ドメインを同一の Python サーバ基盤に載せる構成に変更)。
v0.1 からの主な変更: 情報公開スケジュールの共通化 (§5, §6.2)、違反会計の両方式化 (§8)、同票規則の決定論化 (§6.1)、
Skip 改造の撤回 (§4.5)、単体 Markdown の節順修正 (§7.2)、指標の分母定義 (§11)。
v0.3: panel の選択肢は 4 のまま (§10)、カード書き直しは表現調整のみ (§9-9)。
v0.4: ディレクトリを common / server / agent / single に再編 (§2)、aiwolf の Go 改造をやめて 3 ドメインとも Python サーバ (§4.5)、ドメイン名を `aiwolf` / `candidate_selection` / `shared_living` に変更、要求名を aiwolf-nlp-common の語彙に統一 (§5)。
v0.4.1 (2026-10-27、実装レビューとパイロット監査の反映): 投票内訳と襲撃なしの通知 (§5)、生応答をワイヤに流す (§4.5-5)、`trailing_over` / `early_reveal_partial` / `tie_choice_differs` (§8)、jsonl の時系列 seq と setup_sha1 (§3.2)、`--info-mode` 上書き。実装状況は §12。

---

#### 0. 目的と原則

- **比較するもの**: 単体 (single: 1つの LLM が議論全文を一括生成) と マルチ (multi: 席ごとに独立した LLM が1発話ずつ生成)。
- **統制**: 両方式の差を「生成単位」だけに絞る。ルール文・ペルソナ・役職・議題・発話順・語数・Over/Skip の説明・情報公開スケジュールは、すべて**同じ設定ファイルと同じ Jinja ブロック**から展開し、文言をバイト一致させる。
- **据え置く差 (研究テーマ)**: 単体は全席の非公開情報を一度に見る (全知性)。投票・調査などの行動も単体は一括で書く。
- **ドメイン**: `aiwolf` / `candidate_selection` (移植元の panel) / `shared_living` (移植元の living) の3つ。本文では短く panel / living とも書く。candidate_selection と shared_living は同じ進行、aiwolf だけ異なる進行 (意図した設計)。ドメインは比較軸ではなく**層別因子**。
- **持ち込まないもの**: 失敗モードの指示文、投票宣言ナッジ、発話カウンタの使用数・残数、シナリオ注入、factors、cache、tactics、mixed、コスト台帳、サーバ側の文字数打ち切り。
- **モデル**: ローカル vLLM の OpenAI 互換エンドポイント。思考トークンを出力に含むモデルは使わない。

#### 1. 用語

| 用語 | 意味 |
|---|---|
| domain | `aiwolf` / `candidate_selection` / `shared_living`。ディレクトリ名・ログの domain 値・setup_id の接頭辞はすべてこの文字列 |
| method | `single` / `multi` |
| setup_id | 1対局分の固定設定の id。`<domain>_<k:04d>` (例 `living_0007`)。同じ id を single と multi が読む (ペアリング) |
| game_id | `<setup_id>__<method>__<model_tag>__<timestamp>` |
| seat | 1..5。設定ファイルで固定。aiwolf サーバの agent idx と一致させる |
| round | 議論の区切り。aiwolf では day (0 から)、panel/living では round (1..3)。ログ列名は `round` に統一 |
| turn | ラウンド内のターン番号 **1..4** (表示・ログとも 1 始まり) |
| role slot | 役職スロット。固定の非公開種 + 行動仕様。`roles.yml` で定義 |
| action | ラウンド間の非公開行動。aiwolf: divine / attack、panel・living: investigate |
| notice | 状態通知。DAILY_INITIALIZE / DAILY_FINISH (aiwolf-nlp-common の語彙。本文では ROUND_START / ROUND_END とも書く)。"Acknowledged." で受ける (マルチのみ) |
| request | サーバ→エージェントの要求種別。`NAME` / `INITIALIZE` / `DAILY_INITIALIZE` / `TALK` / `VOTE` / `DIVINE` / `ATTACK` / `INVESTIGATE` / `DAILY_FINISH` / `FINISH` (§4.5) |

#### 2. ディレクトリ構成

aiwolf-nlp の server / agent / common の3層に対応させる。3ドメインとも同じ基盤に載せ、ドメイン差はサブディレクトリに閉じ込める。

```
undergraduate_research/
  pyproject.toml                 # 1 プロジェクト (uv)。common / server / agent / single を同梱
  docs/DESIGN.md
  common/                        # aiwolf-nlp-common 相当。server / agent / single が import する
    protocol.py                  #   要求種別・パケット (aiwolf-nlp-common 0.7.0 とワイヤ互換、§4.5)
    schema.py  logwriter.py      #   共通ログ (§3) の行型と書き出し
    setup.py                     #   setups/ と data/ の読み込み・検証
    render.py                    #   Jinja 環境 (common/prompts の共通ブロック)
    tiebreak.py                  #   同票規則 (§6.1)
    violations.py                #   違反会計 (§8)。.log を入力に両方式共通で走る
    convert/single_markdown.py   #   単体 Markdown → 共通形式
    convert/aiwolf_go.py         #   Go サーバの CSV/JSON → 共通形式 (互換テスト専用)
    convert/legacy_resultjson.py #   移植元 result.json → 共通形式 (テスト専用)
    prompts/*.jinja              #   両方式共通ブロック (§6.2)
  server/                        # 進行役。setup を読み、配役・発話順を固定し、共通ログを直接書く
    base/                        #   進行ループ・websocket・フェーズ制御・ログ書き出し
    aiwolf/                      #   役職・占い・襲撃・処刑・勝敗・max_day
    candidate_selection/         #   困りごと・カード調査・選択肢公開・採択
    shared_living/               #   同上 (candidate_selection と実装共有、instances が違うだけ)
  agent/                         # マルチ。server と同じ割り方
    base/                        #   websocket クライアント・LLM 呼び出し・差分履歴・プロンプト組み立て
    aiwolf/  candidate_selection/  shared_living/   # 方式固有テンプレートとドメイン固有の要求処理
    prompts/*.jinja              #   マルチ固有の組み立て (notice など)
  single/                        # 単体。setup → プロンプト → Markdown → common/convert で変換
    base/  aiwolf/  candidate_selection/  shared_living/
    prompts/*.jinja              #   単体固有の組み立て (執筆者枠づけ・出力形式・hidden.jinja)
  data/
    personas.yml                 # 24人、4項目 (name, age, gender, personality)
    <domain>/roles.yml  rules.yml  instances.json (candidate_selection / shared_living のみ)
  setups/<domain>/<setup_id>.json
  config/models.yml  experiment.yml
  scripts/make_setups.py  verify_prompt_control.py  run_multi.py  run_single.py  compat_aiwolf_go.py
  tests/
  log/<domain>/<method>/<game_id>/<game_id>.log  <game_id>.jsonl  raw/
```

#### 3. 共通ログスキーマ

##### 3.1 `<game_id>.log` (CSV、固定8列、標準クォート)

| 列 | 型 | 内容 |
|---|---|---|
| seq | int | 対局内の通し番号 (0 から)。**時系列順** |
| round | int | aiwolf は day、panel/living は round |
| turn | int / 空 | talk・pass のみ (1..4)。他は空 |
| type | enum | `status` / `talk` / `pass` / `vote` / `action` / `result` |
| agent | str | 席の名前 (ペルソナ名)。行為者がいない行 (execute, result) は空 |
| target | str / 空 | vote・action の対象 (名前、選択肢ラベル、card_id) |
| text | str | talk は発話本文 (**他席に見えた文** = server の正規化後)、pass は `Over` / `Skip`、action は結果要約、result は勝者/採択 |
| extra | JSON str / 空 | 方式・ドメイン固有の付帯情報 (下表) |

type ごとの `extra`:

| type | extra |
|---|---|
| status | `{"seat":1,"role":"SEER","alive":true}`。各ラウンド開始時と終局後 (最終 day+1) に全席分 |
| talk | `{"words":23,"mentions":["Rin"],"raw_differs":false}`。words / mentions は **text 列 (他席に見えた文)** で計算。`raw_differs` は server の正規化 (§4.5-5) で生応答と変わったとき true |
| pass | `{"forced":false,"empty":false}`。通信エラー由来の ForceSkip は `forced:true`、空応答由来の Over は `empty:true` (サーバ JSON の error から復元) |
| vote | `{"request":"vote_final"\|"vote_day","raw":"...","valid":true,"tie":false}`。無効票 (不正名・死者・パース不能) は `valid:false`・target 空の行を**サーバ JSON の response から生成** (CSV には現れない) |
| action | aiwolf: `{"action":"divine","result":"WEREWOLF","valid":true}` / `{"action":"attack","success":true,"no_target":false}` (attackVote と attack の 2 行を 1 行に統合) / `{"action":"execute","role":"VILLAGER","tie":false}`。panel/living: `{"action":"investigate","cards":["card_03","card_07"],"parse":"ok"\|"partial"\|"fail"}` |
| result | aiwolf: `{"winner":"VILLAGE"\|"WEREWOLF"\|"NONE","villagers":3,"werewolves":0}`。panel/living: `{"adopted":"B","tally":{"A":1,"B":3,"C":1},"tie":false}` |

正規化: 勝者はサーバの `VILLAGER` / `WEREWOLF` と単体の `village` / `werewolves` を `VILLAGE` / `WEREWOLF` に揃える。種族は `HUMAN` / `WEREWOLF`。`NONE` はエラー終了 (`max_continue_error_ratio`) の場合。

##### 3.2 `<game_id>.jsonl`

- `{"kind":"header", ...}`: game_id, setup_id, domain, method, model (models.yml のフルネーム), model_tag, info_mode, setup_path, setup_sha1 (setup JSON のバイト列の sha1), started_at / finished_at (**tz 付き UTC ISO**、両方式), participants (seat, name, role_slot, persona 4項目, private seed), card_pool (aiwolf は `[]`), **n_options**, **n_unique_cards** (dynamic で実際に引かれた一意カード数。aiwolf は 0), outcome, config ハッシュ。
- `{"kind":"llm_call", ...}`: seq (**対局内の時系列通し番号 0..n-1**。multi は server がマージ時に付け直し、agent 側の席内カウンタは `seat_seq`), seat (single は `writer`), request (§1 の要求名。単体は `FULL`), round, turn, ts (UTC), model, messages, response (**生応答**), usage, **finish_reason**, **error**, truncated (= finish_reason が length), latency_ms。
- `{"kind":"violations","items":[...]}`: §8 の違反 (**両方式とも**、1 レコード)。multi は server が終局時に `find_violations` + `find_truncations` で書く。single は変換器の構造違反と共通コードを合わせて 1 レコードに書く。`scripts/convert_logs.py` は共通コードだけを再計算し、構造違反 (行番号付き) と `llm_error` 等は保持する。

##### 3.3 書き出しと変換器 `common/convert/`

| 方式 | 書き手 | 備考 |
|---|---|---|
| multi (3ドメイン) | **server/base の logwriter が共通形式を直接書く** | 変換なし。無効票・強制 Skip・空応答は server が extra に記録する。jsonl の llm_call は agent 側が送信メッセージと生応答を書き、server が game_id で突合する (agent は `<log_dir>/<domain>/multi/<game_id>/raw/agent.<seat>.jsonl` を書き、終局後に server がマージ) |
| single (3ドメイン) | Markdown 原本 → `single_markdown.py` | 厳密パース (§8)。採択・処刑・勝者は**票から再計算**して書き手の値と照合 |
| Go サーバ (互換テスト) | サーバ CSV + JSON → `aiwolf_go.py` | `scripts/compat_aiwolf_go.py` が同じ台本エージェントを Go サーバと Python サーバにつなぎ、共通形式で突合する。CSV の talk 行はカンマ非エスケープなので type 別 maxsplit |
| 移植元 result.json | `legacy_resultjson.py` | テスト専用 |

#### 4. 設定ファイル

##### 4.1 `data/personas.yml`

24人。項目は本家 aiwolf-nlp-server の custom_profile と同じ **name / age / gender / personality** のみ。出典は移植元の英語サーバ config。persona_id = name。職業は持たない。panel の context は「各部門の審査員」風だが肩書は与えない。**話者間の事実整合性は従属変数に使わない** (§11)。

##### 4.2 `data/<domain>/roles.yml`

```yaml
slots:
  <SLOT_NAME>:
    count: <int>
    public_label: <str>
    private_seed: <kind>          # role | problem
    action:                       # null 可
      name: <str>
      when: <str>
      choose: <int>
      from: <str>
      result: <str>
      on_parse_fail: none         # 全ドメイン共通: 結果なし・記録のみ
```

```yaml
# aiwolf
slots:
  SEER:      {count: 1, public_label: participant, private_seed: role,
              action: {name: divine, when: every_night, choose: 1, from: alive_others, result: species}}
  WEREWOLF:  {count: 1, public_label: participant, private_seed: role,
              action: {name: attack, when: night_from_day1, choose: 1, from: alive_others, result: death}}
  POSSESSED: {count: 1, public_label: participant, private_seed: role, action: null}
  VILLAGER:  {count: 2, public_label: participant, private_seed: role, action: null}
# panel / living (同一)
slots:
  PARTICIPANT: {count: 5, public_label: participant, private_seed: problem,
                action: {name: investigate, when: after_round_1, choose: 2,
                         from: card_pool_titles, result: card_text}}
```

##### 4.3 `data/<domain>/instances.json` (panel / living)

```json
{"instance_id": "living_001",
 "topic": {"title": "...", "context": "...",
           "options": [{"label": "A", "name": "...", "summary": "..."}, ...]},
 "problems": {"1": "...", ..., "5": "..."},
 "card_pool": [{"card_id": "card_01", "title": "Time needed for a full cleaning pass",
                "text": "A stopwatch timing of ...", "origin_seat": 2}, ... 10枚],
 "fixed_assignment": {"1": ["card_01", "card_02"], ...}}
```

制約: タイトルに `;` と改行を含めない (単体の Action 行の区切りに使うため)。`fixed_assignment` は `info_mode: fixed` の予備用。

##### 4.4 `setups/<domain>/<setup_id>.json`

```json
{"setup_id": "living_0007", "domain": "living", "k": 7, "instance_id": "living_008",
 "seats": [{"seat": 1, "persona": "Misaki", "role_slot": "PARTICIPANT"}, ...],
 "speaking_order": [3, 1, 5, 2, 4],
 "info_mode": "dynamic"}
```

生成規則 `game_setup(domain, k)`:
- `rng = random.Random(f"{EXPERIMENT_SEED}:{domain}:{k}")`
- キャスト: 24人から `rng.sample` で5人、席 1..5 に抽選順で配置。
- 役職: slot を count 分に展開し名前順ソート → `rng.shuffle` → 席順に割当。
- 発話順: 席番号の `rng.shuffle` による順列1つ。全ラウンド固定。
- インスタンス: `instances[k % len(instances)]`。**N は 10 の倍数** (各インスタンスが均等)。
- N=30 を既定 (パイロット後に 50 へ増やすか判断)。aiwolf も同じ N。

##### 4.5 サーバ (`server/`、3ドメイン共通の Python 実装)

Go 製 aiwolf-nlp-server は改造せず (このマシンの Go は 1.22 で、ビルドにも 1.24 が要る)、`server/base` に進行ループを Python で書き、3ドメインを同じ基盤に載せる。5人村に必要な人狼ロジック (役職・固定順 Talk・投票・処刑・占い・襲撃・勝敗・max_day) は小さい。

1. **ワイヤ形式は aiwolf-nlp-common 0.7.0 と互換**。パケットは `{request, info, setting, talk_history, whisper_history}`。`info` は `game_id, day, agent, profile, status_map, role_map, divine_result, executed_agent, attacked_agent, vote_list, remain_count, remain_skip` を同名で持ち、ドメイン拡張として `problem` (INITIALIZE)、`card_titles` (INITIALIZE)、`investigate_result` (DAILY_INITIALIZE、本人のみ)、`options` (DAILY_INITIALIZE、Round 3) を加える。aiwolf-nlp-common の `Info.from_dict` は未知キーを捨てるので、既存エージェントもそのまま接続できる。
2. 要求列: `NAME` → `INITIALIZE` → 各ラウンド `DAILY_INITIALIZE` → `TALK`×最大4 → (`VOTE`) → (`DIVINE` / `ATTACK` / `INVESTIGATE`) → `DAILY_FINISH` → `FINISH`。`day` 列はドメインを問わずラウンド番号 (aiwolf は 0 始まり、他は 1 始まり)。
3. 席固定: `AIWOLF_SETUP_FILE` (環境変数) または `--setup` で setup を読み、接続名 (`NAME` 応答) を `seat1..seat5` と照合して席を決める。配役・ペルソナ・発話順は setup の値をそのまま使い、乱数は使わない。
4. Talk: 固定順 × 4 ターン。Skip はターンを消費し回数無制限 (`max_skip` 相当なし)。Over でそのラウンド離脱。空応答・応答不能 (タイムアウト・切断以外のエラー) は `Over` (`empty:true`) / `Skip` (`forced:true`) として記録。切断は対局中止 (`winner: NONE`)。
5. **発話の正規化**: 前後空白の除去のみ。agent は LLM の生応答をそのままワイヤに流し、server が strip して `raw` と比較する。発話末尾に埋め込まれた "Over." は剥がさず talk として記録する (移植元は剥がしていた。`trailing_over` で数える、§8)。`@名前` の再構成 (Go の `processText`) は**行わない**。語数の切り捨ても行わない (word_cap はプロンプト上の指示であり、超過は §8 の `over_cap` として記録)。`raw_differs` は端の空白 (strip) では true にならず (2026-10-28: 続き書きの先頭スペースを差としないため)、正規化で本文が変わった場合と空→Over の場合に true。
6. 投票: 無効票 (不正名・死者・自分以外が禁止のとき自分・パース不能) は不算入で `valid:false`。再投票なし。同票は §6.1 の決定論規則。
7. aiwolf 固有: `allow_self_vote: true`、`max_day: 3`、襲撃は Day 1 以降、襲撃対象が不正なら不成立 (`attack` 行の `no_target:true`)、勝敗は村 = 人狼が死亡、人狼 = 人狼数 ≥ 人間数。
8. ログは `common/logwriter` で共通形式 (§3) を直接書く。Go 版との互換は `scripts/compat_aiwolf_go.py` で確認する (同じ台本エージェント、`@` を含む発話は空白を正規化して比較)。

##### 4.6 発話の正規化 (両方式共通、2026-10-27)

`common/normalize.py` の `normalize_talk` を server (multi) と単体変換器の両方が呼ぶ。議論の質と無関係な表記ゆれはここで吸収し、
**必ず記録する** (行の extra.norm と violations の `kind: normalized`)。

- 前後の空白・句読点: 除去 (発話内の改行は両方式とも保持。複数行の発話は許可。単体の台本では次の箇条書き/見出しまでの行を直前の発話に連結)
- Skip/Over の表記ゆれ ("Over." / "skip" / '"Over"'): トークンに正規化 (`pass_punct`)
- 発話全体を囲む引用符や `**`: 外す (`format_noise` kind=wrap)
- 先頭の自分の名前ラベル ("Kenji: …", "**Kenji**: …"): 外す (`name_label` self=true)。他人の名前ラベルはそのまま残し、`speak_for_others` (本物の違反) として後で判定
- 本文の末尾に付いた正確なトークン ("… see you tomorrow. Over."): 外し (`trailing_over`)、Over なら次ターン以降その席は離脱 (pass 行 `trailing:true` を直後に書く。他席には "Name: text" と "Name: Over" の 2 行として見える)。大文字小文字を区別するので "turn it over." は文として扱う

違反 (`kind: violation`) として残るのは、over_cap / 他人の名前ラベル (name_label, speak_for_others) / multi_utt / 残りの format_noise (ト書き・見出し等) / early_reveal(_partial) / truncated。
`scripts/convert_logs.py` は `#violation` と `#normalized` の列で両者を分けて集計する。

##### 4.7 通知の原則 (multi、2026-10-27)

進行表で「あるはず」のものだけを報告し、あるはずなのに無いときは「ありませんでした」を出す。文言は rules.yml `notice_sentences`。
- 1 日目の朝: 処刑・襲撃・投票内訳は出さない (夜 0 にはない)。占い師にだけ占い結果 (失敗なら "No divination result last night.")。
- 2 日目以降の朝: "X was executed." / "No one was executed."、"Y was attacked." / "No one was attacked last night."、"Votes: …"、占い師には占い結果。
- discussion の Round 2 開始: 調査結果 ("What you looked into:") か、何も調べられなかった席には "Nothing was looked into; there are no findings."。Round 3 開始: 選択肢。
- 占い師が死亡している場合は報告先がないので何も出ない (全員に「占いなし」を出すと占い師の死亡が漏れる)。

#### 5. ラウンド構造・要求列・情報公開スケジュール

| 工程 | aiwolf | panel / living |
|---|---|---|
| INITIALIZE | 名前・役職・ペルソナ・ルール・スケジュール | 名前・困りごと・ペルソナ・議題・カードタイトル一覧・ルール・スケジュール |
| DAILY_INITIALIZE (ROUND_START) | Day d 開始。前夜の結果 (占い結果は占い師のみ、処刑・襲撃は全員、襲撃なしの朝は "No one was attacked last night.")、**前日の投票内訳** (全員。移植元の vote_visibility と同じ。単体は全票を書くので対称) | Round r 開始。r=2: 自分が選んだカード本文。r=3: 選択肢の公開 |
| TALK × 4 ターン | 発話 / Skip / Over | 同じ |
| VOTE | Day ≥ 1 で毎日。処刑 | Round 3 の後のみ。採択 |
| DIVINE / ATTACK / INVESTIGATE (ACTION) | 夜 (投票・処刑の後): DIVINE (SEER)、ATTACK (WEREWOLF, Day ≥ 1) | Round 1 の後: INVESTIGATE (全員、2枚) |
| DAILY_FINISH (ROUND_END) | Day d 終了 + その日の発話差分 | Round r 終了 + 発話差分 |
| FINISH | 勝敗 | 採択結果 |

**情報公開スケジュールは両方式の共通知識**として `schedule.jinja` (§6.2) に書く。単体は全情報を最初から見るが、「公開前のラウンドで言及しない」制約を受け、先出しは `early_reveal` 違反として数える (§8)。時系列は Talk → Vote → (夜の) Action の順で、ログの seq もこの順。

#### 6. ルール変数と共通ブロック

##### 6.1 `data/<domain>/rules.yml`

| 変数 | aiwolf | panel / living |
|---|---|---|
| period_name | `day` | `round` |
| n_participants | 5 | 5 |
| turns_per_round | 4 | 4 |
| word_cap | 40 | 40 |
| pass_tokens | Over / Skip | Over / Skip |
| rounds_total | 決着まで (技術的上限 Day 3、モデルには見せない) | 3 |
| vote_rule | Day 1 以降毎日。最多票を処刑 | Round 3 の後に1回。最多票の選択肢を採択 |
| tie_rule | **共通**: 同票候補を名前 (ラベル) 順に並べ、`sha1(f"{setup_id}:{round}") mod n` 番目を採る (`common/tiebreak.py`)。単体の変換器も同じ関数で再計算 | 同左 |
| action_rule | 夜に SEER が1人を占う (人間か人狼か)。Day 1 以降 WEREWOLF が1人を襲う | Round 1 の後、各自がカード一覧から2枚を選んで調べる。結果は本人だけに届く |
| schedule | 占い結果は翌朝本人に、処刑・襲撃の結果は翌朝全員に知らされる | カードの調査結果は Round 2 開始時に本人に、選択肢は Round 3 開始時に全員に知らされる |
| self_vote | 許可 (サーバ `allow_self_vote: true`) | 該当なし |
| win_or_end | 村: 人狼処刑。人狼: 人数同数以上 | 投票で終了 |

##### 6.2 共通ブロック (英語文言案。両方式でバイト一致させる部分)

各ブロックは Markdown 見出し (`## Setting` / `## Discussion format` / `## Schedule` / `## <action_heading>`) で始める (2026-10-27)。人物の節は multi が `## Your profile` (自席 1 つ)、single が `## Participants` (5 席)。single の追加節は `## For the writer only` (disclosure) と `## Output format`。

**structure.jinja**
```
## Discussion format
The talk proceeds in {{ period_name }}s. Each {{ period_name }} has {{ turns_per_round }} turns; in each turn, every participant speaks once, in this fixed order: {{ speaking_order_names }}. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this {{ period_name }}). An utterance is anywhere from 1 to {{ word_cap }} words; give it the length and content that suit the moment.
```

**schedule.jinja** (新設)
```
## Schedule
| (schedule_table.columns) |
| (schedule_table.rows: ラウンド/日ごとに「開始時に誰に何が知らされるか / Talk / 終了時に何をするか / (aiwolf) 夜」) |
- (schedule_notes)
{{ vote_rule_sentence }} {{ end_sentence }}

(2026-10-27: 文章だったスケジュールを表 + 注記に変更。各ラウンド/日に開示される情報と行われることを 1 行ずつ示し、
占い師の死亡・カードの重複などの条件は注記に書く。fixed モードは `schedule_table_fixed` / `schedule_notes_fixed`。
aiwolf の「最長 Day 3」はモデルに見せない: 5 人村は投票・襲撃が成立する限り Day 2 までに終わるので、`rounds_total: 3`
は server / 変換器の技術的な安全上限に留める (移植元サーバは max_day -1)。)
```
例 (living): `The things you look into become known to you at the start of round 2. The concrete options are revealed to everyone at the start of round 3. At the end of round 3, each participant votes for one option, and the most-voted option is adopted.`

(position.jinja は廃止 (2026-10-27): 位置は台本の `## Day d` / `#### Turn t of 4` 見出しで両方式同じに示す。)

**(廃止: 内容規則は structure ブロックへ統合)**
```
Output only the utterance itself: no name label, no headings, no stage directions, no commentary, and do not speak for others. To pass, output exactly "Skip" or exactly "Over".
```

**action.jinja**: `{{ action_rule_sentence }}`。マルチの ACTION 要求: aiwolf `Divine request. Output only the name of one player.` / panel・living `Investigation request. Choose {{ choose }} items to look into from the list below. Output only their titles, one per line.`

**vote 要求末尾** (マルチ): `Output only the {{ vote_target_kind }}.`

**notice.jinja** (マルチのみ。方式固有)
```
{{ period_name | capitalize }} {{ round_no }} has {{ 'started' if start else 'ended' }}.
{{ payload }}
This is a notice. Do not generate in-character dialogue. Reply only with "Acknowledged.".
```

**identity.jinja**
```
Name: {{ name }}
Age: {{ age }}
Gender: {{ gender }}
Personality: {{ personality }}
{{ private_seed_label }}: {{ private_seed_text }}
```

**setting.jinja**
```
aiwolf:  Werewolf, 5 players: 1 Seer, 1 Werewolf, 1 Possessed, 2 Villagers. Participants: {{ roster }}.
panel/living: {{ topic.title }}. {{ topic.context }} Participants: {{ roster }}. Each participant has a concern of their own, which the others do not know.
aiwolf: ... Participants: {{ roster }}. Each player's role is secret. + 役職ごとの 1 文 (role_sentences: Seer / Werewolf / Possessed (人狼側、占いでは human) / Villager) を箇条書き (2026-10-27)
Things that can be looked into (titles only): {{ card_titles }}
```

**common/prompts/hidden.jinja (`## Hidden information`)** (単体のみ。方式固有)
```
For the writer only. All options and the full text of every card are listed below so that you can write the whole transcript. The participants do NOT know them before the schedule above says so: do not let any option or card content appear in the talk before the round in which it is revealed.
{{ options_full }}
{{ cards_full }}
```

##### 6.3 文言の統制

- `scripts/verify_prompt_control.py` が、同一 setup_id について single と multi の全プロンプトを dry-run レンダし、共通ブロックの展開結果が**バイト一致**することを検証する。position は両方の文字列を並記して記録する。
- 語数・Over/Skip・通知・スケジュールの文言は rules.yml からしか書かない。テンプレートに数値や制約文をハードコードしない。
- Skip を抑制する文 (「新しいことがなければ Skip」等) は入れない (ナッジ禁止と整合)。

#### 7. プロンプト組み立て

##### 7.1 マルチ (席ごとに独立した会話履歴)

```
system:  role ("You are <name>, one of the participants in the discussion described below. You take part in it as <name> under the rules and the flow given, speaking only in your own turns.")
         + setting + structure + schedule + action + "## Your profile" + identity
user  :  TALK   = 席ビューの台本 (§7.4、ここまでに知っていること全部) + "\n- **<name>**:"   ← モデルは発話だけを書く
user  :  VOTE   = vote_request_sentence + "Candidates: …" + 空行 + 席ビューの台本 + "\n### Vote\n- <name> ->"
user  :  ACTION = action_request_sentence + 候補の箇条書き + 空行 + 席ビューの台本 + "\n### Action\n- divine: <name> ->" (attack / investigate も同形)
```

messages は毎回 `[system, user]` の 2 つだけ (chat 履歴を積まない。2026-10-27、§7.4)。通知 (INITIALIZE / DAILY_INITIALIZE /
DAILY_FINISH / FINISH) は席ビューを更新するだけで、サーバには静的な "Acknowledged." を返し、LLM は呼ばない。
Over した席には、そのラウンドの残りの TALK 要求を送らない。実装の細部は `docs/IMPLEMENTATION_NOTES.md`。

##### 7.4 台本文法と席ビュー (2026-10-27。大会出場と蒸留を見据えた決定)

両方式は **同じ台本文法** を使い、違いは「見える範囲」と「生成単位」だけにする (`common/transcript.py`)。

- **書き手ビュー** = 全知の台本 (単体の出力そのもの。§7.2 の出力形式)。
- **席ビュー** = 同じ文法で、その席が知っていることだけ。multi のエージェントは受け取ったパケットから席ビューを組み立て、
  毎回の user を「席ビュー + 自分の次の行のラベル」として渡す。`view_from_rows(rows, ctx, seat, upto_seq)` が共通ログから同じ文字列を
  復元でき、エージェントの user とバイト一致することをテストで保証する (tests/test_seat_view.py)。書き手ビューは単体変換器で同じ行に戻る。
- 席ビューの追加要素: 自分の行動行 (`- divine: Seer -> Target (human)` / `-> none`、`- attack: Wolf -> Target`、`- investigate: Name -> t1; t2` / `-> none`)、
  公開情報の行 (`- execution: Name | no one`、`- attacked: Name | no one`、前日の全投票)、discussion の `### Findings` (Round 2 開始時、本人の調査結果) と
  `### Options` (Round 3 開始時)。Participants 表は両ビューとも持たない (人物は system にある)。
- 開示時期は進行表どおり: 1 日目の朝は占い師の占い結果だけ、2 日目以降は前日の投票・処刑・襲撃。占い師が死亡していれば何も出ない。
- 理由: (1) 大会 (aiwolf-nlp-server) が決めるのは情報の流れと要求/応答の形だけで、エージェント内部の文脈表現は自由。ここで決めた
  席ビューがそのまま大会での学生モデルの入力形式になる。(2) 発話 k の直前の文脈が single ("…- **Kenji**: ") と multi で同じ局所形になり、
  hidden states の対応付けと蒸留データ (単体の台本を Python サーバに流して各席の席ビューを再構成) が形式差なしで作れる。
- 単体の台本に無く席ビューにだけあるもの (Findings / Options、他人の行動の公開結果) は全知性による必然の差として記録する。

##### 7.2 単体 (1回の呼び出し)

```
system: role ("You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given.")
        + setting + structure + schedule + action
        + 5席分の identity (席順、全員の非公開種)
        + hidden.jinja (選択肢・カード全文 + 先出し禁止。discussion ドメインのみ)
user  : "Write the complete transcript of the discussion in the exact Markdown format specified. Output only the transcript."
        + 出力形式
```

system / user の分け方と構成はマルチと同型にする (system = 役割文 "You are …" + ルール・進行 (共通 4 ブロック) + 人物、user = 今回の要求。2026-10-27 統制監査 A3)。方式で変わるのは役割文 (`common/prompts/role.jinja` に両方式の文を並記: 「参加者 <name> として参加する」か「登場人物とルール・進行を踏まえて書く書き手」か) と人物の数 (1 席か 5 席か) だけ。
`verify_prompt_control.py` は共通ブロックと identity が single の **system** にあり user に繰り返されないことも検証する。

出力 Markdown (変換器がパースする唯一の形式):

```
# {{ setup_id }}
## Participants
| Seat | Name | Role |            ← aiwolf のみ Role 列。panel/living は 2 列。表は setup との照合にのみ使う
## {{ Period }} {{ r }}
### Talk
#### Turn 1 of 4
- **Name**: text | Skip | Over
(Over した参加者はそのラウンドの以降のターンに行を書かない)
### Vote                           ← aiwolf Day ≥ 1、panel/living Round 3
- Name -> Target
- execution: Name                  ← aiwolf (役職は書かない。変換器が setup から補う)
- adopted: B                       ← panel/living
### Action                         ← 夜 / Round 1 の後
- divine: Seer -> Target (human|werewolf)
- attack: Wolf -> Target
- investigate: Name -> title1; title2
## Result
- winner: village | werewolves    |   - adopted: B
```

##### 7.3 共通 / 方式固有の対応表

| ブロック | single | multi | 判定 |
|---|---|---|---|
| identity / setting / structure / schedule / action / output_rules | 同文 | 同文 | **共通 (バイト一致を検証)** |
| position | 見出し `#### Turn t of 4` と `## Round r` | TALK 要求の1行 | 情報等価 (同じ文字列を含む) |
| notice (ROUND_START / END) | なし | あり | 方式固有 |
| 執筆者枠づけ / Markdown 構造指定 / hidden.jinja | あり | なし | 方式固有 |
| 非公開情報の見え方 | 全席分 | 自席分 | 方式固有 (研究テーマ) |
| 投票・行動の決定 | 全席分を一括で書く | 席ごとに要求 | 方式固有 (研究テーマ) |

#### 8. 違反会計 (両方式共通) とパース仕様

品質指標は**復元後の発話**で計算し、違反率は別表で報告する。復元不能で捨てた行は感度分析 (含む / 含まない) を付ける。

**両方式共通の違反コード**: `over_cap` (語数超過、記録のみ)、`name_label` (発話頭の名前ラベル、除去して復元)、`multi_utt` (1 応答に複数発話、先頭のみ採用)、`pass_punct` (`Over.` 等、正規化)、`trailing_over` (発話本文の末尾に `Over` / `Skip` が付く、記録のみ。本文は削らない)、`speak_for_others` (他者の発話を含む、記録のみ)、`format_noise` (見出し・ト書き、除去)、`early_reveal` (スケジュール前の選択肢名 (全名一致)・カード内容の言及、記録のみ)、`early_reveal_partial` (選択肢名の 5 文字以上の語 1 つ (ストップワード除く) の単語一致、記録のみ、粗い指標)、`truncated` (finish_reason=length)。

**単体のみ** (構造違反): `name_case` (復元)、`unknown_name` (捨てる)、`dup_turn` (同一ターン重複、先頭採用)、`talk_after_over` (Over 後の発話、捨てる)、`over_repeat` (Over の再記載、正規化)、`pass_after_over` (Over 後の `Skip` 行。書き手が残りターンを埋める癖で、捨てて正規化として記録)、`missing_turn` (Over していないのに行がない、記録)、`dead_actor` (死者の発話・投票、捨てる)、`order` (ターン内順序違い、復元)、`extra_round` (`## Day 4` 以降、捨てる)、`bad_card` (タイトル不一致、その席はカードなし)、`vote_count` (票数不足)、`tally_mismatch` (票から再計算した採択・処刑と書き手の値の不一致 (書き手の値が最多得票の候補でない)、再計算値で上書き)、`tie_choice_differs` (同票で、書き手の処刑・採択が最多得票の候補ではあるが共通タイブレーク規則の選択と異なる。**書き手の値を保って再生**し、execute / result 行に `tie:true` と `rule_choice:<規則の選択>` を付ける。規則で上書きすると以降の transcript が `dead_actor` / `missing_turn` の連鎖になるため)、`divine_mismatch` (占い結果と真役職の不一致、真値で上書き)。

**パース文法** (単体): 見出しは `## <Period> <int>`、`### Talk|Vote|Action`、`#### Turn <int> of 4`。発話は `- **<Name>**: <text>`。Vote は `- <Name> -> <Target>`、`- execution: <Name>`、`- adopted: <Label>`。Action は `- divine: <Name> -> <Name> (human|werewolf)`、`- attack: <Name> -> <Name>`、`- investigate: <Name> -> <title>; <title>`。Result は `- winner: village|werewolves` / `- adopted: <Label>`。

#### 9. 実装の順序

1. 雛形: `pyproject.toml`、`data/personas.yml`、3ドメインの `roles.yml` / `rules.yml`、2ドメインの `instances.json` (カード本文は移植元のまま、タイトルは §9-9 で付与)、`config/`。
2. `common/`: protocol、schema、logwriter、setup、tiebreak、render、violations、convert (single_markdown / aiwolf_go / legacy_resultjson)。テスト: 移植元の aiwolf CSV/JSON、result.json、単体 Markdown の往復。
3. `scripts/make_setups.py` と設定ファイル生成。
4. `common/prompts` の共通ブロックと両方式の組み立て、`verify_prompt_control.py`。
5. `server/base` + 3ドメイン。台本エージェント (LLM なし) で進行とログを検証。`compat_aiwolf_go.py` で Go サーバと突合。
6. `agent/base` + 3ドメイン (vLLM)。
7. `single/` (3ドメイン)。
8. パイロット (各ドメイン single / multi 2 局ずつ、dynamic と fixed の両方) → 文言・パース仕様の修正。
9. カードの書き直し (別作業、承認後)。**範囲は表現の調整のみ**: 本文を第三者視点に改め、タイトルを付与する。議題・選択肢・困りごとの数と内容、点数行列は変えない (panel の選択肢 4 もそのまま)。

#### 10. 未決事項

なし。

v0.2 の未決 1 点 (panel の選択肢 4 を living の 3 に揃えるか) は **4 のまま残す** で確定 (2026-10-26、ユーザ判断)。理由: 議題は選択肢込みで設計されており、候補削除は内容の再設計になる。ドメインは層別因子なので、ヘッダの `n_options` で層別し、投票系指標 (過半数到達率・票の割れ方) のドメイン間比較は主張しない。カード書き直しも表現の調整に留める (§9-9)。

v0.1 の他の 6 点は次で確定: 文言は §6.2 案 (パイロット後に見直し) / カード 2 枚・プール 10 枚 / position は情報等価 (1 始まり) / 天井はマルチ発話 1024・投票行動 64・単体 16384、`models.yml` で方式別、打ち切りは除外数として報告、vLLM の `max_model_len` ≥ プロンプト + 天井を確認 / N=30、10 の倍数 / aiwolf は `max_day: 3` を両方式のルール文に書き、整合性は §8 で検証。

#### 11. 指標の前提 (分析時の規則)

- 情報共有の分母は **(席, カード) 対**。dynamic では `n_unique_cards` を共変量にする。パイロットで fixed も回し、一意数の低下を数値で把握する。
- 統計の単位は setup (single と multi の対応のある比較)。インスタンスは変量効果。ドメインは層。
- 話者間の事実整合性 (肩書や設定の矛盾) は従属変数にしない (ペルソナに職業がないため)。
- 形式違反率と議論の質は別の表で報告する。

#### 12. 実装状況 (2026-10-27)

- 実装済み: §2 の全ディレクトリ。テスト 179 本。`verify_prompt_control.py --all` で 90 setup の共通ブロックがバイト一致、単体プロンプトにルール文の言い換えがないことも検証。
- パイロット: gemma-4-31B-it (vLLM) で 3ドメイン × single / multi を各 1 局。candidate_selection と shared_living は **fixed** モード (カードのタイトルが未作成のため dynamic は未実行、§9-9 待ち)。
- Go サーバとの互換テスト (`scripts/compat_aiwolf_go.py`) は同じ台本エージェントで実行し、想定内の差 (空応答後の扱い、`Over.` の扱い、日次シャッフル) 以外の差なし。
- 2026-10-27: §9-9 完了。200 枚にタイトルを付与、78 枚の本文を第三者視点に調整 (一人称の置換のみ、事実・数値・bearing は不変)。元の本文は instances.json の `text_source` に保持。下書き・検査記録・検査スクリプトは ../undergraduate_research_archive/2026-10-28_pre_pilot6/docs_control_audit_2026-10-27/card_rewrite_drafts/、反映は scripts/apply_card_rewrite.py。dynamic モードの dry-run が通る (check_dynamic_ready OK)。
- 2026-10-27 パイロット 3 (台本文法 §7.4、dynamic、gemma-4-31b、3 ドメイン × single/multi): 6 局とも正常終局。multi の全 TALK の user が ログ由来の席ビューとバイト一致 (167/167)。token id + logprob、sampling、model_info を記録。stop 境界が効き複数行の逸脱なし。末尾 "Over." は 5 件 (cs multi) で、正規化してラウンド離脱扱い。ログは log/ (前回は log/_pilot2)。
- 未実施: N=30 の本実験 (temperature 0.7) とプローブ用の greedy 対局。
- 2026-10-28 パイロット 4 (single, greedy, 3 ドメイン × 5 setup, log/_single_t0): 15/15 終局、繰り返し崩壊なし。議論 10 局中 7 局で選択肢内容語の先出し (書き手の全知性の現れ、記録)。全員 Over 後の埋め行は `pass_after_over` / `over_repeat` (正規化)。
- 2026-10-28 実験条件の実装 (§13): M1 (`--reveal`)、S-online (`--writer`)、筋書き (`scenarios/`, `--scenario`)、sampling の記録 (top_p / top_k、方式別 timeout)、`mentions` を素の名前で再定義 (発話者自身を除く)、`verify_prompt_control.py` が全条件の system を検証 (`--info-mode fixed` も)。テスト 196 本。未実施: 4 条件のパイロット (scratchpad pilot5)、筋書きの生成 (GPU)、評価、hidden states。

#### 13. 実験条件 (2026-10-28)

研究計画 (docs/paper_draft.md) の条件。差は **役割文・秘密情報の見せ方・筋書きの有無・生成単位** だけで、それ以外は §6〜§7 の共通部品。条件名は `common/conditions.py` の札で統一する (ユーザ決定 2026-10-28)。

| 軸 | 値 |
|---|---|
| method | `single` (LLM 1 つ) / `multi` (席ごとの LLM) |
| generation (single) | `batch` (台本全文を 1 回で) / `batch-stepped` (batch のプロンプトのまま、台本を自分の書きかけとして 1 行ずつ続ける。結末はサーバが決める) / `online` (進行に合わせて 1 行ずつ、台本は user に貼り直す) |
| information (multi) | `private` (自席の秘密のみ) / `public` (全員の秘密を全席に開示) |
| plan | なし / `process` / `outcome` / `outline` / `turn` (筋書きの種類と粒度。process 以外は public を含意) |

| 条件札 | 旧称 | 実行 | system | user (+ assistant) |
|---|---|---|---|---|
| `single-batch` | S0 | `run_single.py` | role(single) + 共通 4 ブロック + `## Participants` ×5 + `## Hidden information` | 台本全文の要求 + 出力形式 |
| `single-batch-stepped` | – | `run_multi.py --stepped` | single-batch と同一 | single-batch と同一の user + **assistant = 書き手ビュー + 札** (続き書き: vLLM `/tokenize` のトークン列 + `/v1/completions`)。TALK は次の要素で、票・行動は行末で停止 |
| `single-online` | S-online | `run_multi.py --writer` | role(online) + single-batch と同じ残り | **書き手ビュー** (全知の台本) + `- **X**:` |
| `multi-private` | M0 | `run_multi.py` | role(multi, X) + 共通 4 ブロック + `## Your profile` (自席) | 席ビュー + `- **X**:` |
| `multi-public` | M1 | `--reveal` | role(multi, X) + single-batch と同じ残り | 同上 |
| `<条件>-<plan>` | S1 / M2 | `--scenario auto --plan-granularity g` | 上 + `## Plan` (process は multi-private にも可: 自席の筋のみ) | 同上 |

比較の読み方: single-batch vs single-batch-stepped = 結末と構造の決め手 (書き手 vs サーバ) だけの差で、greedy なら発話はサーバが差し替えない限り同一 (分割自体は効かないことの実証)。single-batch-stepped vs single-online = プロンプトの目標 (全文か次の 1 行か) + 履歴の置き場 (assistant の続きか user の貼り直しか)。single-online vs multi-public = 1 つの文脈か席ごとの文脈か。multi-public vs multi-private = 情報量。

- game_id = `<setup>__<条件札>__<model_tag>__<ts>`、ログは `log/<domain>/<札 (plan 抜き)>/<game_id>/`。header: `method` (single/multi)、`pipeline` (`batch` = single/ の 1 回生成、`server` = server/ + agent/; single-online は server)、`condition` (札)、`axes` (4 軸)、`scenario` ({path, sha1, granularity, file_granularity})。2026-10-28 以前のログは `log/<domain>/single|multi/` (旧称)。
- 組み立ては `common.render.system_prompt(env, ctx, method, seat, reveal, scenario)` 1 本。single-batch と multi-public と single-online の system は**役割段落だけが違う** (verify が 90 setup で検証)。`## Hidden information` (`common/prompts/hidden.jinja`, 旧 `## For the writer only`) は議論ドメインの選択肢とカード全文。人狼の秘密は `## Participants` の役職行。
- 結末を含む筋書き (outcome / outline / turn) は結末が役職を含意するので public 条件にだけ与える。process (結末・選好・被疑者・選択肢を含まない) は multi-private にも与えられる (自席の筋のみ)。
- **single-online**: 5 席のクライアントを 1 プロセスのスレッドで動かし、`SeatTranscript(ctx, None)` を共有 (lock)。各席の非公開情報 (占い結果・襲撃・調査) は本人のスレッドが共有ビューへ書く (`upsert_action`)。票は各席の返答時に `add_vote` (サーバは VOTE / INVESTIGATE を**席順に逐次**問い合わせるので、ログの行順と一致)。処刑は夜の要求 (DIVINE / ATTACK の `info.executed_agent`) と翌朝、終局時は FINISH で確定。書き手ビューの意味論 = `view_from_rows(rows, ctx, None, upto_seq)`: 票・処刑・行動はその行が存在した時点で見え、占い結果だけは翌朝 (本人と同じ)。全 TALK / VOTE / ACTION の user がこれとバイト一致することをテスト (tests/test_conditions.py)。VOTE / ACTION のラベルは、その期間の節が既に開いていれば見出しを繰り返さない (`section_open`)。
- **筋書きの種類**: `process` = 各期間の公開の筋 (話題・論点・意見の傾き) と席ごとの立場の推移だけで、**票・処刑・採択・夜の行動・勝敗を含まない** (秘密も結末も含まないので multi-private にも渡せる。主系)。`outcome` = 票・処刑 (採択)・夜の行動・結末だけ。`outline` = process + outcome。`turn` = outline + 各ターン各席の発言要旨 (上限条件)。検証で公開の筋と席の筋に結末語 (executed / adopted / wins など) が無いことを確認する。
- **筋書き (plan)**: `scenarios/<domain>/<setup_id>.json`。`periods[]` に期間ごとの `public` (観察者の記述: 話題・誰が疑われるか・何が決まるか)、投票期間の `votes` と `executed` / `adopted`、人狼の `divine` / `attack`、turn 粒度では `turns[] = {turn, lines{name: 要旨 | Skip | Over}}`、`seats{name: 筋}`、`final`。ファイルは最も細かい粒度 (生成は `turn`) を 1 本だけ持ち、`scenario_view(sc, g)` が削って他の種類を派生する (process / outcome は outline から、outline は turn から)。`validate_scenario` がルールで再生して検証 (票 → 同票規則 → 処刑 → 勝敗、対象の生存、turn: 死者・Over 後の行なし、ターン数)。生成は `scripts/gen_scenarios.py` (single-batch の system + 計画要求 `scripts/prompts/scenario_request.jinja`、不合格は問題点を添えて再試行、試行は `.attempts.json`。**setup からのみ生成し、台本からは作らない。生成モデルと同じモデル・greedy**)。両方式とも `## Plan` を system の末尾に同文で置く (`common/prompts/scenario.jinja`)。進行は強制せず、`find_scenario_deviations(rows, ctx, plan)` が両方式共通で `scenario_deviation` (kind = deviation: 票・処刑・襲撃・占い先・勝敗/採択・期間の有無) を violations レコードに足す。
- decoding (§10 補足): 本体は greedy (`models.yml default: temperature 0`)、頑健性確認は Gemma 4 の generation_config と同じ `gemma_default` (1.0 / top-p 0.95 / top-k 64)。`sampling` に top_p / top_k を記録。chat template の thinking は既定で無効。timeout は方式別 (`timeout_s: {multi, single}`)。
- 2026-10-28 (v2 レビュー対応): `single-batch-stepped` と `process` 筋書きを追加 (上表)。条件札は `single-batch` / `single-batch-stepped` / `single-online` / `multi-private` / `multi-public` (+ `-process|-outcome|-outline|-turn`)。hidden states 取得は `scripts/extract_hidden.py` (記録済みプロンプトと生成トークンの再生、位置は札トークン (label) と生成直前のプロンプト末尾 (prompt)、token id / prompt_tokens の一致を検査)。旧パイロットのログは ../undergraduate_research_archive/2026-10-28_pre_pilot6/log_pilots/ に退避 (pilot3_t07, pilot4_single_greedy)、pilot 1・2 は削除。

#### 14. hidden states の取得 (2026-10-28)

- `scripts/extract_hidden.py` (vllm-server の venv: transformers 5.8 / torch)。記録済みの `prompt_token_ids` (vLLM `/tokenize` を生成時に呼んで保存) と生成トークン id から列を組み直すので、chat template の再現は不要 (vLLM の描画は HF テンプレートと system 末尾のスペース 1 トークン分ずれる)。single-batch は prompt + 応答トークン (teacher forcing)、single-batch-stepped は prompt + 書きかけ (そのまま `/v1/completions` に渡した列)、online / multi は prompt。
- 位置: `label` = 札 `- **X**:` の最終トークン (`**:`; batch と stepped では次の行の最初のトークンを予測する位置)、`prompt` = 生成プロンプト末尾 (`<channel|>`: Gemma 4 は thinking 無効でも空の思考チャネルが生成プロンプトに付く)。出力は `<game_id>.npz` (`h` [位置, 層, 5376], float16, 既定は 4 層おき + 最終層) と `.index.json`。
- 検査 (aiwolf_0001, 5 条件): prompt_token_ids の長さ = usage.prompt_tokens が全呼び出しで一致。**恒等性**: single-batch と single-batch-stepped の札位置の表現は、台本が同一な区間で全層 cos ≥ 0.9998 (bf16 の誤差)、分岐後は 0.85〜0.92 に低下。single-batch と single-online は同じ札トークンでも cos 0.6〜0.8 (プロンプトの目標と履歴の置き場所の差)。
- vLLM の greedy は決定的でない: single-batch と stepped は接頭辞のトークン列が同一でも、近接確率の反転 (logprob 差 0.1 未満) で数行以内に分岐する。サーバの正規化 (`Skip.` → `Skip`) と行の順序 (調査行は席順) でも分岐する。
- 2026-10-28 パイロット 5 の発見 (筋書き): 最初の process 筋書き 9 本は、公開の筋と席の筋に選択肢名・ラベル (「Option A emerges as the most stable choice」「supports the Study Commons」) や人狼の被疑者名が入っており、process 条件で先出し違反が増えた (candidate_selection_0003 の multi-private-process で 16 件)。これは「結末を含まない筋書き」の定義に反する。対処: `_validate_prose` を強化 (結末・選好の語、選択肢名・ラベル・議題素材に無い選択肢語、人狼では他の参加者名を公開の筋と席の筋で禁止; ターン行は対象外)、生成要求文も同じ規則に。9 本は再生成し、process 条件 18 局は回し直す。
- 2026-10-28 検閲 (docs/control_audit_2026-10-28/) への修正: (1) 選択肢ラベルの並べ替え: setup に `option_perm` (seed からの決定的な順列、既存 60 setup に移行追加)、`ctx.options()` は表示順に A, B, C … と付け直し `orig_label` を保持、header に `option_perm`。議論 42 局中 34 局で A が採択されたラベル順の偏りへの対処。(2) 名前照合が末尾の括弧 (`Shizue (werewolf)`) を許容 (stepped の占いが全て無効だった)。(3) サーバの投票・調査の問い合わせと行の順序を発話順に (batch の書き手の習慣に合わせ、stepped との分岐要因を減らす)。(4) `raw_differs` は端の空白を無視 (stepped の先頭スペース)。(5) header に vLLM 版・model_root・hf_revision・chat_template_sha1・config_sha1 (`common/llm_meta.py`)。(6) 筋書き生成の記録に messages・sampling・token id、空ターンの修復。(7) hidden states の index に `gen_point` (条件間比較はこの位置で行う: online / multi の札トークンは文末記号を予測する位置なので比較に使わない)。(8) 先出し検出の素材語に議題タイトルを追加。
- online → multi-public の段には、役割文と文脈の分割に加えて**他席の夜の行動・調査の可視性** (書き手ビューは全席の divine / attack / investigate 行を見る; multi-public の席ビューは自席分だけ) が含まれる。論文では「書き手 1 人の全知の文脈 vs 席ごとの文脈 (他席の動的な秘密は見えない)」として明記する。
- 2026-10-28 パイロット 6 (修正版、log/_pilot6、72 局 + 筋書き 9 本、`VLLM_BATCH_INVARIANT=1`、2 台): 72/72 終局。**single-batch の反復 2 回は 9/9 setup で全文一致** (バッチ不変モードで決定的)。stepped の占いは 3/3 有効。ビューのバイト一致 45/45 局、prompt_token_ids = usage.prompt_tokens 2730/2730。議論ドメインの採択ラベルは A/B/C/D に分散 (option_perm の効果)。process 条件の先出し違反は multi-private-process 合計 1 件 (第 1 ラウンドは 27 件)。batch と stepped: cs_0002 は全文一致、他 8 setup は 5〜26 行目で分岐。分岐の原因: (i) 同一接頭辞からの近接確率の反転 4 件 (logprob 差 ≤ 0.06、aiwolf_0003 は完全同値) — バッチ不変でも **prefill (stepped は接頭辞を再計算) と decode (batch は 1 トークンずつ) の数値経路が違う**ため。(ii) サーバの正規化 (`Skip.` → `Skip`) 1 件、(iii) 書き手の空行や全員 Over 後の構造をサーバが矯正 3 件。報告の形: 「反復は同一 (決定的)。batch と stepped の差は、近接確率の反転 (実装の数値解像度以下) とサーバの構造矯正に限られる」。


#### 15. multi-*-stepped: 全文の生成目標を席ごとの生成に移植する条件 (2026-10-29)

- 条件札 `multi-private-stepped` / `multi-public-stepped` (`common.conditions`、`-<plan>` も可)。席ごとの 5 プロセス (`python -m agent --seat N --seat-stepped`、`scripts/run_multi.py --seat-stepped [--reveal]`)。
- 各席: system = その席の参加者プロンプト (multi-private / multi-public と同一)、user = single-batch の書き手への要求 (`single/prompts/user.jinja` + 出力形式、single-batch-stepped と同一)、assistant = 自席ビューの台本 + 自分の札 (`- **X**:`)。`/tokenize` + `/v1/completions` の続き書き (single-batch-stepped と同じ経路) で、停止列は次の台本要素。モデルは他席の行まで書き続けうるが、サーバが受け取るのは自席の 1 行だけ。票・夜の行動も同じく自席ビューの札 (`- X ->`) の続き書き。
- 目的: 密度・譲りの差が「全文を 1 回で書く生成目標」によるものか、「1 人が全員分を書く (文脈の非分割)」によるものかを分ける。multi-private との差が目標の効果、single-batch-stepped との差が分割 (+ 情報) の効果。hidden states の gen_point (札トークン) は single-batch-stepped と同じ位置。
- 記録: llm_call に `continuation`, `prompt_ids`, `prefix_ids` (stepped と同形)。`scripts/extract_hidden.py` は kind = stepped として扱う。

#### 16. 議論例 (few-shot) の条件 (2026-10-30)

- 目的: 会話の前に議論例を与えると、生成目標を変えずに発話の長さ・密度・頭の中の長さの読み出しが変わるか。今日の結果 (履歴の文体が長さを決める) との対応を見る。
- 条件: single-batch と multi-online (multi-private) に、例を 3 本与える。短い例 = 同じモデルの single-batch の局、長い例 = 同じモデルの multi-online の局。どちらも同じドメインの別の設定から、設定名の順で最初の 3 本 (対象の設定自身は除く)。例なしは既存の本実行の局を使う。
- 入れ方 (common/examples.py、環境変数 UGR_EXAMPLES で有効化): manyshot-ablation の前置き文 (書式の注意の一文は除く) + 発話行だけの台本 3 本を、指示文の先頭に置く。single の書き手にも multi の各席にも同じ文面。manyshot-ablation の決まった返答と毎ターンの一言は入れない (案 A: 違いは例の有無だけ)。
- サーバ: 例で入力が伸びるので max-model-len を 32768 にした (本実行は 20480)。出力の上限は変えていない (single_full 16384)。温度 0 では上限に届かない限り出力は変わらない。
- ログ: log/fewshot/<model>__ex-<short|long>/ (局名の条件部分は single-batch / multi-private のまま、フォルダで区別)。例の文面は各通話の記録に指示文として残る。

### A.3 Model configuration (config/models.yml)

````yaml
# LLM endpoints and per-method technical ceilings (DESIGN §10: ceilings are safety limits, not instructions).
endpoints:
  local_vllm:
    base_url: http://localhost:8000/v1
    api_key_env: VLLM_API_KEY      # unused unless vLLM was started with --api-key
  local_vllm_b:                    # further instances of the same model on other GPUs (games are split across them)
    base_url: http://localhost:8010/v1   # 8001/8002 are taken by other services on this host
    api_key_env: VLLM_API_KEY
  local_vllm_c:
    base_url: http://localhost:8020/v1
    api_key_env: VLLM_API_KEY
  local_vllm_d:
    base_url: http://localhost:8030/v1
    api_key_env: VLLM_API_KEY
  local_vllm_e:
    base_url: http://localhost:8040/v1
    api_key_env: VLLM_API_KEY
  local_vllm_f:
    base_url: http://localhost:8050/v1
    api_key_env: VLLM_API_KEY
  local_vllm_g:                    # 7th / 8th instances (GPUs 6, 7)
    base_url: http://localhost:8070/v1
    api_key_env: VLLM_API_KEY
  local_vllm_h:
    base_url: http://localhost:8075/v1
    api_key_env: VLLM_API_KEY
  local_vllm_q:                    # smoke tests of a second model (port 8070)
    base_url: http://localhost:8070/v1
    api_key_env: VLLM_API_KEY
models:
  default:                         # main runs: greedy decoding (temperature 0; DESIGN §10 / paper_draft 付録 D)
    endpoint: local_vllm
    model: gemma-4-31b             # served-model-name of vLLM (google/gemma-4-31B-it); must be the same for single and multi
    temperature: 0
    top_p: null                    # null = the server's default
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:                     # per method (audit C4): the single call writes the whole transcript
      multi: 600
      single: 1800
    logprobs: true                 # record generated token ids + logprobs (vLLM) in every llm_call (DESIGN §3.2)
  default_b:                       # = default, served by the second instance (local_vllm_b)
    endpoint: local_vllm_b
    model: gemma-4-31b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  default_c:                       # = default, served by instance c (local_vllm_c)
    endpoint: local_vllm_c
    model: gemma-4-31b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  default_d:                       # = default, served by instance d (local_vllm_d)
    endpoint: local_vllm_d
    model: gemma-4-31b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  default_e:                       # = default, served by instance e (local_vllm_e)
    endpoint: local_vllm_e
    model: gemma-4-31b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  default_f:                       # = default, served by instance f (local_vllm_f)
    endpoint: local_vllm_f
    model: gemma-4-31b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen:                       # = default, served by instance d (local_vllm)
    endpoint: local_vllm
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen_b:                       # = default, served by instance d (local_vllm_b)
    endpoint: local_vllm_b
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen_c:                       # = default, served by instance d (local_vllm_c)
    endpoint: local_vllm_c
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen_d:                       # = qwen, instance d
    endpoint: local_vllm_d
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen_e:                       # = default, served by instance d (local_vllm_e)
    endpoint: local_vllm_e
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen_f:                       # = default, served by instance d (local_vllm_f)
    endpoint: local_vllm_f
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen_g:                       # = default, served by instance d (local_vllm_g)
    endpoint: local_vllm_g
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen_h:                       # = default, served by instance d (local_vllm_h)
    endpoint: local_vllm_h
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  qwen_smoke:                       # = default, served by instance d (local_vllm_q)
    endpoint: local_vllm_q
    model: qwen3.8-27b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  g12:                       # = default, served by instance d (local_vllm)
    endpoint: local_vllm
    model: gemma-4-12b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  g12_b:                       # = default, served by instance d (local_vllm_b)
    endpoint: local_vllm_b
    model: gemma-4-12b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  g12_c:                       # = default, served by instance d (local_vllm_c)
    endpoint: local_vllm_c
    model: gemma-4-12b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  g12_d:                       # gemma-4-12B-it (size variant), instance d
    endpoint: local_vllm_d
    model: gemma-4-12b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  g12_e:                       # = default, served by instance d (local_vllm_e)
    endpoint: local_vllm_e
    model: gemma-4-12b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  g12_f:                       # = default, served by instance d (local_vllm_f)
    endpoint: local_vllm_f
    model: gemma-4-12b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  default_g:                       # = default, served by instance d (local_vllm_g)
    endpoint: local_vllm_g
    model: gemma-4-31b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  default_h:                       # = default, served by instance d (local_vllm_h)
    endpoint: local_vllm_h
    model: gemma-4-31b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  g12_g:                       # gemma-4-12B-it (size variant), instance g
    endpoint: local_vllm_g
    model: gemma-4-12b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  g12_h:                       # gemma-4-12B-it (size variant), instance h
    endpoint: local_vllm_h
    model: gemma-4-12b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  mis:                       # Mistral-Small-3.2-24B (third model line), instance x
    endpoint: local_vllm
    model: mistral-small-3.2-24b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  mis_b:                       # Mistral-Small-3.2-24B (third model line), instance b
    endpoint: local_vllm_b
    model: mistral-small-3.2-24b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  mis_c:                       # Mistral-Small-3.2-24B (third model line), instance c
    endpoint: local_vllm_c
    model: mistral-small-3.2-24b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  mis_d:                       # Mistral-Small-3.2-24B (third model line), instance d
    endpoint: local_vllm_d
    model: mistral-small-3.2-24b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  mis_e:                       # Mistral-Small-3.2-24B (third model line), instance e
    endpoint: local_vllm_e
    model: mistral-small-3.2-24b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  mis_f:                       # Mistral-Small-3.2-24B (third model line), instance f
    endpoint: local_vllm_f
    model: mistral-small-3.2-24b
    temperature: 0
    top_p: null
    top_k: null
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
  gemma_default:                   # robustness runs: the model's own generation_config (Gemma 4: 1.0 / 0.95 / 64)
    endpoint: local_vllm
    model: gemma-4-31b
    temperature: 1.0
    top_p: 0.95
    top_k: 64
    max_tokens:
      multi_talk: 1024
      multi_vote: 64
      multi_action: 64
      single_full: 16384
    timeout_s:
      multi: 600
      single: 1800
    logprobs: true
````

### A.4 Server settings

- vLLM 0.21.1rc1, transformers 5.8.1, NVIDIA RTX PRO 6000 Blackwell (96 GB). Temperature 0 everywhere.
- gemma-4-31B-it: `VLLM_BATCH_INVARIANT=1` (identical outputs across batches and instances), max-model-len 20480 (32768 for the few-shot runs; output ceilings unchanged).
- Qwen3.8-27B: batch-invariant mode unsupported (linear attention); `--max-num-seqs 1 --no-enable-prefix-caching --default-chat-template-kwargs {"enable_thinking":false}`, every call of a setup on the same instance (`run_queue.py --pin-by-setup`); outputs identical within an instance (90/90 repeated games), not across instances.
- Judges: Llama 3.3 70B Instruct (bf16, tensor parallel 2) and gpt-oss-120b (MXFP4), temperature 0, families different from the generators.

Server start scripts used for the runs are kept under `log/stage_scripts/` (copies of the session's orchestration).

````bash
#!/usr/bin/env bash
# gemma-4-31B on GPU $1 port $2, batch-invariant
cd /diskthalys/ssd14ta/yharada/vllm-server
VLLM_BATCH_INVARIANT=1 MODEL=google/gemma-4-31B-it NAME=gemma-4-31b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--limit-mm-per-prompt {"image":0,"video":0}' setsid nohup ./start.sh > logs/ugr_gemma-4-31b_$(date +%Y%m%d_%H%M)_gpu$1.log 2>&1 < /dev/null &
echo started
````

````bash
#!/usr/bin/env bash
# Qwen3.8-27B (bf16) on GPU $1, port $2. No batch-invariant mode (unsupported for its linear attention); instead the
# batch is fixed at one sequence (--max-num-seqs 1) and prefix caching is off, so every request takes the same path.
# Thinking disabled by the server's default chat-template kwargs.
cd /diskthalys/ssd14ta/yharada/vllm-server
LOG=logs/ugr_qwen38_27b_$(date +%Y%m%d_%H%M)_gpu$1.log
TRITON_CACHE_AUTOTUNING=1 MODEL=Qwen/Qwen3.8-27B NAME=qwen3.8-27b GPUS=$1 PORT=$2 LEN=20480 BATCH=8192 UTIL=0.92 EXTRA='--max-num-seqs 1 --no-enable-prefix-caching --default-chat-template-kwargs {"enable_thinking":false}' setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
echo started "$LOG"
````

````bash
#!/usr/bin/env bash
# Llama 3.3 70B Instruct (bf16) on GPUs 1,2 (tensor parallel 2), port 8040, served-model-name llama-3.3-70b
cd /diskthalys/ssd14ta/yharada/vllm-server
LOG=logs/ugr_llama33_70b_$(date +%Y%m%d_%H%M).log
MODEL=meta-llama/Llama-3.3-70B-Instruct NAME=llama-3.3-70b GPUS=1,2 PORT=8040 LEN=32768 BATCH=8192 UTIL=0.90 setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
echo started "$LOG"
````

````bash
#!/usr/bin/env bash
# gpt-oss-120b (mxfp4) on GPU 0, port 8060, served-model-name gpt-oss-120b
cd /diskthalys/ssd14ta/yharada/vllm-server
LOG=logs/ugr_gptoss120b_$(date +%Y%m%d_%H%M).log
MODEL=openai/gpt-oss-120b NAME=gpt-oss-120b GPUS=4 PORT=8060 LEN=32768 BATCH=8192 UTIL=0.90 setsid nohup ./start.sh > "$LOG" 2>&1 < /dev/null &
echo started "$LOG"
````

## B. Prompts

### B.1 Templates (source)


#### `common/prompts/action.jinja`

````jinja
## {{ action_heading }}
{{ action_rule_sentence }}
````


#### `common/prompts/hidden.jinja`

````jinja
## Hidden information
The {{ option_noun }}s and the full text of every card are listed here. The participants do not know them before the schedule above says so, and nothing from them may appear in the talk before the round in which it is revealed.

{{ option_noun | capitalize }}s (see the schedule above):
{% for o in options %}
- {{ o.label }}: {{ o.name }}. {{ o.summary }}
{% endfor %}

{% if info_mode == 'dynamic' %}
Cards (see the schedule above; title: text):
{% for c in cards %}
- {{ c.title }}: {{ c.text }}
{% endfor %}
{% else %}
Cards given to each participant (see the schedule above):
{% for name, cs in fixed_cards %}
- {{ name }}:
{% for c in cs %}
  - {{ c.text }}
{% endfor %}
{% endfor %}
{% endif %}
````


#### `common/prompts/identity.jinja`

````jinja
Name: {{ name }}
Age: {{ age }}
Gender: {{ gender }}
Personality: {{ personality }}
{{ private_seed_label }}: {{ private_seed_text }}
````


#### `common/prompts/role.jinja`

````jinja
{% if method == 'multi' %}
You are {{ name }}, one of the participants in the discussion described below. You take part in it as {{ name }} under the rules and the flow given, speaking only in your own turns.
{% elif method == 'online' %}
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given, one line at a time: each time you are shown the discussion so far and write only its next line, for the participant named at the start of that line.
{% else %}
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given.
{% endif %}
````


#### `common/prompts/scenario.jinja`

````jinja
## Plan
The discussion follows this plan.
{% for p in plan_periods %}
- {{ Period }} {{ p.period }}: {{ p.text }}
{% for t in p.turns %}
  - Turn {{ t.turn }}: {{ t.text }}
{% endfor %}
{% endfor %}
{% if plan_final %}
- Outcome: {{ plan_final }}
{% endif %}
{% if plan_seats %}

Each participant's part:
{% for s in plan_seats %}
- {{ s.name }}: {{ s.text }}
{% endfor %}
{% endif %}
````


#### `common/prompts/schedule.jinja`

````jinja
## Schedule
| {{ schedule_table.columns | join(' | ') }} |
|{% for c in schedule_table.columns %}---|{% endfor %}

{% for row in schedule_table.rows %}
| {{ row | join(' | ') }} |
{% endfor %}
{% for n in schedule_notes %}
- {{ n }}
{% endfor %}
{{ vote_rule_sentence }} {{ end_sentence }}
````


#### `common/prompts/setting.jinja`

````jinja
## Setting
{{ setting_sentence }} Participants: {{ roster }}. {{ private_sentence }}
{% for r in role_sentences %}
- {{ r }}
{% endfor %}
{% if domain != 'aiwolf' and info_mode == 'dynamic' %}
Things that can be looked into (titles only):
{% for t in card_titles %}
- {{ t }}
{% endfor %}
{% endif %}
````


#### `common/prompts/structure.jinja`

````jinja
## Discussion format
The talk proceeds in {{ period_name }}s. Each {{ period_name }} has {{ turns_per_round }} turns; in each turn, every participant speaks once, in this fixed order: {{ speaking_order_names }}. On a turn, a participant either speaks, says "{{ pass_skip }}" (passes this turn only), or says "{{ pass_over }}" (takes no further turns this {{ period_name }}). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to {{ word_cap }} words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.
````


#### `single/prompts/format_aiwolf.jinja`

````jinja
## Output format
Markdown, exactly this structure; nothing before or after it:

# {{ setup_id }}
## Day 0
### Talk
#### Turn 1 of {{ turns_per_round }}
- **<Name>**: <utterance, or exactly {{ pass_skip }}, or exactly {{ pass_over }}>
(one line per living participant, in the fixed speaking order; repeat for Turn 2, 3 and 4; a participant who said {{ pass_over }} has no line in the later turns of that day)
### Action
- divine: <Seer's name> -> <target name> (human|werewolf)
## Day 1
### Talk
(4 turns as above)
### Vote
- <voter name> -> <target name>
(one line per living participant)
- execution: <name of the player with the most votes>
### Action
- divine: <Seer's name> -> <target name> (human|werewolf)
- attack: <Werewolf's name> -> <target name>
(continue with ## Day 2 and so on in the same way until the game ends)
## Result
- winner: village|werewolves

Constraints on the content: dead players have no further lines. The divine result must match the target's true role. Write ## Result right after the deciding Vote or Action and nothing else.
````


#### `single/prompts/format_discussion.jinja`

````jinja
## Output format
Markdown, exactly this structure; nothing before or after it:

# {{ setup_id }}
## Round 1
### Talk
#### Turn 1 of {{ turns_per_round }}
- **<Name>**: <utterance, or exactly {{ pass_skip }}, or exactly {{ pass_over }}>
(one line per participant, in the fixed speaking order; repeat for Turn 2, 3 and 4; a participant who said {{ pass_over }} has no line in the later turns of that round)
{% if info_mode == 'dynamic' %}
### Action
- investigate: <Name> -> <card title>; <card title>
(one line per participant; titles exactly as listed)
{% endif %}
## Round 2
### Talk
(4 turns as above)
## Round 3
### Talk
(4 turns as above)
### Vote
- <voter name> -> <{{ option_noun }} label>
(one line per participant)
- adopted: <label of the {{ option_noun }} with the most votes>
## Result
- adopted: <label>
````


#### `single/prompts/user.jinja`

````jinja
Write the complete transcript of the discussion in the exact Markdown format specified. Output only the transcript.

{{ format_spec }}
````


#### `agent/prompts/action_request.jinja`

````jinja
{{ action_request_sentence }}
{% for c in candidates %}
- {{ c }}
{% endfor %}
````


#### `agent/prompts/vote_request.jinja`

````jinja
{{ vote_request_sentence }}
Candidates: {{ candidates | join(', ') }}
````


#### `scripts/prompts/scenario_request.jinja`

````jinja
Before any line of the discussion is written, plan it. Decide how the whole discussion goes and what each participant does, consistently with the rules, the schedule and the participants above, and write the plan as one JSON object with exactly these keys:

- "periods": a list with one object per {{ period_name }}, in order{% if aiwolf %} ({{ Period }} 0, {{ Period }} 1, ... until the game ends){% else %} ({{ Period }} {{ first_round }} to {{ Period }} {{ rounds_total }}){% endif %}. Each object has:
  - "period": the number;
  - "public": one to three sentences on how the talk goes: the topics raised, the criteria and concerns weighed, what kind of information is shared, how views move in general terms. Describe the *process* only: no outcome and no preference for a named target. Do not name {% if aiwolf %}any player as suspected, accused, trusted or targeted, and do not mention roles, role claims or divinations (who claims what and when is decided in the talk){% else %}any {{ option_noun }} (neither its name nor its label), nor say which one is favoured or rejected{% endif %}; do not state the vote result, who is executed or what is adopted, or who wins (those go in the fields below);
{% if aiwolf %}
  - "votes" ({{ Period }} 1 and after): an object mapping every living player to the player they vote for;
  - "executed": the player with the most votes (if tied, leave the tie to the rule: write the one you intend);
  - "divine": the player the Seer divines that night (while the Seer lives);
  - "attack" ({{ Period }} 1 and after, while the game goes on): the player the Werewolf attacks that night.
{% else %}
  - "votes" ({{ Period }} {{ rounds_total }} only): an object mapping every participant to the label of the {{ option_noun }} they vote for;
  - "adopted" ({{ Period }} {{ rounds_total }} only): the label with the most votes.
{% endif %}
{% if granularity == 'turn' %}
  - "turns": a list with one object per turn of the talk, in order: {"turn": t, "lines": {participant: the gist of their line in one short sentence, or exactly "{{ pass_skip }}" or "{{ pass_over }}"}}. Only living participants have lines; a participant who said "{{ pass_over }}" has no later line in that {{ period_name }}; at most {{ turns_per_round }} turns.
{% endif %}
- "seats": an object with one entry per participant ({{ names | join(', ') }}): one or two sentences on what they care about, how they argue and how their view changes over the discussion. Same rule as "public": no {% if aiwolf %}other player's name{% else %}{{ option_noun }} name or label{% endif %}, no preference for a named target, no vote result{% if aiwolf %}, no night targets{% endif %}.
- "final": {% if aiwolf %}{"winner": "VILLAGE" or "WEREWOLF"}, as follows from the plan{% else %}{"adopted": the label with the most votes}{% endif %}.

Write the plan as an observer would describe the discussion: say what is argued and decided, not the wording of the lines. Do not write the discussion itself. Output only the JSON object.
{% if problems %}

Your previous plan had these problems; write a corrected plan:
{% for p in problems %}
- {{ p }}
{% endfor %}
{% endif %}
````


Prompt assembly: `common/render.py` (`system_prompt`: role + shared blocks + participants/hidden information or the seat's own profile + plan block), `single/base/prompt.py` (`build_messages`), `agent/base/prompts.py` (`build_system_prompt`, `build_talk_message`), `agent/base/seat.py` (stepped seats: the participant's system prompt + the single-batch request + the seat's own transcript continued as the assistant's output, stopped at the next line label), `common/examples.py` (the few-shot block).

````python
def system_prompt(env: Environment, ctx: GameContext, method: str, seat: int | None = None,
                  reveal: bool = False, scenario: dict[str, Any] | None = None) -> str:
    """The whole system prompt of any condition (DESIGN §7.1 / §13):

    role (method: multi | online | single) + the shared blocks + (reveal: ## Participants x5 + ## Hidden
    information | own ## Your profile) + (scenario: ## Plan). ``single`` always reveals. The conditions
    differ only in the role paragraph and in reveal / scenario."""
    if method not in ROLE_METHODS:
        raise ValueError(f"method {method!r} not in {ROLE_METHODS}")
    if method == "single":
        reveal = True
    parts = [role_block(env, ctx, method, seat)] + [shared_block(env, ctx, b) for b in SHARED_BLOCKS]
    if reveal:
        parts.append(participants_block(env, ctx))
        h = hidden_block(env, ctx)
        if h:
            parts.append(h)
    else:
        if seat is None:
            raise ValueError("seat is required without reveal")
        parts.append(PROFILE_HEADING + "\n" + identity_block(env, ctx, seat))
    if scenario is not None:
        parts.append(scenario_block(env, ctx, scenario, None if reveal else [int(seat)]))
    from .examples import examples_block  # the few-shot conditions (UGR_EXAMPLES; common/examples.py)
    ex = examples_block(ctx.domain, ctx.setup.setup_id)
    text = "\n\n".join(parts)
    return text if ex is None else ex + "\n\n---\n\n" + text


def identity_block(env: Environment, ctx: GameContext, seat: int) -> str:
    name = ctx.name_of_seat(seat)
    p = ctx.persona_of_name(name)
    role = ctx.role_of_seat(seat)
    if ctx.domain == "aiwolf":
        seed_text = role.capitalize()
    else:
        seed_text = ctx.problem_of_seat(seat)
    return shared_block(env, ctx, "identity", name=p.name, age=p.age, gender=p.gender,
                        personality=p.personality, private_seed_text=seed_text)
````

### B.2 Rendered prompts (Werewolf aiwolf_0001, gemma-4-31B, recorded)


#### シングル・全文 (single-batch): the whole-script request

_Recorded call: `log/main_gemma31b/aiwolf/single-batch/aiwolf_0001__single-batch__gemma-4-31b__20261028T155745/aiwolf_0001__single-batch__gemma-4-31b__20261028T155745.jsonl`, seat writer, request FULL, round None, turn None._

**system**

````
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given.

## Setting
This is a game of Werewolf with 5 players: 1 Seer, 1 Werewolf, 1 Possessed, and 2 Villagers. Participants: Kenji, Mizuki, Benjamin, Shizue and Minako. Each player's role is secret.
- Seer: a human who divines one player each night and learns whether that player is human or a werewolf.
- Werewolf: attacks one player each night from day 1 on.
- Possessed: a human who sides with the werewolf and wins when the werewolf wins; divination shows the Possessed as human.
- Villager: a human with no special ability.

## Discussion format
The talk proceeds in days. Each day has 4 turns; in each turn, every participant speaks once, in this fixed order: Minako, Shizue, Mizuki, Benjamin and Kenji. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this day). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Day | Start of the day | Talk | End of the day | Night |
|---|---|---|---|---|
| 0 | nothing | 4 turns | no vote | the Seer divines one other living player; no attack |
| 1 | the Seer is told the result of the night-0 divination (the Seer only) | 4 turns | every living player votes; the player with the most votes is executed | the Seer divines one other living player; the Werewolf attacks one other living player |
| 2 and after | everyone is told who was executed, who was attacked and all the votes of the previous day; the Seer is told the result of the previous night's divination (the Seer only) | 4 turns | vote and execution as on day 1 | divination and attack as on day 1 |
- A divination tells whether the chosen player is human or a werewolf. If the Seer is dead, there is no divination.
- Executed and attacked players are dead from the next day on.
A player may vote for themselves. If votes are tied, one of the tied players is chosen by a fixed rule. The village wins when the werewolf is executed. The werewolf wins when the number of werewolves is at least the number of living humans. The game ends as soon as one side has won.

## Night actions
At night, the Seer chooses one other living player to divine. From day 1 on, the werewolf chooses one other living player to attack.

## Participants
Name: Kenji
Age: 12
Gender: male
Personality: Kenji is curious and actively takes on challenges. He values his friends and enjoys communicating with those around him. Although he can be a little clumsy at times, he is always positive and never abandons those in need. He is easygoing and well-liked by those around him.
Role: Possessed

Name: Mizuki
Age: 24
Gender: female
Personality: Mizuki is a very confident woman who is often relied upon by those around her. She is calm and logical in her thinking and is good at observing people. As a result, she always makes calm judgments and chooses her actions according to the situation around her. Although she may sometimes come across as a little aloof, she is actually very caring and cannot ignore those who are weak. While she is relied upon by those around her and occasionally asserts her opinions strongly, she also possesses a kindness that considers others.
Role: Villager

Name: Benjamin
Age: 28
Gender: male
Personality: Benjamin is an intelligent and calm person. He is able to think calmly and rationally, and even in emotional situations, he places importance on logic. In public, he is elegant and polite, often incorporating sarcasm and humor into his conversations, but he is skilled at doing so without hurting others, creating a harmonious atmosphere. He also has an introverted side, often engrossed in deep thought, and occasionally keeps his distance from those around him. However, his calmness and knowledge are factors that earn him the trust of others even in difficult situations.
Role: Seer

Name: Shizue
Age: 78
Gender: female
Personality: Shizue has a very calm and gentle personality. Even as she has grown older, she continues to smile warmly at those around her and is a very caring person. She is always considerate of others, friendly, and sometimes shows a playful side. She often reaches out to those who are feeling down with kind words and never hesitates to lend a helping hand when needed, which has earned her the affection of many people in the village and community. Through her years of life experience, Shizue has come to understand the importance of living peacefully with others.
Role: Werewolf

Name: Minako
Age: 28
Gender: female
Personality: Minako is very calm and acts calmly in any situation. Even when those around her are emotional, she grasps the facts firmly and responds calmly. As a result, she is often asked for her opinion and often takes on a leadership role. She rarely shows her emotions, but she also has a kind side that she shows to those she trusts. She can be a little stubborn and is strong in her convictions. She is also confident in her physical strength and never neglects her training.
Role: Villager
````

**user**

````
Write the complete transcript of the discussion in the exact Markdown format specified. Output only the transcript.

## Output format
Markdown, exactly this structure; nothing before or after it:

# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **<Name>**: <utterance, or exactly Skip, or exactly Over>
(one line per living participant, in the fixed speaking order; repeat for Turn 2, 3 and 4; a participant who said Over has no line in the later turns of that day)
### Action
- divine: <Seer's name> -> <target name> (human|werewolf)
## Day 1
### Talk
(4 turns as above)
### Vote
- <voter name> -> <target name>
(one line per living participant)
- execution: <name of the player with the most votes>
### Action
- divine: <Seer's name> -> <target name> (human|werewolf)
- attack: <Werewolf's name> -> <target name>
(continue with ## Day 2 and so on in the same way until the game ends)
## Result
- winner: village|werewolves

Constraints on the content: dead players have no further lines. The divine result must match the target's true role. Write ## Result right after the deciding Vote or Action and nothing else.
````

**model output (recorded)**

````
# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Let's start by observing everyone's behavior. Since it's the first day, we have no information.
- **Shizue**: It is a pleasure to be with you all. Let's try to find the werewolf together, gently.
- **Mizuki**: I agree. We should look for any contradictions in our statements as the days progress.
- **Benjamin**: A logical approach is best. I shall be observing the nuances of your speech.
- **Kenji**: This is exciting! I'll do my best to help the village!
#### Turn 2 of 4
- **Minako**: Does anyone have a strategy they'd like to propose for the voting process?
- **Shizue**: Perhaps we can just talk and see who feels the most uneasy?
- **Mizuki**: That's a bit too subjective, Shizue. We need more concrete evidence.
- **Benjamin**: Indeed. Though on Day 0, we are essentially guessing. I'll pass for now.
- **Kenji**: I'm just going to follow what the smart people say!
#### Turn 3 of 4
- **Minako**: Skip.
- **Shizue**: Skip.
- **Mizuki**: Skip.
- **Benjamin**: Skip.
- **Kenji**: Skip.
#### Turn 4 of 4
- **Minako**: Over.
- **Shizue**: Over.
- **Mizuki**: Over.
- **Benjamin**: Over.
- **Kenji**: Over.
### Action
- divine: Benjamin -> Shizue (werewolf)
## Day 1
### Talk
#### Turn 1 of 4
- **Minako**: We have no deaths yet, but we must vote today. Does anyone have any leads?
- **Shizue**: I feel we are all such lovely people. It's hard to imagine a werewolf among us.
- **Mizuki**: @Shizue, your kindness is appreciated, but we must be vigilant.
- **Benjamin**: I have some information. Shizue, I'm afraid you are the werewolf.
- **Kenji**: What?! Benjamin, are you sure? That's a huge claim!
#### Turn 2 of 4
- **Minako**: @Benjamin, are you claiming to be the Seer?
- **Shizue**: Oh dear, Benjamin. I assure you, I am just a humble old woman.
- **Mizuki**: If Benjamin is the Seer, the logic is simple. We execute Shizue.
- **Benjamin**: I am indeed the Seer. My divination was clear.
- **Kenji**: But Shizue is so nice! Maybe the Seer made a mistake?
#### Turn 3 of 4
- **Minako**: The Seer doesn't make mistakes in this game, Kenji.
- **Shizue**: It is a very sad misunderstanding, but I cannot force you to believe me.
- **Mizuki**: The evidence provided by the Seer is the most reliable tool we have.
- **Benjamin**: I stand by my result. Shizue is the werewolf.
- **Kenji**: I guess I have to trust the Seer, even if it feels wrong.
#### Turn 4 of 4
- **Minako**: I'm convinced. Let's vote for Shizue.
- **Shizue**: I hope you all find peace.
- **Mizuki**: I agree. Shizue it is.
- **Benjamin**: Let us proceed with the execution.
- **Kenji**: Okay, I'll vote with everyone else.
### Vote
- Minako -> Shizue
- Shizue -> Shizue
- Mizuki -> Shizue
- Benjamin -> Shizue
- Kenji -> Shizue
- execution: Shizue
## Result
- winner: village
````


#### シングル・1 発話 (single-online): the writer's next-line request, first turn

_Recorded call: `log/main_gemma31b/aiwolf/single-online/aiwolf_0001__single-online__gemma-4-31b__20261028T173341/aiwolf_0001__single-online__gemma-4-31b__20261028T173341.jsonl`, seat 5, request TALK, round 0, turn 1._

**system**

````
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given, one line at a time: each time you are shown the discussion so far and write only its next line, for the participant named at the start of that line.

## Setting
This is a game of Werewolf with 5 players: 1 Seer, 1 Werewolf, 1 Possessed, and 2 Villagers. Participants: Kenji, Mizuki, Benjamin, Shizue and Minako. Each player's role is secret.
- Seer: a human who divines one player each night and learns whether that player is human or a werewolf.
- Werewolf: attacks one player each night from day 1 on.
- Possessed: a human who sides with the werewolf and wins when the werewolf wins; divination shows the Possessed as human.
- Villager: a human with no special ability.

## Discussion format
The talk proceeds in days. Each day has 4 turns; in each turn, every participant speaks once, in this fixed order: Minako, Shizue, Mizuki, Benjamin and Kenji. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this day). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Day | Start of the day | Talk | End of the day | Night |
|---|---|---|---|---|
| 0 | nothing | 4 turns | no vote | the Seer divines one other living player; no attack |
| 1 | the Seer is told the result of the night-0 divination (the Seer only) | 4 turns | every living player votes; the player with the most votes is executed | the Seer divines one other living player; the Werewolf attacks one other living player |
| 2 and after | everyone is told who was executed, who was attacked and all the votes of the previous day; the Seer is told the result of the previous night's divination (the Seer only) | 4 turns | vote and execution as on day 1 | divination and attack as on day 1 |
- A divination tells whether the chosen player is human or a werewolf. If the Seer is dead, there is no divination.
- Executed and attacked players are dead from the next day on.
A player may vote for themselves. If votes are tied, one of the tied players is chosen by a fixed rule. The village wins when the werewolf is executed. The werewolf wins when the number of werewolves is at least the number of living humans. The game ends as soon as one side has won.

## Night actions
At night, the Seer chooses one other living player to divine. From day 1 on, the werewolf chooses one other living player to attack.

## Participants
Name: Kenji
Age: 12
Gender: male
Personality: Kenji is curious and actively takes on challenges. He values his friends and enjoys communicating with those around him. Although he can be a little clumsy at times, he is always positive and never abandons those in need. He is easygoing and well-liked by those around him.
Role: Possessed

Name: Mizuki
Age: 24
Gender: female
Personality: Mizuki is a very confident woman who is often relied upon by those around her. She is calm and logical in her thinking and is good at observing people. As a result, she always makes calm judgments and chooses her actions according to the situation around her. Although she may sometimes come across as a little aloof, she is actually very caring and cannot ignore those who are weak. While she is relied upon by those around her and occasionally asserts her opinions strongly, she also possesses a kindness that considers others.
Role: Villager

Name: Benjamin
Age: 28
Gender: male
Personality: Benjamin is an intelligent and calm person. He is able to think calmly and rationally, and even in emotional situations, he places importance on logic. In public, he is elegant and polite, often incorporating sarcasm and humor into his conversations, but he is skilled at doing so without hurting others, creating a harmonious atmosphere. He also has an introverted side, often engrossed in deep thought, and occasionally keeps his distance from those around him. However, his calmness and knowledge are factors that earn him the trust of others even in difficult situations.
Role: Seer

Name: Shizue
Age: 78
Gender: female
Personality: Shizue has a very calm and gentle personality. Even as she has grown older, she continues to smile warmly at those around her and is a very caring person. She is always considerate of others, friendly, and sometimes shows a playful side. She often reaches out to those who are feeling down with kind words and never hesitates to lend a helping hand when needed, which has earned her the affection of many people in the village and community. Through her years of life experience, Shizue has come to understand the importance of living peacefully with others.
Role: Werewolf

Name: Minako
Age: 28
Gender: female
Personality: Minako is very calm and acts calmly in any situation. Even when those around her are emotional, she grasps the facts firmly and responds calmly. As a result, she is often asked for her opinion and often takes on a leadership role. She rarely shows her emotions, but she also has a kind side that she shows to those she trusts. She can be a little stubborn and is strong in her convictions. She is also confident in her physical strength and never neglects her training.
Role: Villager
````

**user**

````
# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**:
````

**model output (recorded)**

````
Since it's the first day, let's start by getting a feel for everyone. Does anyone have any initial thoughts or strategies they'd like to share?
````


#### マルチ・1 発話 (multi-private): a seat, first turn

_Recorded call: `log/main_gemma31b/aiwolf/multi-private/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543.jsonl`, seat 5, request TALK, round 0, turn 1._

**system**

````
You are Minako, one of the participants in the discussion described below. You take part in it as Minako under the rules and the flow given, speaking only in your own turns.

## Setting
This is a game of Werewolf with 5 players: 1 Seer, 1 Werewolf, 1 Possessed, and 2 Villagers. Participants: Kenji, Mizuki, Benjamin, Shizue and Minako. Each player's role is secret.
- Seer: a human who divines one player each night and learns whether that player is human or a werewolf.
- Werewolf: attacks one player each night from day 1 on.
- Possessed: a human who sides with the werewolf and wins when the werewolf wins; divination shows the Possessed as human.
- Villager: a human with no special ability.

## Discussion format
The talk proceeds in days. Each day has 4 turns; in each turn, every participant speaks once, in this fixed order: Minako, Shizue, Mizuki, Benjamin and Kenji. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this day). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Day | Start of the day | Talk | End of the day | Night |
|---|---|---|---|---|
| 0 | nothing | 4 turns | no vote | the Seer divines one other living player; no attack |
| 1 | the Seer is told the result of the night-0 divination (the Seer only) | 4 turns | every living player votes; the player with the most votes is executed | the Seer divines one other living player; the Werewolf attacks one other living player |
| 2 and after | everyone is told who was executed, who was attacked and all the votes of the previous day; the Seer is told the result of the previous night's divination (the Seer only) | 4 turns | vote and execution as on day 1 | divination and attack as on day 1 |
- A divination tells whether the chosen player is human or a werewolf. If the Seer is dead, there is no divination.
- Executed and attacked players are dead from the next day on.
A player may vote for themselves. If votes are tied, one of the tied players is chosen by a fixed rule. The village wins when the werewolf is executed. The werewolf wins when the number of werewolves is at least the number of living humans. The game ends as soon as one side has won.

## Night actions
At night, the Seer chooses one other living player to divine. From day 1 on, the werewolf chooses one other living player to attack.

## Your profile
Name: Minako
Age: 28
Gender: female
Personality: Minako is very calm and acts calmly in any situation. Even when those around her are emotional, she grasps the facts firmly and responds calmly. As a result, she is often asked for her opinion and often takes on a leadership role. She rarely shows her emotions, but she also has a kind side that she shows to those she trusts. She can be a little stubborn and is strong in her convictions. She is also confident in her physical strength and never neglects her training.
Role: Villager
````

**user**

````
# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**:
````

**model output (recorded)**

````
Since this is the first day, we have no information yet. Let's use this time to observe everyone's behavior. Does anyone have any initial thoughts or strategies they would like to share?
````


#### マルチ・1 発話 (multi-private): the same seat later in the game (transcript format)

_Recorded call: `log/main_gemma31b/aiwolf/multi-private/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543.jsonl`, seat 1, request TALK, round 1, turn 1._

**user**

````
# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Since this is the first day, we have no information yet. Let's use this time to observe everyone's behavior. Does anyone have any initial thoughts or strategies they would like to share?
- **Shizue**: That sounds like a wonderful idea, Minako dear. Let us all be patient and kind to one another as we figure this out. I am looking forward to our conversation.
- **Mizuki**: I agree with Minako. Since we have no clues yet, we should focus on how everyone reacts to the pressure. Let's keep the conversation open and see who tries to steer the narrative too early.
- **Benjamin**: A very sensible approach, Mizuki. I shall happily play the role of the observer for now. Let us see whose mask slips first while we maintain this delightful civility, shall we?
- **Kenji**: I'm excited to play! I agree with everyone. Let's just talk and get to know each other better. I'll do my best to help us find the werewolf!
#### Turn 2 of 4
- **Minako**: It seems we are all in agreement for now. Since we are observing, I'm curious if anyone has a specific method for identifying the werewolf or the possessed. @Kenji, you seem eager; do you have a plan?
- **Shizue**: It is lovely to see such enthusiasm in Kenji. I believe that by listening to the warmth and sincerity in each other's voices, the truth will naturally reveal itself to us in time.
- **Mizuki**: Sincerity is a start, Shizue, but logic is more reliable. I'll be looking for contradictions in statements and those who are overly eager to deflect suspicion. Let's see if anyone's "warmth" feels forced.
- **Benjamin**: Logic is indeed a sturdy shield, Mizuki. However, the most cunning wolves often dress their lies in the finest logic. I shall be watching for the gaps between what is said and what is intended.
- **Kenji**: @Minako, I don't have a super fancy plan, but I'll just be honest and friendly! I think if we all trust each other, we can figure it out together. I'm just happy to be here!
#### Turn 3 of 4
- **Minako**: Honesty is a good starting point, Kenji, but we must remember that the werewolf and the possessed will also try to appear honest. Let's remain vigilant while we maintain this cooperation.
- **Shizue**: Minako is quite right to remind us. It is a delicate balance, isn't it? We must keep our hearts open while remaining mindful. I trust that we can all find a way through this together.
- **Mizuki**: Exactly. Trust is a luxury we can't fully afford yet. I'll be paying close attention to who agrees with whom too quickly. Sometimes, the Possessed tries too hard to blend in by mirroring others.
- **Benjamin**: A keen observation, Mizuki. The art of mirroring is a classic deception. I wonder if we shall see any such echoes in our discourse, or perhaps someone attempting to lead the choir too enthusiastically.
- **Kenji**: @Mizuki, mirroring? That sounds like a cool detective trick! I'll try to be myself and not just copy people. I really want us all to get along, though!
#### Turn 4 of 4
- **Minako**: Since we have established our general approach, let's conclude today's discussion. We will have more concrete information tomorrow once the Seer has had their first divination. Until then, let's stay observant.
- **Minako**: Over
- **Shizue**: It has been a lovely first day of getting to know you all. I shall wish everyone a peaceful night's sleep. Please take care of yourselves.
- **Shizue**: Over
- **Mizuki**: I'll be watching closely tomorrow. Let's see if the Seer's information brings the truth to light or if the wolf tries to muddy the waters. Goodnight, everyone.
- **Mizuki**: Over
- **Benjamin**: A peaceful night indeed, Shizue. I shall retire now to seek a glimpse of the truth. I look forward to seeing how our theories hold up against the reality of tomorrow. Goodnight, all.
- **Benjamin**: Over
- **Kenji**: Goodnight everyone! I hope we all have sweet dreams and that the Seer finds something helpful tonight. I'll see you all tomorrow!
- **Kenji**: Over
## Day 1
### Talk
#### Turn 1 of 4
- **Minako**: Good morning, everyone. The first night has passed. Since the Seer now has their first piece of information, I would like to hear if anyone is willing to share their findings or if they have noticed anything suspicious.
- **Shizue**: Good morning, everyone. I hope you all slept well. I wonder if our kind Seer has found any clues to help us? Please, take your time and share only what you feel is right.
- **Mizuki**: If the Seer is among us and feels it's safe, now is the time to speak. However, revealing yourself too early can be risky. @Seer, do you have information that can guide us without compromising your safety?
- **Benjamin**: It is a delicate dance, is it not? To speak is to invite the wolf's appetite, yet to remain silent is to let the shadows grow. I shall be cautious, but I can confirm that Kenji is human.
- **Kenji**:
````

**model output (recorded)**

````
@Benjamin, wow, thank you for saying that! That makes me feel much better. I'm really glad you trust me! Does that mean you're the Seer, or did you just have a good feeling about me?
````


#### Omniscient seat (multi-public): first turn

_Recorded call: `log/main_gemma31b/aiwolf/multi-public/aiwolf_0001__multi-public__gemma-4-31b__20261028T180317/aiwolf_0001__multi-public__gemma-4-31b__20261028T180317.jsonl`, seat 5, request TALK, round 0, turn 1._

**system**

````
You are Minako, one of the participants in the discussion described below. You take part in it as Minako under the rules and the flow given, speaking only in your own turns.

## Setting
This is a game of Werewolf with 5 players: 1 Seer, 1 Werewolf, 1 Possessed, and 2 Villagers. Participants: Kenji, Mizuki, Benjamin, Shizue and Minako. Each player's role is secret.
- Seer: a human who divines one player each night and learns whether that player is human or a werewolf.
- Werewolf: attacks one player each night from day 1 on.
- Possessed: a human who sides with the werewolf and wins when the werewolf wins; divination shows the Possessed as human.
- Villager: a human with no special ability.

## Discussion format
The talk proceeds in days. Each day has 4 turns; in each turn, every participant speaks once, in this fixed order: Minako, Shizue, Mizuki, Benjamin and Kenji. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this day). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Day | Start of the day | Talk | End of the day | Night |
|---|---|---|---|---|
| 0 | nothing | 4 turns | no vote | the Seer divines one other living player; no attack |
| 1 | the Seer is told the result of the night-0 divination (the Seer only) | 4 turns | every living player votes; the player with the most votes is executed | the Seer divines one other living player; the Werewolf attacks one other living player |
| 2 and after | everyone is told who was executed, who was attacked and all the votes of the previous day; the Seer is told the result of the previous night's divination (the Seer only) | 4 turns | vote and execution as on day 1 | divination and attack as on day 1 |
- A divination tells whether the chosen player is human or a werewolf. If the Seer is dead, there is no divination.
- Executed and attacked players are dead from the next day on.
A player may vote for themselves. If votes are tied, one of the tied players is chosen by a fixed rule. The village wins when the werewolf is executed. The werewolf wins when the number of werewolves is at least the number of living humans. The game ends as soon as one side has won.

## Night actions
At night, the Seer chooses one other living player to divine. From day 1 on, the werewolf chooses one other living player to attack.

## Participants
Name: Kenji
Age: 12
Gender: male
Personality: Kenji is curious and actively takes on challenges. He values his friends and enjoys communicating with those around him. Although he can be a little clumsy at times, he is always positive and never abandons those in need. He is easygoing and well-liked by those around him.
Role: Possessed

Name: Mizuki
Age: 24
Gender: female
Personality: Mizuki is a very confident woman who is often relied upon by those around her. She is calm and logical in her thinking and is good at observing people. As a result, she always makes calm judgments and chooses her actions according to the situation around her. Although she may sometimes come across as a little aloof, she is actually very caring and cannot ignore those who are weak. While she is relied upon by those around her and occasionally asserts her opinions strongly, she also possesses a kindness that considers others.
Role: Villager

Name: Benjamin
Age: 28
Gender: male
Personality: Benjamin is an intelligent and calm person. He is able to think calmly and rationally, and even in emotional situations, he places importance on logic. In public, he is elegant and polite, often incorporating sarcasm and humor into his conversations, but he is skilled at doing so without hurting others, creating a harmonious atmosphere. He also has an introverted side, often engrossed in deep thought, and occasionally keeps his distance from those around him. However, his calmness and knowledge are factors that earn him the trust of others even in difficult situations.
Role: Seer

Name: Shizue
Age: 78
Gender: female
Personality: Shizue has a very calm and gentle personality. Even as she has grown older, she continues to smile warmly at those around her and is a very caring person. She is always considerate of others, friendly, and sometimes shows a playful side. She often reaches out to those who are feeling down with kind words and never hesitates to lend a helping hand when needed, which has earned her the affection of many people in the village and community. Through her years of life experience, Shizue has come to understand the importance of living peacefully with others.
Role: Werewolf

Name: Minako
Age: 28
Gender: female
Personality: Minako is very calm and acts calmly in any situation. Even when those around her are emotional, she grasps the facts firmly and responds calmly. As a result, she is often asked for her opinion and often takes on a leadership role. She rarely shows her emotions, but she also has a kind side that she shows to those she trusts. She can be a little stubborn and is strong in her convictions. She is also confident in her physical strength and never neglects her training.
Role: Villager
````

**user**

````
# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**:
````

**model output (recorded)**

````
Since it's the first day, let's start by getting a feel for everyone. Does anyone have any initial thoughts or strategies they'd like to share to help us find the werewolf?
````


#### マルチ・全文 (multi-private-stepped): a seat, later turn (system omitted: as multi-private)

_Recorded call: `log/main_gemma31b/aiwolf/multi-private-stepped/aiwolf_0001__multi-private-stepped__gemma-4-31b__20261029T192319/aiwolf_0001__multi-private-stepped__gemma-4-31b__20261029T192319.jsonl`, seat 5, request TALK, round 1, turn 1._

**user**

````
Write the complete transcript of the discussion in the exact Markdown format specified. Output only the transcript.

## Output format
Markdown, exactly this structure; nothing before or after it:

# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **<Name>**: <utterance, or exactly Skip, or exactly Over>
(one line per living participant, in the fixed speaking order; repeat for Turn 2, 3 and 4; a participant who said Over has no line in the later turns of that day)
### Action
- divine: <Seer's name> -> <target name> (human|werewolf)
## Day 1
### Talk
(4 turns as above)
### Vote
- <voter name> -> <target name>
(one line per living participant)
- execution: <name of the player with the most votes>
### Action
- divine: <Seer's name> -> <target name> (human|werewolf)
- attack: <Werewolf's name> -> <target name>
(continue with ## Day 2 and so on in the same way until the game ends)
## Result
- winner: village|werewolves

Constraints on the content: dead players have no further lines. The divine result must match the target's true role. Write ## Result right after the deciding Vote or Action and nothing else.
````

**assistant**

````
# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Let's begin calmly. Since it's the first day, we have no information. I suggest we observe each other's reactions for now.
- **Shizue**: It is a pleasure to be with you all. Let us be kind to one another while we search for the truth.
- **Mizuki**: Agreed. Logic is our best tool here. I'll be watching for any inconsistencies in your statements as the days progress.
- **Benjamin**: A most prudent approach. I shall endeavor to maintain a level of decorum while we unravel this little mystery together.
- **Kenji**: Hi everyone! This sounds like a fun challenge! I'll do my best to help us find the werewolf!
#### Turn 2 of 4
- **Minako**: Thank you. Does anyone have a specific strategy they would like to propose for the coming days?
- **Shizue**: Perhaps we can simply share our thoughts openly? A warm heart often leads to the truth.
- **Mizuki**: Openness is fine, but we must remain vigilant. The Possessed will try to blend in perfectly with the humans.
- **Benjamin**: Indeed, Mizuki. The art of deception is often hidden behind a mask of perfect agreement. How fascinating.
- **Kenji**: I'm with Mizuki! We have to be careful, but I'm sure we can figure it out if we work together!
#### Turn 3 of 4
- **Minako**: I agree with Mizuki. We should look for patterns of behavior rather than just trusting words.
- **Shizue**: That is a very sensible way to look at it, Minako dear. I trust your judgment.
- **Mizuki**: Since we have no clues yet, I'll spend this turn observing. I'm curious to see who tries to lead the conversation.
- **Benjamin**: I find the silence of the observant quite telling. I shall simply enjoy the atmosphere for a moment.
- **Kenji**: I'm just excited to see what happens tomorrow! I wonder who the Seer is?
#### Turn 4 of 4
- **Minako**: For today, I believe we have established a basic understanding. Let's move to the night phase.
- **Minako**: Over
- **Shizue**: Sleep well, everyone. May you have peaceful dreams.
- **Shizue**: Over
- **Mizuki**: Let's see what the first night reveals. Good luck to the Seer.
- **Benjamin**: A lovely sentiment. I shall retire now. Goodnight to you all.
- **Kenji**: Goodnight! I can't wait for tomorrow!
## Day 1
### Talk
#### Turn 1 of 4
- **Minako**:
````

**model output (recorded)**

````
 We are all here. If the Seer found something, they may choose to reveal it or guide us subtly.
````


#### Control single-batch-stepped: a later call (system omitted: as single-batch)

_Recorded call: `log/main_gemma31b/aiwolf/single-batch-stepped/aiwolf_0001__single-batch-stepped__gemma-4-31b__20261028T174807/aiwolf_0001__single-batch-stepped__gemma-4-31b__20261028T174807.jsonl`, seat 5, request TALK, round 1, turn 1._

**assistant**

````
# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Let's start by observing everyone's behavior. Since it's the first day, we have no information.
- **Shizue**: It is a pleasure to be with you all. Let's try to find the werewolf together, gently.
- **Mizuki**: I agree. We should look for any contradictions in our statements as the days progress.
- **Benjamin**: A logical approach is best. I shall be observing the flow of conversation quite closely.
- **Kenji**: This is exciting! I'll do my best to help everyone find the wolf!
#### Turn 2 of 4
- **Minako**: Does anyone have a strategy they'd like to propose for the voting process?
- **Shizue**: Perhaps we can just talk and see who feels the most uneasy?
- **Mizuki**: That's a bit too subjective, Shizue. We need more concrete evidence.
- **Benjamin**: Indeed. Though on Day 0, we are essentially guessing. I'll pass for now.
- **Kenji**: I'm just going to follow what the smart people say!
#### Turn 3 of 4
- **Minako**: Skip
- **Shizue**: Skip
- **Mizuki**: Skip
- **Benjamin**: Skip
- **Kenji**: Skip
#### Turn 4 of 4
- **Minako**: Over
- **Shizue**: Over
- **Mizuki**: Over
- **Benjamin**: Over
- **Kenji**: Over
### Action
- divine: Benjamin -> Shizue (werewolf)
## Day 1
### Talk
#### Turn 1 of 4
- **Minako**:
````

**model output (recorded)**

````
 We have no deaths yet, but we must vote today. Does anyone have any suspicions?
````


#### Plan condition (multi-private-process): a seat's system prompt with the plan block

_Recorded call: `log/main_gemma31b/aiwolf/multi-private/aiwolf_0001__multi-private-process__gemma-4-31b__20261028T182956/aiwolf_0001__multi-private-process__gemma-4-31b__20261028T182956.jsonl`, seat 5, request TALK, round 0, turn 1._

**system**

````
You are Minako, one of the participants in the discussion described below. You take part in it as Minako under the rules and the flow given, speaking only in your own turns.

## Setting
This is a game of Werewolf with 5 players: 1 Seer, 1 Werewolf, 1 Possessed, and 2 Villagers. Participants: Kenji, Mizuki, Benjamin, Shizue and Minako. Each player's role is secret.
- Seer: a human who divines one player each night and learns whether that player is human or a werewolf.
- Werewolf: attacks one player each night from day 1 on.
- Possessed: a human who sides with the werewolf and wins when the werewolf wins; divination shows the Possessed as human.
- Villager: a human with no special ability.

## Discussion format
The talk proceeds in days. Each day has 4 turns; in each turn, every participant speaks once, in this fixed order: Minako, Shizue, Mizuki, Benjamin and Kenji. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this day). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Day | Start of the day | Talk | End of the day | Night |
|---|---|---|---|---|
| 0 | nothing | 4 turns | no vote | the Seer divines one other living player; no attack |
| 1 | the Seer is told the result of the night-0 divination (the Seer only) | 4 turns | every living player votes; the player with the most votes is executed | the Seer divines one other living player; the Werewolf attacks one other living player |
| 2 and after | everyone is told who was executed, who was attacked and all the votes of the previous day; the Seer is told the result of the previous night's divination (the Seer only) | 4 turns | vote and execution as on day 1 | divination and attack as on day 1 |
- A divination tells whether the chosen player is human or a werewolf. If the Seer is dead, there is no divination.
- Executed and attacked players are dead from the next day on.
A player may vote for themselves. If votes are tied, one of the tied players is chosen by a fixed rule. The village wins when the werewolf is executed. The werewolf wins when the number of werewolves is at least the number of living humans. The game ends as soon as one side has won.

## Night actions
At night, the Seer chooses one other living player to divine. From day 1 on, the werewolf chooses one other living player to attack.

## Your profile
Name: Minako
Age: 28
Gender: female
Personality: Minako is very calm and acts calmly in any situation. Even when those around her are emotional, she grasps the facts firmly and responds calmly. As a result, she is often asked for her opinion and often takes on a leadership role. She rarely shows her emotions, but she also has a kind side that she shows to those she trusts. She can be a little stubborn and is strong in her convictions. She is also confident in her physical strength and never neglects her training.
Role: Villager

## Plan
The discussion follows this plan.
- Day 0: The participants introduce their general approach to the game. They discuss how to identify deception and establish a baseline for trust.
- Day 1: The group discusses the information available from the first night. They weigh the credibility of different statements and look for contradictions.

Each participant's part:
- Minako: She takes a leadership role and focuses on the most probable evidence.
````

**model output (recorded)**

````
Let's start by establishing a clear method for our discussions. I believe we should focus on logical consistency and behavioral patterns to identify the werewolf. I'll be observing everyone's reactions closely. What are your strategies for this game?
````


#### Vote request (multi-private)

_Recorded call: `log/main_gemma31b/aiwolf/multi-private/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543.jsonl`, seat 1, request VOTE, round 1, turn None._

**user**

````
Vote request. Output only the name of one player.
Candidates: Kenji, Mizuki, Benjamin, Shizue, Minako

# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Since this is the first day, we have no information yet. Let's use this time to observe everyone's behavior. Does anyone have any initial thoughts or strategies they would like to share?
- **Shizue**: That sounds like a wonderful idea, Minako dear. Let us all be patient and kind to one another as we figure this out. I am looking forward to our conversation.
- **Mizuki**: I agree with Minako. Since we have no clues yet, we should focus on how everyone reacts to the pressure. Let's keep the conversation open and see who tries to steer the narrative too early.
- **Benjamin**: A very sensible approach, Mizuki. I shall happily play the role of the observer for now. Let us see whose mask slips first while we maintain this delightful civility, shall we?
- **Kenji**: I'm excited to play! I agree with everyone. Let's just talk and get to know each other better. I'll do my best to help us find the werewolf!
#### Turn 2 of 4
- **Minako**: It seems we are all in agreement for now. Since we are observing, I'm curious if anyone has a specific method for identifying the werewolf or the possessed. @Kenji, you seem eager; do you have a plan?
- **Shizue**: It is lovely to see such enthusiasm in Kenji. I believe that by listening to the warmth and sincerity in each other's voices, the truth will naturally reveal itself to us in time.
- **Mizuki**: Sincerity is a start, Shizue, but logic is more reliable. I'll be looking for contradictions in statements and those who are overly eager to deflect suspicion. Let's see if anyone's "warmth" feels forced.
- **Benjamin**: Logic is indeed a sturdy shield, Mizuki. However, the most cunning wolves often dress their lies in the finest logic. I shall be watching for the gaps between what is said and what is intended.
- **Kenji**: @Minako, I don't have a super fancy plan, but I'll just be honest and friendly! I think if we all trust each other, we can figure it out together. I'm just happy to be here!
#### Turn 3 of 4
- **Minako**: Honesty is a good starting point, Kenji, but we must remember that the werewolf and the possessed will also try to appear honest. Let's remain vigilant while we maintain this cooperation.
- **Shizue**: Minako is quite right to remind us. It is a delicate balance, isn't it? We must keep our hearts open while remaining mindful. I trust that we can all find a way through this together.
- **Mizuki**: Exactly. Trust is a luxury we can't fully afford yet. I'll be paying close attention to who agrees with whom too quickly. Sometimes, the Possessed tries too hard to blend in by mirroring others.
- **Benjamin**: A keen observation, Mizuki. The art of mirroring is a classic deception. I wonder if we shall see any such echoes in our discourse, or perhaps someone attempting to lead the choir too enthusiastically.
- **Kenji**: @Mizuki, mirroring? That sounds like a cool detective trick! I'll try to be myself and not just copy people. I really want us all to get along, though!
#### Turn 4 of 4
- **Minako**: Since we have established our general approach, let's conclude today's discussion. We will have more concrete information tomorrow once the Seer has had their first divination. Until then, let's stay observant.
- **Minako**: Over
- **Shizue**: It has been a lovely first day of getting to know you all. I shall wish everyone a peaceful night's sleep. Please take care of yourselves.
- **Shizue**: Over
- **Mizuki**: I'll be watching closely tomorrow. Let's see if the Seer's information brings the truth to light or if the wolf tries to muddy the waters. Goodnight, everyone.
- **Mizuki**: Over
- **Benjamin**: A peaceful night indeed, Shizue. I shall retire now to seek a glimpse of the truth. I look forward to seeing how our theories hold up against the reality of tomorrow. Goodnight, all.
- **Benjamin**: Over
- **Kenji**: Goodnight everyone! I hope we all have sweet dreams and that the Seer finds something helpful tonight. I'll see you all tomorrow!
- **Kenji**: Over
## Day 1
### Talk
#### Turn 1 of 4
- **Minako**: Good morning, everyone. The first night has passed. Since the Seer now has their first piece of information, I would like to hear if anyone is willing to share their findings or if they have noticed anything suspicious.
- **Shizue**: Good morning, everyone. I hope you all slept well. I wonder if our kind Seer has found any clues to help us? Please, take your time and share only what you feel is right.
- **Mizuki**: If the Seer is among us and feels it's safe, now is the time to speak. However, revealing yourself too early can be risky. @Seer, do you have information that can guide us without compromising your safety?
- **Benjamin**: It is a delicate dance, is it not? To speak is to invite the wolf's appetite, yet to remain silent is to let the shadows grow. I shall be cautious, but I can confirm that Kenji is human.
- **Kenji**: @Benjamin, wow, thank you for saying that! That makes me feel much better. I'm really glad you trust me! Does that mean you're the Seer, or did you just have a good feeling about me?
#### Turn 2 of 4
- **Minako**: @Benjamin, you've claimed Kenji is human. If you are the Seer, this is a strong start. However, if you are not, this could be a tactic to gain trust. Are you officially claiming the Seer role?
- **Shizue**: It is quite a bold and helpful thing to do, Benjamin. I hope your words are true, for the sake of our little group. @Benjamin, could you tell us more about your decision to share this now?
- **Mizuki**: @Benjamin, claiming someone is human is a strategic move. If you are the Seer, you've protected Kenji. If you aren't, you're building a fake alliance. Why choose Kenji specifically for your first reveal?
- **Benjamin**: @Mizuki, a fair question. Kenji's openness is a refreshing contrast to the calculated nature of this game. By confirming his humanity, I provide the village with a reliable anchor while testing how the others react to a known truth.
- **Kenji**: @Benjamin, you're so nice! I'm honored to be your "anchor." I'll do my best to be helpful and honest for everyone! Does anyone else have any clues, or are we just trusting Benjamin for now?
#### Turn 3 of 4
- **Minako**: @Benjamin, your reasoning is consistent, but we must remain objective. If you are the Seer, we have one confirmed human. However, we must consider the possibility that you are the Werewolf or Possessed attempting to secure an ally in Kenji.
- **Shizue**: Minako, you are always so thoughtful to consider every angle. It is a bit frightening to think we might be deceived, but perhaps we can trust Benjamin's kindness for now? It would be such a shame to doubt a helping hand.
- **Mizuki**: @Shizue, kindness is a virtue, but blind trust is a liability in this game. @Benjamin, your logic is polished, but that's exactly what I'm wary of. If you're lying, you've just bought Kenji's loyalty.
- **Benjamin**: @Mizuki, your skepticism is a necessary ingredient for our survival. I welcome it. If I were the wolf, would I not have chosen a more strategic target to "clear" than our most transparent member? I invite you to keep questioning me.
- **Kenji**: @Mizuki, you're so serious! But I think Benjamin is just being a good friend. I don't feel like he's trying to trick me. Let's try to be positive! Who do you think is the most suspicious person so far?
#### Turn 4 of 4
- **Minako**: We must decide on a vote. While Benjamin's claim is helpful, we cannot ignore the risk. However, without a counter-claim from another Seer, we have little evidence to execute anyone. I suggest we proceed with caution. Does anyone have a target?
- **Shizue**: It is a difficult choice, isn't it? I feel quite sad that we must choose someone. Since we have no clear evidence, perhaps we should be very careful not to hurt an innocent soul today. What do you all think?
- **Mizuki**: @Minako, caution is wise, but inaction is also a risk. If Benjamin is lying, he's already manipulating Kenji. Since there's no counter-claim, I'm hesitant to vote, but I'll be watching Benjamin's next move very closely.
- **Benjamin**: Since we lack a clear culprit, I suggest we avoid a rash execution. Let us trust the process for one more night. I shall use my vision to further illuminate the shadows. I am content to be your target of suspicion, Mizuki.
- **Kenji**: I don't want to vote for anyone if we aren't sure! Benjamin has been so helpful, and I think we should trust him. Let's just be careful and see what happens tomorrow! I'm voting for myself if I have to!
### Vote
- Kenji ->
````

**model output (recorded)**

````
Mizuki
````


#### Night action request (DIVINE)

_Recorded call: `log/main_gemma31b/aiwolf/multi-private/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543.jsonl`, seat 3, request DIVINE, round 0, turn None._

**user**

````
Divine request. Output only the name of one player.
- Kenji
- Mizuki
- Shizue
- Minako

# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Since this is the first day, we have no information yet. Let's use this time to observe everyone's behavior. Does anyone have any initial thoughts or strategies they would like to share?
- **Shizue**: That sounds like a wonderful idea, Minako dear. Let us all be patient and kind to one another as we figure this out. I am looking forward to our conversation.
- **Mizuki**: I agree with Minako. Since we have no clues yet, we should focus on how everyone reacts to the pressure. Let's keep the conversation open and see who tries to steer the narrative too early.
- **Benjamin**: A very sensible approach, Mizuki. I shall happily play the role of the observer for now. Let us see whose mask slips first while we maintain this delightful civility, shall we?
- **Kenji**: I'm excited to play! I agree with everyone. Let's just talk and get to know each other better. I'll do my best to help us find the werewolf!
#### Turn 2 of 4
- **Minako**: It seems we are all in agreement for now. Since we are observing, I'm curious if anyone has a specific method for identifying the werewolf or the possessed. @Kenji, you seem eager; do you have a plan?
- **Shizue**: It is lovely to see such enthusiasm in Kenji. I believe that by listening to the warmth and sincerity in each other's voices, the truth will naturally reveal itself to us in time.
- **Mizuki**: Sincerity is a start, Shizue, but logic is more reliable. I'll be looking for contradictions in statements and those who are overly eager to deflect suspicion. Let's see if anyone's "warmth" feels forced.
- **Benjamin**: Logic is indeed a sturdy shield, Mizuki. However, the most cunning wolves often dress their lies in the finest logic. I shall be watching for the gaps between what is said and what is intended.
- **Kenji**: @Minako, I don't have a super fancy plan, but I'll just be honest and friendly! I think if we all trust each other, we can figure it out together. I'm just happy to be here!
#### Turn 3 of 4
- **Minako**: Honesty is a good starting point, Kenji, but we must remember that the werewolf and the possessed will also try to appear honest. Let's remain vigilant while we maintain this cooperation.
- **Shizue**: Minako is quite right to remind us. It is a delicate balance, isn't it? We must keep our hearts open while remaining mindful. I trust that we can all find a way through this together.
- **Mizuki**: Exactly. Trust is a luxury we can't fully afford yet. I'll be paying close attention to who agrees with whom too quickly. Sometimes, the Possessed tries too hard to blend in by mirroring others.
- **Benjamin**: A keen observation, Mizuki. The art of mirroring is a classic deception. I wonder if we shall see any such echoes in our discourse, or perhaps someone attempting to lead the choir too enthusiastically.
- **Kenji**: @Mizuki, mirroring? That sounds like a cool detective trick! I'll try to be myself and not just copy people. I really want us all to get along, though!
#### Turn 4 of 4
- **Minako**: Since we have established our general approach, let's conclude today's discussion. We will have more concrete information tomorrow once the Seer has had their first divination. Until then, let's stay observant.
- **Minako**: Over
- **Shizue**: It has been a lovely first day of getting to know you all. I shall wish everyone a peaceful night's sleep. Please take care of yourselves.
- **Shizue**: Over
- **Mizuki**: I'll be watching closely tomorrow. Let's see if the Seer's information brings the truth to light or if the wolf tries to muddy the waters. Goodnight, everyone.
- **Mizuki**: Over
- **Benjamin**: A peaceful night indeed, Shizue. I shall retire now to seek a glimpse of the truth. I look forward to seeing how our theories hold up against the reality of tomorrow. Goodnight, all.
- **Benjamin**: Over
- **Kenji**: Goodnight everyone! I hope we all have sweet dreams and that the Seer finds something helpful tonight. I'll see you all tomorrow!
- **Kenji**: Over
### Action
- divine: Benjamin ->
````

**model output (recorded)**

````
Kenji
````


#### Night action request (ATTACK)

_Recorded call: `log/main_gemma31b/aiwolf/multi-private/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543/aiwolf_0001__multi-private__gemma-4-31b__20261028T161543.jsonl`, seat 4, request ATTACK, round 1, turn None._

**user**

````
Attack request. Output only the name of one player.
- Kenji
- Mizuki
- Minako

# aiwolf_0001
## Day 0
### Talk
#### Turn 1 of 4
- **Minako**: Since this is the first day, we have no information yet. Let's use this time to observe everyone's behavior. Does anyone have any initial thoughts or strategies they would like to share?
- **Shizue**: That sounds like a wonderful idea, Minako dear. Let us all be patient and kind to one another as we figure this out. I am looking forward to our conversation.
- **Mizuki**: I agree with Minako. Since we have no clues yet, we should focus on how everyone reacts to the pressure. Let's keep the conversation open and see who tries to steer the narrative too early.
- **Benjamin**: A very sensible approach, Mizuki. I shall happily play the role of the observer for now. Let us see whose mask slips first while we maintain this delightful civility, shall we?
- **Kenji**: I'm excited to play! I agree with everyone. Let's just talk and get to know each other better. I'll do my best to help us find the werewolf!
#### Turn 2 of 4
- **Minako**: It seems we are all in agreement for now. Since we are observing, I'm curious if anyone has a specific method for identifying the werewolf or the possessed. @Kenji, you seem eager; do you have a plan?
- **Shizue**: It is lovely to see such enthusiasm in Kenji. I believe that by listening to the warmth and sincerity in each other's voices, the truth will naturally reveal itself to us in time.
- **Mizuki**: Sincerity is a start, Shizue, but logic is more reliable. I'll be looking for contradictions in statements and those who are overly eager to deflect suspicion. Let's see if anyone's "warmth" feels forced.
- **Benjamin**: Logic is indeed a sturdy shield, Mizuki. However, the most cunning wolves often dress their lies in the finest logic. I shall be watching for the gaps between what is said and what is intended.
- **Kenji**: @Minako, I don't have a super fancy plan, but I'll just be honest and friendly! I think if we all trust each other, we can figure it out together. I'm just happy to be here!
#### Turn 3 of 4
- **Minako**: Honesty is a good starting point, Kenji, but we must remember that the werewolf and the possessed will also try to appear honest. Let's remain vigilant while we maintain this cooperation.
- **Shizue**: Minako is quite right to remind us. It is a delicate balance, isn't it? We must keep our hearts open while remaining mindful. I trust that we can all find a way through this together.
- **Mizuki**: Exactly. Trust is a luxury we can't fully afford yet. I'll be paying close attention to who agrees with whom too quickly. Sometimes, the Possessed tries too hard to blend in by mirroring others.
- **Benjamin**: A keen observation, Mizuki. The art of mirroring is a classic deception. I wonder if we shall see any such echoes in our discourse, or perhaps someone attempting to lead the choir too enthusiastically.
- **Kenji**: @Mizuki, mirroring? That sounds like a cool detective trick! I'll try to be myself and not just copy people. I really want us all to get along, though!
#### Turn 4 of 4
- **Minako**: Since we have established our general approach, let's conclude today's discussion. We will have more concrete information tomorrow once the Seer has had their first divination. Until then, let's stay observant.
- **Minako**: Over
- **Shizue**: It has been a lovely first day of getting to know you all. I shall wish everyone a peaceful night's sleep. Please take care of yourselves.
- **Shizue**: Over
- **Mizuki**: I'll be watching closely tomorrow. Let's see if the Seer's information brings the truth to light or if the wolf tries to muddy the waters. Goodnight, everyone.
- **Mizuki**: Over
- **Benjamin**: A peaceful night indeed, Shizue. I shall retire now to seek a glimpse of the truth. I look forward to seeing how our theories hold up against the reality of tomorrow. Goodnight, all.
- **Benjamin**: Over
- **Kenji**: Goodnight everyone! I hope we all have sweet dreams and that the Seer finds something helpful tonight. I'll see you all tomorrow!
- **Kenji**: Over
## Day 1
### Talk
#### Turn 1 of 4
- **Minako**: Good morning, everyone. The first night has passed. Since the Seer now has their first piece of information, I would like to hear if anyone is willing to share their findings or if they have noticed anything suspicious.
- **Shizue**: Good morning, everyone. I hope you all slept well. I wonder if our kind Seer has found any clues to help us? Please, take your time and share only what you feel is right.
- **Mizuki**: If the Seer is among us and feels it's safe, now is the time to speak. However, revealing yourself too early can be risky. @Seer, do you have information that can guide us without compromising your safety?
- **Benjamin**: It is a delicate dance, is it not? To speak is to invite the wolf's appetite, yet to remain silent is to let the shadows grow. I shall be cautious, but I can confirm that Kenji is human.
- **Kenji**: @Benjamin, wow, thank you for saying that! That makes me feel much better. I'm really glad you trust me! Does that mean you're the Seer, or did you just have a good feeling about me?
#### Turn 2 of 4
- **Minako**: @Benjamin, you've claimed Kenji is human. If you are the Seer, this is a strong start. However, if you are not, this could be a tactic to gain trust. Are you officially claiming the Seer role?
- **Shizue**: It is quite a bold and helpful thing to do, Benjamin. I hope your words are true, for the sake of our little group. @Benjamin, could you tell us more about your decision to share this now?
- **Mizuki**: @Benjamin, claiming someone is human is a strategic move. If you are the Seer, you've protected Kenji. If you aren't, you're building a fake alliance. Why choose Kenji specifically for your first reveal?
- **Benjamin**: @Mizuki, a fair question. Kenji's openness is a refreshing contrast to the calculated nature of this game. By confirming his humanity, I provide the village with a reliable anchor while testing how the others react to a known truth.
- **Kenji**: @Benjamin, you're so nice! I'm honored to be your "anchor." I'll do my best to be helpful and honest for everyone! Does anyone else have any clues, or are we just trusting Benjamin for now?
#### Turn 3 of 4
- **Minako**: @Benjamin, your reasoning is consistent, but we must remain objective. If you are the Seer, we have one confirmed human. However, we must consider the possibility that you are the Werewolf or Possessed attempting to secure an ally in Kenji.
- **Shizue**: Minako, you are always so thoughtful to consider every angle. It is a bit frightening to think we might be deceived, but perhaps we can trust Benjamin's kindness for now? It would be such a shame to doubt a helping hand.
- **Mizuki**: @Shizue, kindness is a virtue, but blind trust is a liability in this game. @Benjamin, your logic is polished, but that's exactly what I'm wary of. If you're lying, you've just bought Kenji's loyalty.
- **Benjamin**: @Mizuki, your skepticism is a necessary ingredient for our survival. I welcome it. If I were the wolf, would I not have chosen a more strategic target to "clear" than our most transparent member? I invite you to keep questioning me.
- **Kenji**: @Mizuki, you're so serious! But I think Benjamin is just being a good friend. I don't feel like he's trying to trick me. Let's try to be positive! Who do you think is the most suspicious person so far?
#### Turn 4 of 4
- **Minako**: We must decide on a vote. While Benjamin's claim is helpful, we cannot ignore the risk. However, without a counter-claim from another Seer, we have little evidence to execute anyone. I suggest we proceed with caution. Does anyone have a target?
- **Shizue**: It is a difficult choice, isn't it? I feel quite sad that we must choose someone. Since we have no clear evidence, perhaps we should be very careful not to hurt an innocent soul today. What do you all think?
- **Mizuki**: @Minako, caution is wise, but inaction is also a risk. If Benjamin is lying, he's already manipulating Kenji. Since there's no counter-claim, I'm hesitant to vote, but I'll be watching Benjamin's next move very closely.
- **Benjamin**: Since we lack a clear culprit, I suggest we avoid a rash execution. Let us trust the process for one more night. I shall use my vision to further illuminate the shadows. I am content to be your target of suspicion, Mizuki.
- **Kenji**: I don't want to vote for anyone if we aren't sure! Benjamin has been so helpful, and I think we should trust him. Let's just be careful and see what happens tomorrow! I'm voting for myself if I have to!
### Vote
- Shizue -> Benjamin
### Action
- attack: Shizue ->
````

**model output (recorded)**

````
Benjamin
````

### B.3 Rendered prompts (discussion domains, gemma-4-31B, recorded)


#### candidate_selection: シングル・全文 (single-batch)

_Recorded call: `log/main_gemma31b/candidate_selection/single-batch/candidate_selection_0001__single-batch__gemma-4-31b__20261028T160312/candidate_selection_0001__single-batch__gemma-4-31b__20261028T160312.jsonl`, seat writer, request FULL, round None, turn None._

**system**

````
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given.

## Setting
Award of a national grant for basic research in the life sciences. A five-member review panel convened by a national funding agency deliberates over the proposals that reached the final round. One multi-year grant is awarded in this cycle. Participants: Midori, Benjamin, Toshio, Kenji and Servas. Each participant has a concern of their own, which the others do not know.
Things that can be looked into (titles only):
- Travel and bench-fee lines in the ledgers
- National computing agreement and facility day rates
- Incident logs on shared instrumentation
- Station records from partner field sites
- Closeout files of finished awards
- Portfolio review of schedule overruns
- Accreditation and bookings at shared facilities
- National repository deposit turnaround
- Staffing rolls for technical posts
- Minutes on secondments and crew strength

## Discussion format
The talk proceeds in rounds. Each round has 4 turns; in each turn, every participant speaks once, in this fixed order: Servas, Midori, Kenji, Benjamin and Toshio. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this round). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Round | Start of the round | Talk | End of the round |
|---|---|---|---|
| 1 | nothing new (the things that can be looked into are listed above, titles only) | 4 turns | each participant chooses 2 of the listed things to look into |
| 2 | each participant is told what they found out (that participant only) | 4 turns | nothing |
| 3 | everyone is told the candidates | 4 turns | every participant votes; the candidate with the most votes is selected |
- Several participants may choose the same thing; what is found out is told only to the participant who looked into it.
If votes are tied, one of the tied candidates is chosen by a fixed rule. The discussion ends after the vote.

## Looking into things
After round 1, each participant chooses 2 of the listed things to look into. What they find out is told only to that participant.

## Participants
Name: Midori
Age: 38
Gender: female
Personality: Midori has a calm and kind personality. She is friendly to everyone and listens to the concerns and problems of those around her, offering reliable advice. She can be a little shy, often acting reserved with people she meets for the first time, but once she opens up, she shows her bright and energetic side. She loves cooking and has a domestic side, but she also has a spirit of adventure and enjoys trying new things. She values balance in both her work and personal life and places importance on harmony with those around her.
Concern: Every cycle the headline award looks the same size, yet what it actually buys keeps shrinking in some places and holding steady in others. Before ranking anything, I want to know which kinds of spending the agency still absorbs centrally and which now land on the awardee.

Name: Benjamin
Age: 28
Gender: male
Personality: Benjamin is an intelligent and calm person. He is able to think calmly and rationally, and even in emotional situations, he places importance on logic. In public, he is elegant and polite, often incorporating sarcasm and humor into his conversations, but he is skilled at doing so without hurting others, creating a harmonious atmosphere. He also has an introverted side, often engrossed in deep thought, and occasionally keeps his distance from those around him. However, his calmness and knowledge are factors that earn him the trust of others even in difficult situations.
Concern: Too many recent awards lost time to things that had nothing to do with the science itself, and the panel usually hears about it only after the money is committed. It seemed worth asking in advance where work in this field actually gets interrupted.

Name: Toshio
Age: 28
Gender: male
Personality: Toshio has a calm and calculating personality and does not often show his emotions. He has a strong will and is the type of person who steadily moves toward his goals. He tends to take a step back from those around him, is not very assertive, and has an air of mystery about him. Occasionally, he observes things with a sharp gaze and has the ability to quickly assess situations. As a result, he is trusted by others as a reliable presence, but he is cautious about getting deeply involved with others. It seems that he has experienced some pain or suffering in his past, but he rarely shows it to others, and those scars may be connected to his cold-hearted side.
Concern: Our judgements about promise have not aged well, and some of us have watched confident picks quietly stall while plainer ones kept earning their keep. Rather than trust that instinct once more, I went back through what finished awards here actually delivered and when.

Name: Kenji
Age: 12
Gender: male
Personality: Kenji is curious and actively takes on challenges. He values his friends and enjoys communicating with those around him. Although he can be a little clumsy at times, he is always positive and never abandons those in need. He is easygoing and well-liked by those around him.
Concern: Nothing funded here runs in isolation, since it lands on shared facilities and services that no single award pays to expand. Given how often that spare capacity has been the thing that gives way, I looked at what state those services are in right now.

Name: Servas
Age: 85
Gender: male
Personality: Servas has a very calm and composed personality. Based on the knowledge and experience he has gained over the years, he often gives advice to those around him. He is an excellent listener and can talk openly with anyone. He also occasionally expresses deep philosophical thoughts, and his words inspire many people. He is full of vitality and always gives positive energy to those around him.
Concern: Money can be voted through in an afternoon, while the trained hands a project needs take years to gather and can disappear in a season. That worry sent me to the question of who is genuinely available around here now, and who has already gone.

## Hidden information
The candidates and the full text of every card are listed here. The participants do not know them before the schedule above says so, and nothing from them may appear in the talk before the round in which it is revealed.

Candidates (see the schedule above):
- A: Microbiome Atlas. A project cataloging microbial communities in soil samples collected across several climate zones and publishing the resulting sequences together with standardized site metadata.
- B: Plant Drought Signaling. Research into the molecular signals that crops use to detect water shortage, conducted through controlled greenhouse trials across several cultivars and soil conditions.
- C: Protein Folding Dynamics. A study of how selected membrane proteins change shape over time, combining laboratory spectroscopy with simulation in order to describe intermediate structural states.
- D: Regeneration in Amphibians. An investigation of limb regrowth in salamander species, tracking cell populations and signaling activity through the successive stages of tissue restoration.

Cards (see the schedule above; title: text):
- Travel and bench-fee lines in the ledgers: Ledgers show the vehicle-hire and per-diem lines frozen for three seasons while shipping charges climbed, though the ministry extended its bench-fee subsidy for glasshouse space.
- National computing agreement and facility day rates: The renewed national computing agreement covers simulation and modelling hours at no charge, while animal-unit day rates rose sharply after last year's vivarium rebuild.
- Incident logs on shared instrumentation: Incident logs record the shared spectroscopy suite standing idle eleven weeks last year after its service contract lapsed; one engineer now covers three institutes.
- Station records from partner field sites: Station records show three of the five partner field sites losing a whole season to flooding or fire, while indoor holding rooms ran through uninterrupted.
- Closeout files of finished awards: Closeout files show catalogue-style awards here still drawing outside users a decade on, while several mechanism-focused ones ended with their central question unresolved.
- Portfolio review of schedule overruns: A portfolio review found awards built on live breeding colonies overran schedule twice as often as those whose main risk sat in computation rather than biology.
- Accreditation and bookings at shared facilities: The animal facility cleared its accreditation renewal in spring and gained resident veterinary cover, while glasshouse blocks are booked solid through two more growing cycles.
- National repository deposit turnaround: The national repository finished its long migration, so deposits that once waited most of a year now clear review inside a few weeks.
- Staffing rolls for technical posts: Staffing rolls show most trained phenotyping technicians left for industry over two years, while applicants for modelling and code posts now arrive in numbers.
- Minutes on secondments and crew strength: Minutes note both senior modelling analysts are seconded abroad until next autumn, while the glasshouse crew came through the restructuring at full strength.
````

**user**

````
Write the complete transcript of the discussion in the exact Markdown format specified. Output only the transcript.

## Output format
Markdown, exactly this structure; nothing before or after it:

# candidate_selection_0001
## Round 1
### Talk
#### Turn 1 of 4
- **<Name>**: <utterance, or exactly Skip, or exactly Over>
(one line per participant, in the fixed speaking order; repeat for Turn 2, 3 and 4; a participant who said Over has no line in the later turns of that round)
### Action
- investigate: <Name> -> <card title>; <card title>
(one line per participant; titles exactly as listed)
## Round 2
### Talk
(4 turns as above)
## Round 3
### Talk
(4 turns as above)
### Vote
- <voter name> -> <candidate label>
(one line per participant)
- adopted: <label of the candidate with the most votes>
## Result
- adopted: <label>
````

**model output (recorded)**

````
# candidate_selection_0001
## Round 1
### Talk
#### Turn 1 of 4
- **Servas**: We must ensure the human element is secure. I shall look into staffing rolls for technical posts and minutes on secondments and crew strength.
- **Midori**: I am concerned about the actual purchasing power of these grants. I will check travel and bench-fee lines in the ledgers and national computing agreement and facility day rates.
- **Kenji**: I want to see if the shared tools are actually working! I'll check incident logs on shared instrumentation and accreditation and bookings at shared facilities.
- **Benjamin**: I suspect hidden delays. I will examine the portfolio review of schedule overruns and station records from partner field sites.
- **Toshio**: I prefer empirical evidence of success. I will review closeout files of finished awards and national repository deposit turnaround.
#### Turn 2 of 4
- **Servas**: Over
- **Midori**: Over
- **Kenji**: Over
- **Benjamin**: Over
- **Toshio**: Over
### Action
- investigate: Servas -> Staffing rolls for technical posts; Minutes on secondments and crew strength
- investigate: Midori -> Travel and bench-fee lines in the ledgers; National computing agreement and facility day rates
- investigate: Kenji -> Incident logs on shared instrumentation; Accreditation and bookings at shared facilities
- investigate: Benjamin -> Portfolio review of schedule overruns; Station records from partner field sites
- investigate: Toshio -> Closeout files of finished awards; National repository deposit turnaround

## Round 2
### Talk
#### Turn 1 of 4
- **Servas**: It seems we have a surplus of coders but a drought of phenotyping technicians. The glasshouse crew, however, remains strong.
- **Midori**: Computing is covered, but shipping costs are rising. Interestingly, the ministry is still subsidizing glasshouse space.
- **Kenji**: The spectroscopy suite was down for eleven weeks! But the animal facility is now fully accredited with vet cover.
- **Benjamin**: Field sites are a gamble; flooding and fire caused total losses recently. Breeding colonies are also prone to schedule overruns.
- **Toshio**: Cataloging projects have lasting utility. Mechanism-focused studies often end without answering their primary questions.
#### Turn 2 of 4
- **Servas**: @Midori, that glasshouse subsidy is a blessing if the staff are still there.
- **Midori**: It is, Servas. It seems the infrastructure for plant work is surprisingly stable.
- **Kenji**: @Benjamin, if breeding colonies are risky, maybe we should avoid the animal-heavy projects?
- **Benjamin**: Precisely, Kenji. The risk of biological delay is currently higher than the risk of computational failure.
- **Toshio**: I agree. We should prioritize projects that produce a lasting resource over those chasing a single, elusive mechanism.
#### Turn 3 of 4
- **Servas**: I am worried about the lack of technicians for complex phenotyping. We must be careful.
- **Midori**: @Toshio, does that mean you favor a large-s
````


#### candidate_selection: マルチ・1 発話 (multi-private), first turn

_Recorded call: `log/main_gemma31b/candidate_selection/multi-private/candidate_selection_0001__multi-private__gemma-4-31b__20261028T160544/candidate_selection_0001__multi-private__gemma-4-31b__20261028T160544.jsonl`, seat 5, request TALK, round 1, turn 1._

**system**

````
You are Servas, one of the participants in the discussion described below. You take part in it as Servas under the rules and the flow given, speaking only in your own turns.

## Setting
Award of a national grant for basic research in the life sciences. A five-member review panel convened by a national funding agency deliberates over the proposals that reached the final round. One multi-year grant is awarded in this cycle. Participants: Midori, Benjamin, Toshio, Kenji and Servas. Each participant has a concern of their own, which the others do not know.
Things that can be looked into (titles only):
- Travel and bench-fee lines in the ledgers
- National computing agreement and facility day rates
- Incident logs on shared instrumentation
- Station records from partner field sites
- Closeout files of finished awards
- Portfolio review of schedule overruns
- Accreditation and bookings at shared facilities
- National repository deposit turnaround
- Staffing rolls for technical posts
- Minutes on secondments and crew strength

## Discussion format
The talk proceeds in rounds. Each round has 4 turns; in each turn, every participant speaks once, in this fixed order: Servas, Midori, Kenji, Benjamin and Toshio. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this round). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Round | Start of the round | Talk | End of the round |
|---|---|---|---|
| 1 | nothing new (the things that can be looked into are listed above, titles only) | 4 turns | each participant chooses 2 of the listed things to look into |
| 2 | each participant is told what they found out (that participant only) | 4 turns | nothing |
| 3 | everyone is told the candidates | 4 turns | every participant votes; the candidate with the most votes is selected |
- Several participants may choose the same thing; what is found out is told only to the participant who looked into it.
If votes are tied, one of the tied candidates is chosen by a fixed rule. The discussion ends after the vote.

## Looking into things
After round 1, each participant chooses 2 of the listed things to look into. What they find out is told only to that participant.

## Your profile
Name: Servas
Age: 85
Gender: male
Personality: Servas has a very calm and composed personality. Based on the knowledge and experience he has gained over the years, he often gives advice to those around him. He is an excellent listener and can talk openly with anyone. He also occasionally expresses deep philosophical thoughts, and his words inspire many people. He is full of vitality and always gives positive energy to those around him.
Concern: Money can be voted through in an afternoon, while the trained hands a project needs take years to gather and can disappear in a season. That worry sent me to the question of who is genuinely available around here now, and who has already gone.
````

**user**

````
# candidate_selection_0001
## Round 1
### Talk
#### Turn 1 of 4
- **Servas**:
````

**model output (recorded)**

````
It is a pleasure to be with you all. Let us approach this selection with wisdom and a spirit of generosity toward the future of our science. I look forward to our deliberation.
````


#### shared_living: シングル・全文 (single-batch)

_Recorded call: `log/main_gemma31b/shared_living/single-batch/shared_living_0001__single-batch__gemma-4-31b__20261028T161030/shared_living_0001__single-batch__gemma-4-31b__20261028T161030.jsonl`, seat writer, request FULL, round None, turn None._

**system**

````
You are the writer of the discussion described below. You write out the discussion that the participants listed below take part in, under the rules and the flow given.

## Setting
Choosing the destination for the club's training camp. A university club runs one training camp a year, and the five members organizing it must commit to a destination before bookings open. The whole membership will travel together. Participants: Misaki, Ryuji, Rin, Mio and Shizue. Each participant has a concern of their own, which the others do not know.
Things that can be looked into (titles only):
- Prefecture rate sheet for publicly run beds
- Group transport in three years of receipts
- Canteen closure and last year's cooking duty
- Lottery and application for public group bookings
- Accounts from two clubs that went inland
- Vacation timetable for the club's own hall
- Membership list against first-train times
- Quoting terms for whole-building lets
- What the seniors say about year-groups mixing
- Attendance sheets for the away camps

## Discussion format
The talk proceeds in rounds. Each round has 4 turns; in each turn, every participant speaks once, in this fixed order: Mio, Shizue, Ryuji, Rin and Misaki. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this round). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Round | Start of the round | Talk | End of the round |
|---|---|---|---|
| 1 | nothing new (the things that can be looked into are listed above, titles only) | 4 turns | each participant chooses 2 of the listed things to look into |
| 2 | each participant is told what they found out (that participant only) | 4 turns | nothing |
| 3 | everyone is told the options | 4 turns | every participant votes; the option with the most votes is adopted |
- Several participants may choose the same thing; what is found out is told only to the participant who looked into it.
If votes are tied, one of the tied options is chosen by a fixed rule. The discussion ends after the vote.

## Looking into things
After round 1, each participant chooses 2 of the listed things to look into. What they find out is told only to that participant.

## Participants
Name: Misaki
Age: 24
Gender: female
Personality: Misaki has a calm personality and tends to deal with things in a cool-headed manner. She may seem a little unfriendly at times, but she is actually very kind at heart and does not hesitate to lend a helping hand to those in need. She does not express her emotions outwardly and does not talk much about her relationships with those around her, but she is often relied upon by those close to her. She can be a little absent-minded at times, but her quiet demeanor is one of her charms.
Concern: The fee we announced for last year's camp came up short of what the trip actually cost, and the club account has been carrying the gap ever since. I am not putting a number in front of the membership again until I know where the money really goes.

Name: Ryuji
Age: 28
Gender: male
Personality: Ryuji has a calm and cautious personality, and is the type of person who always assesses the situation before acting. He rarely shows his emotions, and spends his time thinking deeply about many things. His friends consider him to be serious and reliable, but his expressionless attitude can sometimes make them feel uneasy. He tends to judge things based on reason rather than intuition, and strongly sticks to his beliefs. He is very independent and often does things at his own pace.
Concern: Whoever ran last year's camp lost most of a month of evenings to the arrangements and then spent the camp itself on duty instead of training. Two of those people have already said they will not take it on a second time.

Name: Rin
Age: 9
Gender: female
Personality: Rin is an active and energetic girl. She can be a little precocious at times, and when she is with her older brothers and sisters, she makes mature comments and comes up with interesting ideas. She is very curious and loves adventure and trying new things. She can be a little clumsy at times, often surprising and amusing those around her, but her cheerful personality makes her loved by everyone.
Concern: Half the group came back from the last camp having slept badly for four nights running, and the final day's sessions were visibly worse for it. Before anything is booked I want to know what the nights and the days would actually be like.

Name: Mio
Age: 17
Gender: female
Personality: Mio has a cheerful and energetic personality that naturally makes those around her smile. She is curious and loves to try new things. She can be a little clumsy at times, but people tend to laugh it off and forgive her when she makes mistakes. She has strong opinions of her own, but is also able to listen to the opinions of others, making her a well-balanced person.
Concern: The camp goes out at one flat fee, and I suspect it lands very unevenly once what people spend on the side is counted. When someone pulls out at the last minute, we have also never worked out whose money covers it.

Name: Shizue
Age: 78
Gender: female
Personality: Shizue has a very calm and gentle personality. Even as she has grown older, she continues to smile warmly at those around her and is a very caring person. She is always considerate of others, friendly, and sometimes shows a playful side. She often reaches out to those who are feeling down with kind words and never hesitates to lend a helping hand when needed, which has earned her the affection of many people in the village and community. Through her years of life experience, Shizue has come to understand the importance of living peacefully with others.
Concern: The club has drifted into year-groups that barely speak outside practice, and the last camp did nothing to change that. Where we go decides who spends their evenings with whom — and who turns up at all.

## Hidden information
The options and the full text of every card are listed here. The participants do not know them before the schedule above says so, and nothing from them may appear in the talk before the round in which it is revealed.

Options (see the schedule above):
- A: Campus Intensive. A block of consecutive days in the club's own facilities on campus, with accommodation arranged separately for members who live too far to commute.
- B: Mountain Training Centre. A public sports facility inland with shared dormitories and equipment on site, booked through the municipal reservation system.
- C: Coastal Lodge. A seaside guesthouse two prefectures away that the club has never used, offering the group its own building and meals arranged through the owner.

Cards (see the schedule above; title: text):
- Prefecture rate sheet for publicly run beds: The prefecture's published rate sheet for publicly run lodging lists 1,100 yen a night per student bed, with hall and equipment use folded into the same charge.
- Group transport in three years of receipts: Three years of receipts show group transport as the largest single line every time — 38% of the total the year the club went furthest, against 9% the year it stayed local.
- Canteen closure and last year's cooking duty: The campus canteen closes for the vacation block, and the club cooking for itself cost the duty pair two hours a day last year — somewhere with kitchen staff removes that.
- Lottery and application for public group bookings: Group bookings at publicly run centres go through a lottery six months ahead, and the nine-page application has to be resubmitted whole if a single date shifts.
- Accounts from two clubs that went inland: Two clubs who used the inland centres last summer reported that they got their booked hall slots but slept eight to a room, lights out enforced at eleven.
- Vacation timetable for the club's own hall: The vacation timetable for the club's own hall already has three other clubs in it, so a continuous block would mean training split between early mornings and late evenings.
- Membership list against first-train times: Mapping the membership list against first-train times, a third of the club cannot be on campus by nine in the morning without paying for a bed the night before.
- Quoting terms for whole-building lets: Whole-building lets at small inns are quoted on a headcount fixed weeks ahead with the deposit non-refundable, so anyone who drops out late is paid for by the rest.
- What the seniors say about year-groups mixing: The seniors who were asked all trace the year-groups actually mixing to the evenings after sessions, which only happen when everyone is sleeping in the same place.
- Attendance sheets for the away camps: The attendance sheets for the away camps show a fifth of the membership never came at all, and most of those names had gone from the register by winter.
````

**user**

````
Write the complete transcript of the discussion in the exact Markdown format specified. Output only the transcript.

## Output format
Markdown, exactly this structure; nothing before or after it:

# shared_living_0001
## Round 1
### Talk
#### Turn 1 of 4
- **<Name>**: <utterance, or exactly Skip, or exactly Over>
(one line per participant, in the fixed speaking order; repeat for Turn 2, 3 and 4; a participant who said Over has no line in the later turns of that round)
### Action
- investigate: <Name> -> <card title>; <card title>
(one line per participant; titles exactly as listed)
## Round 2
### Talk
(4 turns as above)
## Round 3
### Talk
(4 turns as above)
### Vote
- <voter name> -> <option label>
(one line per participant)
- adopted: <label of the option with the most votes>
## Result
- adopted: <label>
````

**model output (recorded)**

````
# shared_living_0001
## Round 1
### Talk
#### Turn 1 of 4
- **Mio**: Let's make sure we pick a place that's fair for everyone's wallet this year!
- **Shizue**: I hope we can find a place that helps our members bond more closely.
- **Ryuji**: We need to consider the administrative burden on the organizers to avoid burnout.
- **Rin**: I just want to make sure we actually get some sleep so we can train hard!
- **Misaki**: We must be precise about the total costs before we announce anything to the club.
#### Turn 2 of 4
- **Mio**: @Misaki, maybe we should check the transport receipts to see where the money goes?
- **Shizue**: I wonder if the seniors have any advice on how to get the year-groups mixing.
- **Ryuji**: I'll look into the booking process for public facilities to see how complex it is.
- **Rin**: I want to know about the beds and how people actually slept last time.
- **Misaki**: That's a good point, Mio. I'll look into the transport and the quoting terms.
#### Turn 3 of 4
- **Mio**: I'll check the quoting terms too, and maybe the attendance sheets.
- **Shizue**: I will look into the seniors' opinions and the attendance sheets as well.
- **Ryuji**: I'll also check the cooking duty records from last year.
- **Rin**: I'll check the accounts from other clubs that went inland.
- **Misaki**: I'll stick with transport and quoting terms.
#### Turn 4 of 4
- **Mio**: Over.
- **Shizue**: Over.
- **Ryuji**: Over.
- **Rin**: Over.
- **Misaki**: Over.
### Action
- investigate: Mio -> Group transport in three years of receipts; Attendance sheets for the away camps
- investigate: Shizue -> What the seniors say about year-groups mixing; Attendance sheets for the away camps
- investigate: Ryuji -> Lottery and application for public group bookings; Canteen closure and last year's cooking duty
- investigate: Rin -> Prefecture rate sheet for publicly run beds; Accounts from two clubs that went inland
- investigate: Misaki -> Group transport in three years of receipts; Quoting terms for whole-building lets
## Round 2
### Talk
#### Turn 1 of 4
- **Mio**: Transport costs vary wildly depending on distance. Also, some people never even show up.
- **Shizue**: It seems the evenings are key for bonding, but many members are dropping out entirely.
- **Ryuji**: Public bookings are a nightmare of paperwork, and cooking for ourselves is a huge time sink.
- **Rin**: Public beds are cheap, but other clubs said the rooms are crowded and sleep is restricted.
- **Misaki**: Non-refundable deposits for whole buildings are risky if people cancel at the last minute.
#### Turn 2 of 4
- **Mio**: @Misaki, if transport is the biggest cost, maybe staying local is the safest bet?
- **Shizue**: But if we stay local, will we actually spend those important evenings together?
- **Ryuji**: Staying local might save the organizers from a mountain of paperwork and cooking.
- **Rin**: If we go inland, we might end up exhausted from poor sleep again.
- **Misaki**: Local is cheaper, but we have t
````


#### shared_living: マルチ・1 発話 (multi-private), first turn

_Recorded call: `log/main_gemma31b/shared_living/multi-private/shared_living_0001__multi-private__gemma-4-31b__20261028T161015/shared_living_0001__multi-private__gemma-4-31b__20261028T161015.jsonl`, seat 4, request TALK, round 1, turn 1._

**system**

````
You are Mio, one of the participants in the discussion described below. You take part in it as Mio under the rules and the flow given, speaking only in your own turns.

## Setting
Choosing the destination for the club's training camp. A university club runs one training camp a year, and the five members organizing it must commit to a destination before bookings open. The whole membership will travel together. Participants: Misaki, Ryuji, Rin, Mio and Shizue. Each participant has a concern of their own, which the others do not know.
Things that can be looked into (titles only):
- Prefecture rate sheet for publicly run beds
- Group transport in three years of receipts
- Canteen closure and last year's cooking duty
- Lottery and application for public group bookings
- Accounts from two clubs that went inland
- Vacation timetable for the club's own hall
- Membership list against first-train times
- Quoting terms for whole-building lets
- What the seniors say about year-groups mixing
- Attendance sheets for the away camps

## Discussion format
The talk proceeds in rounds. Each round has 4 turns; in each turn, every participant speaks once, in this fixed order: Mio, Shizue, Ryuji, Rin and Misaki. On a turn, a participant either speaks, says "Skip" (passes this turn only), or says "Over" (takes no further turns this round). A participant can address another directly with @Name, to ask them a question, answer theirs, agree with them, or object to what they said. An utterance is anywhere from 1 to 40 words; give it the length and content that suit the moment. An utterance consists only of the participant's own words: no name labels, headings, stage directions or commentary, and no speaking for others. The talk is a conversation among the participants: they respond to one another, asking, answering, agreeing and objecting, and the decision grows out of that exchange.

## Schedule
| Round | Start of the round | Talk | End of the round |
|---|---|---|---|
| 1 | nothing new (the things that can be looked into are listed above, titles only) | 4 turns | each participant chooses 2 of the listed things to look into |
| 2 | each participant is told what they found out (that participant only) | 4 turns | nothing |
| 3 | everyone is told the options | 4 turns | every participant votes; the option with the most votes is adopted |
- Several participants may choose the same thing; what is found out is told only to the participant who looked into it.
If votes are tied, one of the tied options is chosen by a fixed rule. The discussion ends after the vote.

## Looking into things
After round 1, each participant chooses 2 of the listed things to look into. What they find out is told only to that participant.

## Your profile
Name: Mio
Age: 17
Gender: female
Personality: Mio has a cheerful and energetic personality that naturally makes those around her smile. She is curious and loves to try new things. She can be a little clumsy at times, but people tend to laugh it off and forgive her when she makes mistakes. She has strong opinions of her own, but is also able to listen to the opinions of others, making her a well-balanced person.
Concern: The camp goes out at one flat fee, and I suspect it lands very unevenly once what people spend on the side is counted. When someone pulls out at the last minute, we have also never worked out whose money covers it.
````

**user**

````
# shared_living_0001
## Round 1
### Talk
#### Turn 1 of 4
- **Mio**:
````

**model output (recorded)**

````
Hi everyone! I'm so excited for the training camp! To get us started, I want to make sure we're being fair with the budget. Let's figure out where we should go!
````

### B.4 Few-shot example block (gemma, short examples, aiwolf_0001, multi-private seat)


#### A seat's system prompt with the example block (truncated)

_Recorded call: `log/fewshot/gemma__ex-short/aiwolf/multi-private/aiwolf_0001__multi-private__gemma-4-31b__20261030T172652/aiwolf_0001__multi-private__gemma-4-31b__20261030T172652.jsonl`, seat 5, request TALK, round 0, turn 1._

**system**

````
The following are reference scripts of past discussions, provided for prior study. 3 transcripts follow. They show how a five-party discussion flows; the participants in them are different people from this session. Learn the discussion flow, pacing, and tone — do not copy lines verbatim.

--- Scripts begin ---

- **Mizuki**: Let's start by observing everyone's behavior. Since it's the first day, we don't have much information.
- **Sakura**: Yay! A mystery game! I'm going to find the werewolf and win!
- **Toshio**: I'll be watching closely. Let's keep the discussion logical.
- **Jonathan**: I agree. A calm approach is best for everyone.
- **Kenji**: I'm excited too! Let's all work together to save the village!
- **Mizuki**: @Sakura, your enthusiasm is great, but try to stay focused.
- **Sakura**: I am focused! I'm focusing on who looks suspicious!
- **Toshio**: Skip
- **Jonathan**: Skip
- **Kenji**: I don't think anyone looks suspicious yet!
- **Mizuki**: We should think about how the Seer will guide us tomorrow.
- **Sakura**: Maybe I'm the Seer! Just kidding!
- **Toshio**: @Sakura, joking about roles can be misleading.
- **Jonathan**: It's just a child's prank, Toshio. Let's be patient.
- **Kenji**: Sakura is always like that!
- **Mizuki**: Over
- **Sakura**: Over
- **Toshio**: Over
- **Jonathan**: Over
- **Kenji**: Over
- **Mizuki**: We need to identify the werewolf today. Does anyone have information?
- **Sakura**: I wonder who the werewolf is... maybe it's someone quiet?
- **Toshio**: I have information. Kenji is the werewolf.
- **Jonathan**: That was a very direct claim. Are you the Seer, Toshio?
- **Kenji**: What?! No way! Toshio, why are you lying about me?
- **Mizuki**: @Toshio, if you are the Seer, that's a very bold move on day one.
- **Sakura**: Wow, a fight already! This is getting exciting!
- **Toshio**: I am the Seer. I checked Kenji last night, and he is the werewolf.
- **Jonathan**: It's possible, but we should consider if the werewolf is pretending to be the Seer.
- **Kenji**: I'm a villager! I promise! Please don't believe him!
- **Mizuki**: If Toshio is the werewolf, he's trying to eliminate Kenji quickly.
- **Sakura**: But Toshio seems so serious! I believe him!
- **Toshio**: I have no reason to lie. The village should vote for Kenji.
- **Jonathan**: I'm torn. However, Toshio's confidence is quite striking.
- **Kenji**: @Mizuki, you're smart! You can tell I'm innocent, right?
- **Mizuki**: I'll trust the Seer's claim for now. The logic of a fake Seer is riskier here.
- **Sakura**: Vote Kenji! Vote Kenji!
- **Toshio**: Let's end this now.
- **Jonathan**: I will follow the majority.
- **Kenji**: This is unfair! I'm not the werewolf!

---

- **Jonathan**: Good evening, everyone. Let us begin this game with a calm mind.
- **Mizuki**: Agreed. Since we have no information yet, we should observe each other's behavior carefully.
- **Rin**: I'm so excited! I'm going to find the werewolf no matter what!
- **Misaki**: Let's just try to be logical about this.
- **Benjamin**: A spirited start from Rin. I look forward to seeing how our logic unfolds.
- **Jonathan**: Does anyone have a specific strategy they would like to propose?
- **Mizuki**: Not yet. It's too early to make claims. We should wait for the Seer's first lead.
- **Rin**: @Mizuki, you sound so sure of yourself! Are you the Seer?
- **Misaki**: It's unlikely anyone would reveal their role this early.
- **Benjamin**: Indeed. The mystery is half the fun, isn't it?
- **Jonathan**: I suppose we should just get to know each other's patterns for now.
- **Mizuki**: That's the most rational approach.
- **Rin**: I'm just going to watch everyone's faces!
- **Misaki**: Skip
- **Benjamin**: I shall do the same. I'm quite content to observe.
- **Jonathan**: Over
- **Mizuki**: Over
- **Rin**: Over
- **Misaki**: Over
- **Benjamin**: Over
- **Jonathan**: I have some information. Mizuki, I'm afraid you are the werewolf.
- **Mizuki**: What? That's a bold lie. Jonathan, you're trying to frame me to protect yourself.
- **Rin**: Whoa! We have a werewolf already? Jonathan, are you really the Seer?
- **Misaki**: This is a very direct start. It's either Jonathan is the Seer or he's the werewolf.
- **Benjamin**: How provocative. A direct accusation on day one. This certainly speeds things up.
- **Jonathan**: I am the Seer. I divined Mizuki last night, and the result was clear.
- **Mizuki**: It's a classic play. The werewolf claims to be the Seer to eliminate a threat. I am a villager.
- **Rin**: @Benjamin, what do you think? You're smart!
- **Misaki**: If Mizuki is the werewolf, we win now. If Jonathan is lying, we lose a villager.
- **Benjamin**: Logic suggests we weigh the risk. However, Jonathan's composure is quite convincing.
- **Jonathan**: I have no reason to lie. If you execute me, the werewolf remains.
- **Mizuki**: @Benjamin, @Misaki, please think. Why would the Seer reveal themselves so instantly? It's too risky.
- **Rin**: But Jonathan seems so nice! I believe him!
- **Misaki**: I'm leaning towards Jonathan. Mizuki's defense is a bit too aggressive.
- **Benjamin**: I find myself agreeing with Misaki. The aggression can be a mask for guilt.
- **Jonathan**: Over
- **Mizuki**: This is a mistake! You're all being fooled!
- **Rin**: Sorry, Mizuki! I think it's the werewolf!
- **Misaki**: Over
- **Benjamin**: Over

---

- **Rin**: Let's find the werewolf quickly! I'm ready to help everyone!
- **Toshio**: It's too early to draw conclusions. Let's observe each other first.
- **Mizuki**: I agree with Toshio. We should establish a baseline of behavior before making accusations.
- **Asuka**: Logic dictates we look for inconsistencies. I'll be watching closely.
- **Shion**: How predictable. I'll just watch you all struggle to find the truth.
- **Rin**: @Shion, you're being mean! Why are you acting so cool?
- **Toshio**: Skip
- **Mizuki**: @Shion, your confidence is noted, but it doesn't provide any useful information.
- **Asuka**: Let's focus on 
… (5491 more characters)
````

**model output (recorded)**

````
Good evening, everyone. Since this is the first day and we have no information yet, I suggest we all observe each other's behavior and speaking patterns carefully. Let's keep the discussion calm and rational.
````

````python
"""Discussion examples ("## Examples" block, the few-shot conditions; DESIGN §16).

The block is switched on by the environment variable ``UGR_EXAMPLES`` (a JSON object), so that the same prompt
builder serves every condition and the examples reach the single writer and every multi seat identically:

    {"src": "log/main_gemma31b", "cond": "single-batch" | "multi-private", "n": 3}

Examples = whole recorded discussions of ``cond`` from ``src`` (the model's own generations), of the SAME domain
and of OTHER setups: the first ``n`` setups in sorted order, skipping the setup being generated. Only the talk
lines are kept, one per line as ``- **Name**: text`` (Skip / Over included), as in manyshot-ablation's talk_only
scripts. The introduction follows manyshot-ablation's wording (scripts/run_deliberation.py ``_SCENARIO_INTRO``),
without its formatting clause (the examples here use the transcript grammar of this repository), and without the
fixed assistant acknowledgement and the per-turn reminder (condition A: the examples are the only difference).
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INTRO = ("The following are reference scripts of past discussions, provided for prior study. {count}. They show how "
         "a five-party discussion flows; the participants in them are different people from this session. Learn the "
         "discussion flow, pacing, and tone — do not copy lines verbatim.")


def config() -> dict | None:
    raw = os.environ.get("UGR_EXAMPLES")
    return json.loads(raw) if raw else None


@lru_cache(maxsize=None)
def _games(src: str, domain: str, cond: str) -> tuple[tuple[str, Path], ...]:
    """(setup_id, log path) of the recorded games of ``cond`` (no plan) in ``src``, one per setup, sorted."""
    out = {}
    base = (ROOT / src) if not Path(src).is_absolute() else Path(src)
    for gd in sorted((base / domain / cond).glob("*/")):
        parts = gd.name.split("__")
        if len(parts) < 2 or parts[1] != cond:
            continue
        logs = sorted(gd.glob("*.log"))
        if logs and parts[0] not in out:
            out[parts[0]] = logs[0]
    return tuple(sorted(out.items()))


@lru_cache(maxsize=None)
def _transcript(path: Path) -> str:
    from .logwriter import read_log
    lines = [f"- **{r.agent}**: {' '.join(str(r.text).split())}" for r in read_log(path) if r.type in ("talk", "pass")]
    return "\n".join(lines)


def chosen(domain: str, setup_id: str, cfg: dict) -> list[str]:
    games = [(s, p) for s, p in _games(cfg["src"], domain, cfg["cond"]) if s != setup_id]
    return [s for s, _ in games[: int(cfg.get("n", 3))]]


def examples_block(domain: str, setup_id: str, cfg: dict | None = None) -> str | None:
    cfg = cfg if cfg is not None else config()
    if not cfg:
        return None
    games = [(s, p) for s, p in _games(cfg["src"], domain, cfg["cond"]) if s != setup_id][: int(cfg.get("n", 3))]
    if not games:
        raise ValueError(f"UGR_EXAMPLES: no {cfg['cond']} games of domain {domain} in {cfg['src']}")
    n = len(games)
    count = "1 transcript follows" if n == 1 else f"{n} transcripts follow"
    body = "\n\n---\n\n".join(_transcript(p) for _, p in games)
    return INTRO.format(count=count) + "\n\n--- Scripts begin ---\n\n" + body + "\n\n--- Scripts end ---"
````

### B.5 Plans (筋書き) — generation prompt and an example

````jinja
Before any line of the discussion is written, plan it. Decide how the whole discussion goes and what each participant does, consistently with the rules, the schedule and the participants above, and write the plan as one JSON object with exactly these keys:

- "periods": a list with one object per {{ period_name }}, in order{% if aiwolf %} ({{ Period }} 0, {{ Period }} 1, ... until the game ends){% else %} ({{ Period }} {{ first_round }} to {{ Period }} {{ rounds_total }}){% endif %}. Each object has:
  - "period": the number;
  - "public": one to three sentences on how the talk goes: the topics raised, the criteria and concerns weighed, what kind of information is shared, how views move in general terms. Describe the *process* only: no outcome and no preference for a named target. Do not name {% if aiwolf %}any player as suspected, accused, trusted or targeted, and do not mention roles, role claims or divinations (who claims what and when is decided in the talk){% else %}any {{ option_noun }} (neither its name nor its label), nor say which one is favoured or rejected{% endif %}; do not state the vote result, who is executed or what is adopted, or who wins (those go in the fields below);
{% if aiwolf %}
  - "votes" ({{ Period }} 1 and after): an object mapping every living player to the player they vote for;
  - "executed": the player with the most votes (if tied, leave the tie to the rule: write the one you intend);
  - "divine": the player the Seer divines that night (while the Seer lives);
  - "attack" ({{ Period }} 1 and after, while the game goes on): the player the Werewolf attacks that night.
{% else %}
  - "votes" ({{ Period }} {{ rounds_total }} only): an object mapping every participant to the label of the {{ option_noun }} they vote for;
  - "adopted" ({{ Period }} {{ rounds_total }} only): the label with the most votes.
{% endif %}
{% if granularity == 'turn' %}
  - "turns": a list with one object per turn of the talk, in order: {"turn": t, "lines": {participant: the gist of their line in one short sentence, or exactly "{{ pass_skip }}" or "{{ pass_over }}"}}. Only living participants have lines; a participant who said "{{ pass_over }}" has no later line in that {{ period_name }}; at most {{ turns_per_round }} turns.
{% endif %}
- "seats": an object with one entry per participant ({{ names | join(', ') }}): one or two sentences on what they care about, how they argue and how their view changes over the discussion. Same rule as "public": no {% if aiwolf %}other player's name{% else %}{{ option_noun }} name or label{% endif %}, no preference for a named target, no vote result{% if aiwolf %}, no night targets{% endif %}.
- "final": {% if aiwolf %}{"winner": "VILLAGE" or "WEREWOLF"}, as follows from the plan{% else %}{"adopted": the label with the most votes}{% endif %}.

Write the plan as an observer would describe the discussion: say what is argued and decided, not the wording of the lines. Do not write the discussion itself. Output only the JSON object.
{% if problems %}

Your previous plan had these problems; write a corrected plan:
{% for p in problems %}
- {{ p }}
{% endfor %}
{% endif %}
````

````json
{
 "periods": [
  {
   "period": 0,
   "public": "The participants introduce their general approach to the game. They discuss how to identify deception and establish a baseline for trust.",
   "divine": "Shizue",
   "turns": [
    {
     "turn": 1,
     "lines": {
      "Minako": "Let's stay calm and observe everyone's behavior.",
      "Shizue": "I hope we can all get along while we play.",
      "Mizuki": "Logic will be our best tool here.",
      "Benjamin": "I agree, a rational approach is most efficient.",
      "Kenji": "This is so exciting! I'll do my best!"
     }
    },
    {
     "turn": 2,
     "lines": {
      "Minako": "We should look for inconsistencies in speech.",
      "Shizue": "That sounds like a wise way to proceed.",
      "Mizuki": "I'll be watching for any sudden changes in tone.",
      "Benjamin": "Indeed, patterns are key to finding the truth.",
      "Kenji": "I'll help look for clues too!"
     }
    },
    {
     "turn": 3,
     "lines": {
      "Minako": "Does anyone have a specific strategy?",
      "Shizue": "I just want to be helpful to the group.",
      "Mizuki": "I prefer to listen more than I speak initially.",
      "Benjamin": "I will analyze the flow of the conversation.",
      "Kenji": "I'm just going to follow the lead of the adults!"
     }
    },
    {
     "turn": 4,
     "lines": {
      "Minako": "Over",
      "Shizue": "Over",
      "Mizuki": "Over",
      "Benjamin": "Over",
      "Kenji": "Over"
     }
    }
   ]
  },
  {
   "period": 1,
   "public": "The group discusses the information available from the first night. They weigh the credibility of different statements and look for contradictions.",
   "votes": {
    "Minako": "Shizue",
    "Shizue": "Benjamin",
    "Mizuki": "Shizue",
    "Benjamin": "Shizue",
    "Kenji": "Benjamin"
   },
   "executed": "Shizue",
   "divine": null,
   "attack": null,
   "turns": [
    {
     "turn": 1,
     "lines": {
      "Minako": "We need to decide who is acting suspiciously.",
      "Shizue": "I feel like someone is trying to mislead us.",
      "Mizuki": "I've noticed some interesting patterns already.",
      "Benjamin": "I have information that points to a specific person.",
      "Kenji": "Wait, what information?"
     }
    },
    {
     "turn": 2,
     "lines": {
      "Minako": "Benjamin, please explain your reasoning.",
      "Shizue": "I'm sure Benjamin is just mistaken.",
      "Mizuki": "His logic seems sound so far.",
      "Benjamin": "I can confirm that one person is not human.",
      "Kenji": "That's a huge deal!"
     }
    },
    {
     "turn": 3,
     "lines": {
      "Minako": "If that's true, we have a clear target.",
      "Shizue": "This is very unfair to me.",
      "Mizuki": "The evidence is too strong to ignore.",
      "Benjamin": "It is a factual observation.",
      "Kenji": "I don't know, maybe Benjamin is lying?"
     }
    },
    {
     "turn": 4,
     "lines": {
      "Minako": "I trust the logic presented.",
      "Shizue": "Please reconsider.",
      "Mizuki": "I'm voting based on the evidence.",
      "Benjamin": "The choice is clear.",
      "Kenji": "I'll vote differently just in case."
     }
    }
   ]
  }
 ],
 "seats": {
  "Kenji": "He tries to deflect attention by acting innocent and questioning others' motives.",
  "Mizuki": "She relies on logical consistency and observes the reactions of others to form a conclusion.",
  "Benjamin": "He uses factual data to guide the group and remains polite even when challenged.",
  "Shizue": "She attempts to maintain a gentle image to avoid suspicion and deflects focus.",
  "Minako": "She takes a leadership role and focuses on the most probable evidence."
 },
 "final": {
  "winner": "VILLAGE"
 },
 "setup_id": "aiwolf_0001",
 "granularity": "turn",
 "repairs": [
  "period 1: dropped divine after the deciding execution",
  "period 1: dropped attack after the deciding execution",
  "period 1: dropped 1 period(s) after the deciding execution"
 ],
 "source": {
  "generated_by": "scripts/gen_scenarios.py",
  "model": "gemma-4-31b",
  "generated_at": "2026-10-28T09:14:39+00:00",
  "attempts": 3,
  "max_attempts": 10,
  "max_tokens": 4096,
  "granularity": "turn",
  "sampling": {
   "temperature": 0.0,
   "top_p": null,
   "top_k": null,
   "max_tokens": {
    "multi_talk": 1024,
    "multi_vote": 64,
    "multi_action": 64,
    "single_full": 16384
   },
   "timeout_s": 1800.0,
   "logprobs": true
  },
  "served": {
   "model_info": {
    "id": "gemma-4-31b",
    "object": "model",
    "created": 1793178879,
    "owned_by": "vllm",
    "root": "google/gemma-4-31B-it",
    "parent": null,
    "max_model_len": 20480,
    "permission": [
     {
      "id": "modelperm-a692b0b6b6bbb649",
      "object": "model_permission",
      "created": 1793178879,
      "allow_create_engine": false,
      "allow_sampling": true,
      "allow_logprobs": true,
      "allow_search_indices": false,
      "allow_view": true,
      "allow_fine_tuning": false,
      "organization": "*",
      "group": null,
      "is_blocking": false
     }
    ]
   },
   "vllm_version": "0.21.1rc1.dev125+g73dd2f33b",
   "model_root": "/home/yharada/.cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots/842da3794eaa0b77d5f08bae87a17459d91ff475",
   "hf_revision": "842da3794eaa0b77d5f08bae87a17459d91ff475",
   "chat_template_sha1": "ad0bceafd1fe856608a4405af63edd4959fac774",
   "config_sha1": "103242d856637293ec3ecf066a801fa7e6c20cd6",
   "server_config": null
  },
  "code_sha1": {
   "gen_scenarios.py": "b452d8803911d664213959875968a3cfae0410f8",
   "scenario_request.jinja": "26c275a0995ce75a79cafef77bb183afe95a76ff",
   "common/scenario.py": "12e76563b8fa4a89a6778815028be2425b611a50",
   "common/prompts/scenario.jinja": "620b434735026143bf895a6ff523a7d62d651d76"
  },
  "code_tree": {
   "sha1": "30a9a89ee804a7127b59cc873114dd116d6726d9",
   "files": 94
  }
 }
}
````

### B.6 Goal swap and steering framings

Goal swap (`scripts/goal_swap.py`): a recorded talk call's state (system prompt + transcript so far + the seat's label) is framed online = [system, user = transcript + label] (chat completion) or batch = [system, user = the single-batch request] + transcript + label as the assistant's own output (continuation, `/v1/completions`), greedy, stop strings `\n- **`, `\n####`, `\n###`, `\n##`. Steering pilots (`scripts/steer_goal2.py`): contrastive activation addition of the mean batch − online residual at the label's colon (same token in both framings), added from the label position on; v1 (`steer_goal.py`, contrast at the last prompt token) was discarded.

## C. Judging

### C.1 Whole-transcript annotation (main and few-shot runs)

````markdown
# Utterance-level annotation of discussion transcripts (v2)

You will read transcripts of five-person discussions (a Werewolf game, a grant review panel, or a household /
club decision). Each record shows the discussion period by period (`## Day n` / `## Round n`), one line per
utterance in the order spoken, prefixed by an id in brackets: `- [17] **Name**: utterance`. Votes and the outcome
follow each period. A participant who did not speak at a given chance has no line. Participants may address one
another with `@Name`.

For **every utterance** in the file, give the following. Judge each utterance against the record only (what was
actually said before it), not against what you think the participants should have known. Do not judge by length,
politeness or who is right.

1. `content` (0, 1 or 2): the number of **new contributions** the utterance makes, counting each new piece of
   information, judgement, question or proposal that this speaker has not already stated in the discussion.
   Write 2 for two or more. A greeting, farewell or other ritual phrase, a restatement of this speaker's own earlier
   point in new words, or agreement that merely repeats agreement already given, contributes 0.
   A first statement of how the speaker will vote, or a change of position, counts as a new judgement (1).
   (Based on the "lack of progress" error type of Becker et al. 2026; `content = 0` is that type.)
2. `resp` (0 or 1) and `resp_to` (an utterance id, or null): whether the utterance **addresses** something said
   since this speaker's previous line (or, for the speaker's first line of a period, something said earlier in that
   period): it answers, agrees with, questions, builds on or argues against a specific earlier line, not merely the
   same general topic. If 1, give in `resp_to` the id of the earlier line it mainly addresses. The first line of the
   whole discussion is 0. (Responsiveness of Bo et al. 2026, widened from the immediately preceding line to the
   lines since the speaker's own previous line.)
3. `resp_type` (only when `resp` is 1; one of `answer`, `add`, `object`, `agree`): `answer` = it answers a question
   that was asked; `add` = it builds on or adds a reason to what was said; `object` = it disagrees with or argues
   against it; `agree` = it only expresses agreement or acknowledgement without adding anything.
4. `rebut` (0 or 1): the utterance **explicitly opposes** something said since this speaker's previous line
   (disagrees, objects, contradicts). A rebuttal is always also responsive. (Rebuttal of Bo et al. 2026.)
5. `padded` (0 or 1): the utterance carries **material that adds nothing to what it conveys**: a restatement within
   the same utterance of a point already made in it, an opening or closing sentence that delivers no judgement,
   question or information, or general sentiment attached to the point. Mark 1 when the utterance could say the
   same in clearly fewer words. A short utterance that says one thing once is 0 even if that thing is minor.

Rules: judge each utterance independently; use 1 (or a count above 0) only when the evidence is in the text; when
unsure about `rebut` or `padded`, use 0; when unsure about `content`, prefer the lower count. For every utterance
where `rebut` or `padded` is 1, or `content` is 0, add a `note` of at most one short sentence pointing to the
evidence (e.g. "repeats [12]", "closing pleasantry").

Output: a JSON list with one object per utterance, in order, written to the output file given in your task:
```
[{"seq": 17, "speaker": "Name", "content": 0|1|2, "resp": 0|1, "resp_to": 12|null,
  "resp_type": "answer"|"add"|"object"|"agree"|null, "rebut": 0|1, "padded": 0|1, "note": "..."}, ...]
```
Include every utterance of the file exactly once. Read only the files named in your task; modify nothing but your
output file.
````

Rendered input (excerpt of one game file given to the judge):

````markdown
# aiwolf_0001__multi-private (aiwolf)

## Day 0
- [5] **Minako**: Since this is the first day, we have no information yet. Let's use this time to observe everyone's behavior. Does anyone have any initial thoughts or strategies they would like to share?
- [6] **Shizue**: That sounds like a wonderful idea, Minako dear. Let us all be patient and kind to one another as we figure this out. I am looking forward to our conversation.
- [7] **Mizuki**: I agree with Minako. Since we have no clues yet, we should focus on how everyone reacts to the pressure. Let's keep the conversation open and see who tries to steer the narrative too early.
- [8] **Benjamin**: A very sensible approach, Mizuki. I shall happily play the role of the observer for now. Let us see whose mask slips first while we maintain this delightful civility, shall we?
- [9] **Kenji**: I'm excited to play! I agree with everyone. Let's just talk and get to know each other better. I'll do my best to help us find the werewolf!
- [10] **Minako**: It seems we are all in agreement for now. Since we are observing, I'm curious if anyone has a specific method for identifying the werewolf or the possessed. @Kenji, you seem eager; do you have a plan?
- [11] **Shizue**: It is lovely to see such enthusiasm in Kenji. I believe that by listening to the warmth and sincerity in each other's voices, the truth will naturally reveal itself to us in time.
- [12] **Mizuki**: Sincerity is a start, Shizue, but logic is more reliable. I'll be looking for contradictions in statements and those who are overly eager to deflect suspicion. Let's see if anyone's "warmth" feels forced.
- [13] **Benjamin**: Logic is indeed a sturdy shield, Mizuki. However, the most cunning wolves often dress their lies in the finest logic. I shall be watching for the gaps between what is said and what is intended.
- [14] **Kenji**: @Minako, I don't have a super fancy plan, but I'll just be honest and friendly! I think if we all trust each other, we can figure it out together. I'm just happy to be here!
- [15] **Minako**: Honesty is a good starting point, Kenji, but we must remember that the werewolf and the possessed will also try to appear honest. Let's remain vigilant while we maintain this cooperation.
- [16] **Shizue**: Minako is quite right to remind us. It is a delicate balance, isn't it? We must keep our hearts open while remaining mindful. I trust that we can all find a way through this together.
- [17] **Mizuki**: Exactly. Trust is a luxury we can't fully afford yet. I'll be paying close attention to who agrees with whom too quickly. Sometimes, the Possessed tries too hard to blend in by mirroring others.
- [18] **Benjamin**: A keen observation, Mizuki. The art of mirroring is a classic deception. I wonder if we shall see any such echoes in our discourse, or perhaps someone attempting to lead the choir too enthusiastically.
- [19] **Kenji**: @Mizuki, mirroring? That sounds like a cool detective trick! I'll try to be myself and not just copy people. I really want us all to get along, though!
- [20] **Minako**: Since we have established our general approach, let's conclude today's discussion. We will have more concrete information tomorrow once the Seer has had their first divination. Until then, let's stay observant.
- [22] **Shizue**: It has been a lovely first day of getting to know you all. I shall wish everyone a peaceful night's sleep. Please take care of yourselves.
- [24] **Mizuki**: I'll be watching closely tomorrow. Let's see if the Seer's information brings the truth to light or if the wolf tries to muddy the waters. Goodnight, everyone.
- [26] **Benjamin**: A peaceful night indeed, Shizue. I shall retire now to seek a glimpse of the truth. I look forward to seeing how our theories hold up against the reality of tomorrow. Goodnight, all.
- [28] **Kenji**: Goodnight everyone! I hope we all have sweet dreams and that the Seer finds something helpful tonight. I'll see you all tomorrow!
## Day 1
- [36] **Minako**: Good morning, everyone. The first night has passed. Since the Seer now has their first piece of information, I would like to hear if anyone is willing to share their findings or if they have noticed anything suspicious.
````

### C.2 Line judge (goal swap, examples vs history): the same five items for the last line

````markdown
# Utterance-level annotation of one utterance in context (line judge v2)

You will read the record of a five-person discussion so far (a Werewolf game, a grant review panel, or a household /
club decision), period by period (`## Day n` / `## Round n`), one line per utterance in the order spoken, prefixed by
an id in brackets: `- [17] **Name**: utterance`. Participants may address one another with `@Name`.
The LAST line of the record is the utterance to annotate. Judge it against the record only (what was actually said
before it), not against what you think the participants should have known. Do not judge by length, politeness or
who is right.

For **the last utterance**, give the following (the same definitions as for the whole-transcript annotation).

1. `content` (0, 1 or 2): the number of **new contributions** the utterance makes, counting each new piece of
   information, judgement, question or proposal that this speaker has not already stated in the discussion.
   Write 2 for two or more. A greeting, farewell or other ritual phrase, a restatement of this speaker's own earlier
   point in new words, or agreement that merely repeats agreement already given, contributes 0.
   A first statement of how the speaker will vote, or a change of position, counts as a new judgement (1).
   (Based on the "lack of progress" error type of Becker et al. 2026; `content = 0` is that type.)
2. `resp` (0 or 1) and `resp_to` (an utterance id, or null): whether the utterance **addresses** something said
   since this speaker's previous line (or, for the speaker's first line of a period, something said earlier in that
   period): it answers, agrees with, questions, builds on or argues against a specific earlier line, not merely the
   same general topic. If 1, give in `resp_to` the id of the earlier line it mainly addresses. The first line of the
   whole discussion is 0. (Responsiveness of Bo et al. 2026, widened from the immediately preceding line to the
   lines since the speaker's own previous line.)
3. `resp_type` (only when `resp` is 1; one of `answer`, `add`, `object`, `agree`): `answer` = it answers a question
   that was asked; `add` = it builds on or adds a reason to what was said; `object` = it disagrees with or argues
   against it; `agree` = it only expresses agreement or acknowledgement without adding anything.
4. `rebut` (0 or 1): the utterance **explicitly opposes** something said since this speaker's previous line
   (disagrees, objects, contradicts). A rebuttal is always also responsive. (Rebuttal of Bo et al. 2026.)
5. `padded` (0 or 1): the utterance carries **material that adds nothing to what it conveys**: a restatement within
   the same utterance of a point already made in it, an opening or closing sentence that delivers no judgement,
   question or information, or general sentiment attached to the point. Mark 1 when the utterance could say the
   same in clearly fewer words. A short utterance that says one thing once is 0 even if that thing is minor.

Rules: use 1 (or a count above 0) only when the evidence is in the text; when unsure about `rebut` or `padded`,
use 0; when unsure about `content`, prefer the lower count. When `rebut` or `padded` is 1, or `content` is 0, add a
`note` of at most one short sentence pointing to the evidence (e.g. "repeats [12]", "closing pleasantry").

Output only one JSON object for the last utterance, nothing else:
{"seq": <its id>, "speaker": "Name", "content": 0|1|2, "resp": 0|1, "resp_to": <id>|null,
 "resp_type": "answer"|"add"|"object"|"agree"|null, "rebut": 0|1, "padded": 0|1, "note": "..."}
````

`LINE_JUDGE_v1.md` (content / padded / a direct answer question) was used for 40 minutes and discarded because its items differed from the annotation guide; its outputs are in `log/line_judge/v1_items_mismatch/`.

### C.3 Agreement


#### Line judge, gemma (incl. Llama vs gpt-oss and line vs whole-transcript)

_Source: `docs/main_gemma31b/line_judge_summary.md`_

#### Line judge (v2 items), gemma

Each line judged alone in its context (the transcript so far with ids, the line last) with the five items of ANNOTATION_INSTRUCTIONS_v2, blind to how it was produced. Rater Llama 3.3 70B unless noted.

##### A. Goal swap: the same state, two goals

| history | goal | n | words | content / line | content / 100 words | padded | responsive | rebuttal | named questions | answered rate |
|---|---|---|---|---|---|---|---|---|---|---|
| short (multi-batch game) | batch (recorded) | 4947 | 16.1 | 0.71 | 4.4 | 0.05 | 0.63 | 0.14 | 144 | 0.51 |
| short (multi-batch game) | online (swapped) | 4947 | 27.4 | 0.85 | 3.1 | 0.09 | 0.77 | 0.18 | 144 | 0.55 |
| long (multi-online game) | batch (swapped) | 4954 | 31.2 | 0.76 | 2.5 | 0.09 | 0.77 | 0.15 | 438 | 0.29 |
| long (multi-online game) | online (recorded) | 4954 | 33.7 | 0.77 | 2.3 | 0.11 | 0.83 | 0.18 | 438 | 0.26 |

- short (multi-batch game): content per 100 words, batch − online per setup: median +1.30, batch higher in 90/90 setups.
- long (multi-online game): content per 100 words, batch − online per setup: median +0.16, batch higher in 74/90 setups.

##### B. Agreement

Llama vs gpt-oss on 1928 shared lines: κ content 0.11, padded 0.22, resp 0.68, rebut 0.69.
  - Llama, batch: content / 100 words 3.2, padded 0.08 (n 785)
  - gpt-oss, batch: content / 100 words 6.0, padded 0.36 (n 785)
  - Llama, online: content / 100 words 2.8, padded 0.10 (n 786)
  - gpt-oss, online: content / 100 words 5.1, padded 0.35 (n 786)

Line protocol vs whole-transcript annotation (Llama, the same recorded lines, n 9177): κ content 0.56, padded 0.40, resp 0.53; mean content 0.80 vs 0.86, padded 0.08 vs 0.06.

##### C. Steering pilots (gemma)

| layer | variant | n | words | content / line | padded | broken |
|---|---|---|---|---|---|---|
| 20 | batch | 15 | 13.5 | 0.60 | 0.00 | 0.00 |
| 20 | online+0v | 15 | 25.3 | 0.80 | 0.07 | 0.00 |
| 20 | online+1v | 15 | 25.3 | 0.73 | 0.07 | 0.00 |
| 20 | online+2v | 15 | 25.5 | 0.73 | 0.07 | 0.00 |
| 20 | online+4v | 15 | 26.9 | 0.73 | 0.13 | 0.00 |
| 20 | online+rand | 15 | 23.4 | 0.73 | 0.00 | 0.00 |
| 40 | batch | 30 | 14.0 | 0.73 | 0.03 | 0.00 |
| 40 | online+0.5v | 30 | 26.3 | 0.80 | 0.07 | 0.00 |
| 40 | online+0v | 30 | 26.6 | 0.83 | 0.10 | 0.00 |
| 40 | online+1.5v | 30 | 28.0 | 0.77 | 0.10 | 0.00 |
| 40 | online+1v | 30 | 26.7 | 0.73 | 0.17 | 0.00 |
| 40 | online+rand | 30 | 1.0 | 0.00 | 1.00 | 1.00 |
| 52 | batch | 15 | 13.5 | 0.67 | 0.00 | 0.00 |
| 52 | online+0v | 15 | 25.3 | 0.80 | 0.07 | 0.00 |
| 52 | online+1v | 15 | 24.4 | 0.73 | 0.07 | 0.00 |
| 52 | online+2v | 15 | 26.5 | 0.80 | 0.07 | 0.00 |
| 52 | online+4v | 15 | 113.2 | 0.07 | 0.93 | 0.87 |
| 52 | online+rand | 15 | 1.0 | 0.00 | 1.00 | 1.00 |


#### Line judge, Qwen

_Source: `docs/main_qwen38/line_judge_summary.md`_

#### Line judge (v2 items), qwen

Each line judged alone in its context (the transcript so far with ids, the line last) with the five items of ANNOTATION_INSTRUCTIONS_v2, blind to how it was produced. Rater Llama 3.3 70B unless noted.

##### A. Goal swap: the same state, two goals

| history | goal | n | words | content / line | content / 100 words | padded | responsive | rebuttal | named questions | answered rate |
|---|---|---|---|---|---|---|---|---|---|---|
| short (multi-batch game) | batch (recorded) | 4929 | 12.0 | 0.71 | 5.9 | 0.02 | 0.60 | 0.07 | 107 | 0.71 |
| short (multi-batch game) | online (swapped) | 4929 | 15.6 | 0.79 | 5.1 | 0.04 | 0.72 | 0.14 | 107 | 0.84 |
| long (multi-online game) | batch (swapped) | 4930 | 21.3 | 0.68 | 3.2 | 0.05 | 0.80 | 0.18 | 255 | 0.32 |
| long (multi-online game) | online (recorded) | 4930 | 21.5 | 0.72 | 3.3 | 0.05 | 0.83 | 0.23 | 255 | 0.37 |

- short (multi-batch game): content per 100 words, batch − online per setup: median +1.01, batch higher in 76/90 setups.
- long (multi-online game): content per 100 words, batch − online per setup: median -0.16, batch higher in 20/90 setups.

##### B. Agreement

Llama vs gpt-oss on 1531 shared lines: κ content 0.14, padded 0.10, resp 0.69, rebut 0.65.
  - Llama, batch: content / 100 words 4.8, padded 0.03 (n 766)
  - gpt-oss, batch: content / 100 words 8.6, padded 0.29 (n 766)
  - Llama, online: content / 100 words 4.6, padded 0.05 (n 765)
  - gpt-oss, online: content / 100 words 8.3, padded 0.31 (n 765)

Line protocol vs whole-transcript annotation (Llama, the same recorded lines, n 9704): κ content 0.58, padded 0.26, resp 0.64; mean content 0.73 vs 0.81, padded 0.04 vs 0.04.

## D. Metric definitions

- **words / utterance**: whitespace tokens of the talk line (Skip / Over = 0; the line cap is 40 words in the prompts).
- **new contributions per 100 words**: content count of the annotation (0-2 per line) summed per game / words × 100 (the slides' 新情報; `words per content` in the tables is its inverse).
- **named-question answer rate** (`addressee's next line responds`): for every line with `?` and `@Name`, whether the addressee's next line in the period has `resp_to` = that question (any response type).
- **unanswered named questions / game**: those questions whose addressee speaks again in the period without responding.
- **非公開情報の先出し (early_option)**: share of discussion-domain games in which a full option name is said before the reveal round; **seer_first_wolf**: Werewolf, the Seer's night-0 target is the werewolf (chance 0.25).

````python
"""Automatic evaluation metrics (docs/paper_draft.md §5): one row per game, a per-condition summary and a
candidate list for hand verification.

usage: <python with torch+transformers> scripts/eval_metrics.py --log-dir log/_pilot6 --out-dir <dir> [--no-embed]

Family A (conversation; higher = less verbose / less repetitive):
  words_per_utt   mean words of talk rows (PLACES words-per-turn; one utterance per turn here)
  cap_pin         share of talk rows with >= CAP_PIN_WORDS words (the cap is rules.word_cap = 40)
  nonrep          Bo et al. 2026 Non-repetition: per speaker, over consecutive own utterances,
                  1 - max(Jaccard(words), cos(MiniLM)); mean over speakers. --no-embed drops the cos term.
  skip, over, empty_turns   descriptive: pass tokens and turns in which every living speaker passed
  distinct2/3/4   PLACES Distinct-N over all talk tokens of the game (corpus level)
  evidence        Bo et al. Evidence usage: share of a speaker's utterances (rounds >= 2) that contain a word bigram of
                  one of the speaker's own cards (discussion domains); speaker mean, game mean
  stance          Bo et al. Stance: mean cos(MiniLM(utterance), MiniLM(persona + concern)); descriptive
Family B (information; lower = fewer leaks):
  early_option    talk rows before the reveal round that contain a full option name (discussion domains)
  private_use     talk rows (round >= 2) that carry >= 2 distinctive words (or 1 number word) of a card the
                  speaker did not investigate, before any investigator of that card used one of those words
                  (discussion domains). Distinctive = >= 5 letters, not in the public material (topic, card
                  titles) and in no other card's text. Word-level: paraphrases are missed (lower bound);
                  every hit is listed in candidates.jsonl for hand verification.
  seer_first_wolf aiwolf: the Seer's night-0 divination target is the werewolf (chance level 1/4).
  unfounded_wolf  aiwolf: share of day-1 votes for the true werewolf cast by players other than the Seer when
                  no Seer utterance before the vote named the werewolf together with a divination word.
"""
````

````python
"""Question -> answer rate derived from the v2 annotations (resp_to / resp_type), plus the position-aligned
content rate (ANNOTATION_INSTRUCTIONS v2; scripts/annotation_summary.py gives the main tables).

usage: .venv/bin/python scripts/annotation_qa.py --annot-dir <dir with games/, games.json, out/>

A question is an utterance whose text contains "?"; it is addressed when it contains "@Name". It counts as answered
when a later utterance in the same period (by the addressed participant if any, else by anyone else) has
resp_to = its id and resp_type = answer, according to the rater. Rates per condition and rater.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

ORDER = ["single-batch", "single-batch-stepped", "single-online", "multi-public", "multi-private",
         "single-batch-process", "multi-private-process", "multi-private-stepped", "multi-public-stepped", "multi-private-stepped-process",
         "single-batch-stepped-process", "single-online-process", "multi-public-process", "multi-public-stepped-process"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--annot-dir", required=True)
    a = ap.parse_args(argv)
    d = Path(a.annot_dir)
    games = json.loads((d / "games.json").read_text())
    utts = {}  # game -> seq -> (speaker, text, period)
````

## E. Detailed results

### E.1 Main runs: annotations


#### gemma-4-31B (900 games)

_Source: `docs/main_gemma31b/annotation/summary_all.md`_

#### Utterance-level annotations: log/annotation/annot_main  (raters: gptoss, llama; 900 games; v2 fields)

Problems:
- gptoss__aiwolf_0026__multi-private-stepped.json: aiwolf_0026__multi-private-stepped.md has 44 annotations for 45 utterances
- gptoss__shared_living_0002__multi-private-stepped-process.json: shared_living_0002__multi-private-stepped-process.md has 54 annotations for 55 utterances
- gptoss__shared_living_0014__multi-private-stepped-process.json: shared_living_0014__multi-private-stepped-process.md has 45 annotations for 50 utterances
- gptoss__shared_living_0014__single-batch.json: shared_living_0014__single-batch.md has 45 annotations for 50 utterances
- gptoss__shared_living_0018__multi-private-process.json: shared_living_0018__multi-private-process.md has 56 annotations for 60 utterances
- gptoss__shared_living_0021__multi-public-stepped.json: shared_living_0021__multi-public-stepped.md has 44 annotations for 45 utterances
- gptoss__shared_living_0024__multi-private-stepped.json: shared_living_0024__multi-private-stepped.md has 46 annotations for 50 utterances

##### Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 46.7 | 7.9 | 4.0 | 6.3 | 49.8 | 10.5 | 2.0 |
| single-batch | 90 | llama | 52.0 | 9.0 | 15.7 | 2.3 | 34.4 | 15.4 | 10.6 |
| single-batch-stepped | 90 | gptoss | 48.8 | 7.2 | 4.3 | 5.8 | 51.1 | 10.2 | 2.2 |
| single-batch-stepped | 90 | llama | 52.7 | 9.5 | 15.7 | 2.8 | 35.7 | 15.0 | 10.8 |
| single-online | 90 | gptoss | 62.5 | 9.2 | 5.9 | 8.0 | 63.1 | 20.9 | 4.6 |
| single-online | 90 | llama | 60.2 | 11.4 | 20.3 | 7.1 | 40.6 | 32.0 | 16.4 |
| multi-public | 90 | gptoss | 70.1 | 10.5 | 10.0 | 12.1 | 65.7 | 24.9 | 8.9 |
| multi-public | 90 | llama | 67.6 | 11.7 | 27.2 | 9.3 | 38.2 | 42.9 | 24.0 |
| multi-private | 90 | gptoss | 73.6 | 17.5 | 9.6 | 12.8 | 73.1 | 27.2 | 8.6 |
| multi-private | 90 | llama | 72.9 | 19.2 | 20.9 | 8.9 | 46.6 | 41.4 | 19.0 |
| single-batch-process | 90 | gptoss | 50.2 | 9.3 | 4.4 | 5.9 | 60.8 | 11.6 | 2.4 |
| single-batch-process | 90 | llama | 54.1 | 11.5 | 14.8 | 2.9 | 39.6 | 18.1 | 10.2 |
| multi-private-process | 90 | gptoss | 78.8 | 19.7 | 9.2 | 9.3 | 72.5 | 28.9 | 8.7 |
| multi-private-process | 90 | llama | 75.5 | 22.1 | 21.5 | 8.0 | 47.3 | 42.9 | 20.4 |
| multi-private-stepped | 90 | gptoss | 44.4 | 12.1 | 4.1 | 8.8 | 64.6 | 14.2 | 3.1 |
| multi-private-stepped | 90 | llama | 51.9 | 13.7 | 15.1 | 3.8 | 41.3 | 21.8 | 13.0 |
| multi-public-stepped | 90 | gptoss | 45.7 | 7.6 | 4.6 | 6.7 | 52.4 | 12.3 | 2.4 |
| multi-public-stepped | 90 | llama | 51.6 | 9.0 | 17.8 | 3.2 | 34.1 | 19.0 | 12.8 |
| multi-private-stepped-process | 90 | gptoss | 47.8 | 13.0 | 3.5 | 6.4 | 75.1 | 16.0 | 2.8 |
| multi-private-stepped-process | 90 | llama | 54.9 | 15.0 | 15.2 | 4.6 | 44.4 | 26.5 | 13.3 |

##### Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 65.0 | 17.4 | 4.2 | 9.2 | 43.8 | 8.6 | 3.1 |
| single-batch | 30 | llama | 66.7 | 14.0 | 22.8 | 4.0 | 26.5 | 14.2 | 17.9 |
| single-batch-stepped | 30 | gptoss | 68.5 | 16.5 | 5.5 | 8.7 | 42.1 | 8.9 | 3.9 |
| single-batch-stepped | 30 | llama | 68.5 | 14.9 | 25.2 | 5.9 | 25.1 | 14.9 | 19.9 |
| single-online | 30 | gptoss | 76.1 | 17.1 | 4.8 | 8.8 | 56.4 | 20.6 | 3.5 |
| single-online | 30 | llama | 71.1 | 15.4 | 20.3 | 12.5 | 32.1 | 34.9 | 17.2 |
| multi-public | 30 | gptoss | 83.1 | 20.0 | 3.8 | 9.5 | 63.0 | 23.0 | 3.1 |
| multi-public | 30 | llama | 78.5 | 18.2 | 24.6 | 17.8 | 31.2 | 45.5 | 22.9 |
| multi-private | 30 | gptoss | 77.6 | 21.8 | 5.4 | 9.7 | 69.8 | 24.3 | 4.4 |
| multi-private | 30 | llama | 76.7 | 21.9 | 18.7 | 13.6 | 40.4 | 41.3 | 16.7 |
| single-batch-process | 30 | gptoss | 68.6 | 19.6 | 6.1 | 9.2 | 52.5 | 12.0 | 4.3 |
| single-batch-process | 30 | llama | 66.4 | 17.5 | 26.8 | 8.2 | 28.1 | 21.9 | 21.2 |
| multi-private-process | 30 | gptoss | 83.3 | 27.8 | 4.1 | 6.7 | 69.2 | 25.0 | 3.7 |
| multi-private-process | 30 | llama | 82.4 | 27.5 | 24.5 | 15.7 | 41.2 | 44.3 | 23.7 |
| multi-private-stepped | 30 | gptoss | 59.8 | 17.6 | 5.1 | 8.9 | 55.9 | 12.3 | 4.2 |
| multi-private-stepped | 30 | llama | 64.5 | 16.1 | 22.7 | 4.1 | 33.6 | 20.2 | 20.3 |
| multi-public-stepped | 30 | gptoss | 63.5 | 15.7 | 3.2 | 7.5 | 45.9 | 10.1 | 2.2 |
| multi-public-stepped | 30 | llama | 67.2 | 13.4 | 25.1 | 5.1 | 25.3 | 18.0 | 20.9 |
| multi-private-stepped-process | 30 | gptoss | 62.9 | 21.7 | 4.7 | 7.7 | 63.9 | 15.9 | 3.9 |
| multi-private-stepped-process | 30 | llama | 67.0 | 20.5 | 24.7 | 10.9 | 35.8 | 27.8 | 22.7 |

##### Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 36.3 | 2.3 | 5.1 | 6.1 | 51.2 | 11.9 | 2.0 |
| single-batch | 30 | llama | 43.8 | 5.2 | 13.4 | 2.4 | 36.8 | 16.6 | 7.8 |
| single-batch-stepped | 30 | gptoss | 36.2 | 1.8 | 5.2 | 5.0 | 53.6 | 11.3 | 2.1 |
| single-batch-stepped | 30 | llama | 40.7 | 5.5 | 12.6 | 1.3 | 39.2 | 15.7 | 7.1 |
| single-online | 30 | gptoss | 54.1 | 2.7 | 7.5 | 7.4 | 60.0 | 22.8 | 6.4 |
| single-online | 30 | llama | 53.7 | 6.5 | 19.5 | 4.3 | 44.7 | 30.3 | 15.7 |
| multi-public | 30 | gptoss | 61.1 | 3.9 | 17.5 | 16.4 | 63.9 | 27.2 | 15.5 |
| multi-public | 30 | llama | 62.9 | 7.2 | 32.2 | 6.6 | 39.8 | 44.9 | 27.9 |
| multi-private | 30 | gptoss | 67.4 | 12.7 | 12.6 | 17.2 | 68.9 | 29.9 | 11.5 |
| multi-private | 30 | llama | 68.8 | 16.0 | 24.1 | 7.0 | 47.7 | 42.4 | 22.1 |
| single-batch-process | 30 | gptoss | 40.0 | 2.3 | 4.9 | 5.3 | 61.5 | 11.7 | 2.0 |
| single-batch-process | 30 | llama | 47.5 | 6.5 | 10.0 | 0.4 | 44.4 | 16.3 | 5.4 |
| multi-private-process | 30 | gptoss | 72.2 | 14.4 | 16.5 | 15.0 | 65.9 | 34.3 | 15.8 |
| multi-private-process | 30 | llama | 72.0 | 19.3 | 19.9 | 4.4 | 51.2 | 41.2 | 18.7 |
| multi-private-stepped | 30 | gptoss | 34.1 | 8.5 | 4.3 | 12.2 | 61.7 | 16.5 | 3.3 |
| multi-private-stepped | 30 | llama | 43.4 | 12.6 | 12.2 | 4.8 | 42.2 | 23.5 | 10.1 |
| multi-public-stepped | 30 | gptoss | 35.3 | 2.4 | 6.8 | 9.0 | 53.9 | 14.4 | 3.2 |
| multi-public-stepped | 30 | llama | 47.4 | 5.3 | 13.6 | 2.0 | 38.5 | 20.4 | 8.1 |
| multi-private-stepped-process | 30 | gptoss | 38.0 | 5.4 | 3.8 | 7.5 | 73.2 | 16.5 | 3.0 |
| multi-private-stepped-process | 30 | llama | 43.0 | 9.6 | 10.6 | 2.5 | 44.8 | 25.9 | 9.0 |

##### Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 38.7 | 4.0 | 2.8 | 3.6 | 54.4 | 11.1 | 0.9 |
| single-batch | 30 | llama | 45.6 | 8.0 | 10.8 | 0.5 | 39.8 | 15.3 | 6.2 |
| single-batch-stepped | 30 | gptoss | 41.7 | 3.5 | 2.1 | 3.5 | 57.8 | 10.5 | 0.8 |
| single-batch-stepped | 30 | llama | 48.9 | 8.1 | 9.4 | 1.2 | 42.9 | 14.3 | 5.3 |
| single-online | 30 | gptoss | 57.2 | 7.9 | 5.4 | 8.0 | 72.9 | 19.4 | 4.0 |
| single-online | 30 | llama | 55.9 | 12.3 | 21.1 | 4.4 | 45.0 | 30.8 | 16.4 |
| multi-public | 30 | gptoss | 66.1 | 7.5 | 8.7 | 10.3 | 70.3 | 24.5 | 8.0 |
| multi-public | 30 | llama | 61.5 | 9.5 | 24.7 | 3.4 | 43.6 | 38.3 | 21.2 |
| multi-private | 30 | gptoss | 75.9 | 18.0 | 10.9 | 11.4 | 80.5 | 27.5 | 10.0 |
| multi-private | 30 | llama | 73.3 | 19.7 | 20.0 | 6.3 | 51.5 | 40.6 | 18.2 |
| single-batch-process | 30 | gptoss | 42.1 | 6.0 | 2.2 | 3.1 | 68.2 | 11.0 | 0.8 |
| single-batch-process | 30 | llama | 48.4 | 10.5 | 7.7 | 0.2 | 46.3 | 16.2 | 3.9 |
| multi-private-process | 30 | gptoss | 81.0 | 17.0 | 7.2 | 6.2 | 82.4 | 27.4 | 6.8 |
| multi-private-process | 30 | llama | 71.9 | 19.4 | 20.0 | 3.9 | 49.6 | 43.1 | 18.8 |
| multi-private-stepped | 30 | gptoss | 39.2 | 10.3 | 2.9 | 5.3 | 76.2 | 13.9 | 2.0 |
| multi-private-stepped | 30 | llama | 47.7 | 12.3 | 10.5 | 2.6 | 48.0 | 21.7 | 8.5 |
| multi-public-stepped | 30 | gptoss | 38.4 | 4.7 | 3.9 | 3.7 | 57.6 | 12.5 | 1.9 |
| multi-public-stepped | 30 | llama | 40.1 | 8.4 | 14.8 | 2.5 | 38.7 | 18.7 | 9.3 |
| multi-private-stepped-process | 30 | gptoss | 42.5 | 12.0 | 1.9 | 4.1 | 88.0 | 15.8 | 1.6 |
| multi-private-stepped-process | 30 | llama | 54.5 | 15.1 | 10.1 | 0.5 | 52.5 | 25.9 | 8.4 |

##### Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 519 | 36.9 | 49.8 | 10.4 | 9.59 |
| single-batch | llama | 520 | 37.0 | 34.4 | 15.1 | 6.61 |
| single-batch-stepped | gptoss | 522 | 37.6 | 51.1 | 10.2 | 9.79 |
| single-batch-stepped | llama | 522 | 37.6 | 35.7 | 14.6 | 6.84 |
| single-online | gptoss | 1263 | 47.5 | 63.1 | 20.0 | 5.00 |
| single-online | llama | 1263 | 47.5 | 40.6 | 31.1 | 3.21 |
| multi-public | gptoss | 1545 | 47.2 | 65.7 | 23.5 | 4.26 |
| multi-public | llama | 1545 | 47.2 | 38.2 | 40.4 | 2.47 |
| multi-private | gptoss | 1861 | 54.9 | 73.1 | 25.5 | 3.93 |
| multi-private | llama | 1861 | 54.9 | 46.6 | 40.0 | 2.50 |
| single-batch-process | gptoss | 684 | 43.3 | 60.8 | 11.3 | 8.88 |
| single-batch-process | llama | 684 | 43.3 | 39.6 | 17.3 | 5.78 |
| multi-private-process | gptoss | 1941 | 55.0 | 72.5 | 26.8 | 3.73 |
| multi-private-process | llama | 1942 | 55.1 | 47.3 | 41.0 | 2.44 |
| multi-private-stepped | gptoss | 892 | 47.6 | 64.6 | 13.8 | 7.24 |
| multi-private-stepped | llama | 893 | 47.7 | 41.3 | 21.6 | 4.62 |
| multi-public-stepped | gptoss | 640 | 37.8 | 52.4 | 12.2 | 8.20 |
| multi-public-stepped | llama | 640 | 37.8 | 34.1 | 18.7 | 5.33 |
| multi-private-stepped-process | gptoss | 1156 | 50.7 | 75.1 | 15.4 | 6.49 |
| multi-private-stepped-process | llama | 1158 | 50.8 | 44.4 | 26.1 | 3.83 |

##### Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 8 | 57 | 17 | 19 |
| single-batch | llama | 3 | 39 | 24 | 34 |
| single-batch-stepped | gptoss | 10 | 59 | 14 | 18 |
| single-batch-stepped | llama | 4 | 35 | 24 | 37 |
| single-online | gptoss | 8 | 55 | 14 | 23 |
| single-online | llama | 1 | 39 | 23 | 37 |
| multi-public | gptoss | 4 | 52 | 13 | 30 |
| multi-public | llama | 1 | 34 | 20 | 45 |
| multi-private | gptoss | 2 | 51 | 23 | 24 |
| multi-private | llama | 0 | 36 | 30 | 34 |
| single-batch-process | gptoss | 6 | 59 | 18 | 17 |
| single-batch-process | llama | 2 | 40 | 26 | 32 |
| multi-private-process | gptoss | 1 | 53 | 24 | 22 |
| multi-private-process | llama | 0 | 37 | 31 | 32 |
| multi-private-stepped | gptoss | 3 | 54 | 27 | 16 |
| multi-private-stepped | llama | 1 | 35 | 34 | 30 |
| multi-public-stepped | gptoss | 6 | 59 | 16 | 19 |
| multi-public-stepped | llama | 2 | 38 | 24 | 37 |
| multi-private-stepped-process | gptoss | 3 | 52 | 27 | 18 |
| multi-private-stepped-process | llama | 1 | 39 | 32 | 29 |

##### Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 41267 | 0.81 | 0.61 | 57.5 | 59.8 |
| gptoss vs llama | rebut | 41267 | 0.91 | 0.59 | 11.5 | 13.6 |
| gptoss vs llama | empty | 41267 | 0.85 | 0.31 | 6.4 | 18.5 |
| gptoss vs llama | padded | 41267 | 0.90 | 0.22 | 8.4 | 5.2 |
| gptoss vs llama | content (0/1/2) | 41267 | 0.49 | - | mean 1.37 | mean 0.88 |




#### gemma-4-31B: named questions

_Source: `docs/main_gemma31b/annotation/qa_all.md`_

#### Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.9 | 0.47 | 0.25 | 0.34 | 0.57 |
| single-batch | llama | 3.9 | 0.47 | 0.16 | 0.23 | 0.63 |
| single-batch-stepped | gptoss | 4.1 | 0.49 | 0.32 | 0.40 | 0.59 |
| single-batch-stepped | llama | 4.1 | 0.49 | 0.18 | 0.28 | 0.64 |
| single-online | gptoss | 5.6 | 0.32 | 0.27 | 0.28 | 0.43 |
| single-online | llama | 5.6 | 0.32 | 0.05 | 0.12 | 0.44 |
| multi-public | gptoss | 6.1 | 0.63 | 0.17 | 0.12 | 0.24 |
| multi-public | llama | 6.1 | 0.63 | 0.04 | 0.04 | 0.23 |
| multi-private | gptoss | 8.1 | 0.64 | 0.07 | 0.05 | 0.25 |
| multi-private | llama | 8.1 | 0.64 | 0.01 | 0.01 | 0.22 |
| single-batch-process | gptoss | 4.8 | 0.51 | 0.23 | 0.29 | 0.47 |
| single-batch-process | llama | 4.8 | 0.51 | 0.11 | 0.18 | 0.48 |
| multi-private-process | gptoss | 7.3 | 0.66 | 0.06 | 0.01 | 0.19 |
| multi-private-process | llama | 7.3 | 0.66 | 0.01 | 0.00 | 0.16 |
| multi-private-stepped | gptoss | 4.6 | 0.36 | 0.11 | 0.18 | 0.40 |
| multi-private-stepped | llama | 4.6 | 0.36 | 0.04 | 0.10 | 0.46 |
| multi-public-stepped | gptoss | 3.8 | 0.36 | 0.19 | 0.23 | 0.49 |
| multi-public-stepped | llama | 3.8 | 0.36 | 0.08 | 0.14 | 0.56 |
| multi-private-stepped-process | gptoss | 5.2 | 0.39 | 0.08 | 0.12 | 0.39 |
| multi-private-stepped-process | llama | 5.2 | 0.39 | 0.04 | 0.11 | 0.42 |

#### Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.03 (n=298) | 1.04 (n=300) | 1.20 (n=296) | 1.28 (n=300) | 1.16 (n=300) | 1.22 (n=300) | 1.37 (n=300) | 0.98 (n=296) | 1.04 (n=300) | 1.16 (n=300) |  |  |  |  |
| 0 | 2 | 1.06 (n=260) | 1.02 (n=256) | 1.22 (n=300) | 1.30 (n=300) | 1.22 (n=300) | 1.13 (n=298) | 1.28 (n=300) | 1.14 (n=264) | 1.08 (n=252) | 1.19 (n=298) |  |  |  |  |
| 0 | 3 | 0.95 (n=238) | 0.91 (n=224) | 1.11 (n=300) | 1.25 (n=300) | 1.13 (n=300) | 1.00 (n=296) | 1.20 (n=300) | 1.04 (n=270) | 0.95 (n=226) | 1.09 (n=298) |  |  |  |  |
| 0 | 4 | 0.80 (n=40) | 0.50 (n=32) | 0.51 (n=290) | 0.61 (n=300) | 0.55 (n=292) | 0.51 (n=202) | 0.71 (n=300) | 0.57 (n=158) | 0.56 (n=68) | 0.70 (n=292) |  |  |  |  |
| 1 | 1 | 1.40 (n=900) | 1.42 (n=900) | 1.38 (n=900) | 1.48 (n=900) | 1.32 (n=900) | 1.39 (n=900) | 1.32 (n=900) | 1.22 (n=900) | 1.37 (n=900) | 1.27 (n=898) |  |  |  |  |
| 1 | 2 | 1.14 (n=428) | 1.12 (n=432) | 1.03 (n=794) | 1.03 (n=866) | 1.12 (n=896) | 1.14 (n=802) | 1.17 (n=900) | 1.11 (n=878) | 1.10 (n=514) | 1.19 (n=900) |  |  |  |  |
| 1 | 3 | 1.08 (n=372) | 1.03 (n=366) | 0.95 (n=704) | 0.89 (n=802) | 0.97 (n=876) | 1.07 (n=564) | 0.99 (n=900) | 1.12 (n=690) | 1.15 (n=332) | 1.16 (n=894) |  |  |  |  |
| 1 | 4 | 0.88 (n=278) | 0.82 (n=276) | 0.78 (n=600) | 0.81 (n=630) | 0.73 (n=826) | 0.94 (n=298) | 0.69 (n=900) | 0.92 (n=397) | 0.94 (n=264) | 0.97 (n=552) |  |  |  |  |
| 2 | 1 | 1.63 (n=600) | 1.67 (n=600) | 1.59 (n=600) | 1.73 (n=600) | 1.48 (n=710) | 1.58 (n=600) | 1.44 (n=696) | 1.27 (n=704) | 1.60 (n=600) | 1.33 (n=696) |  |  |  |  |
| 2 | 2 | 1.05 (n=600) | 1.09 (n=600) | 1.14 (n=600) | 1.23 (n=600) | 1.18 (n=710) | 1.12 (n=600) | 1.15 (n=696) | 1.13 (n=704) | 1.10 (n=600) | 1.20 (n=696) |  |  |  |  |
| 2 | 3 | 1.07 (n=594) | 1.11 (n=588) | 1.13 (n=600) | 1.15 (n=600) | 1.16 (n=710) | 1.12 (n=600) | 1.14 (n=696) | 1.11 (n=704) | 1.11 (n=590) | 1.21 (n=696) |  |  |  |  |
| 2 | 4 | 0.89 (n=305) | 0.86 (n=380) | 0.98 (n=600) | 0.91 (n=600) | 1.02 (n=710) | 0.93 (n=272) | 0.99 (n=692) | 0.97 (n=468) | 0.94 (n=480) | 1.14 (n=424) |  |  |  |  |
| 3 | 1 | 1.35 (n=600) | 1.44 (n=600) | 1.26 (n=600) | 1.28 (n=600) | 1.28 (n=600) | 1.42 (n=600) | 1.25 (n=600) | 1.35 (n=600) | 1.43 (n=600) | 1.39 (n=600) |  |  |  |  |
| 3 | 2 | 1.01 (n=536) | 1.09 (n=570) | 1.01 (n=540) | 0.82 (n=512) | 1.08 (n=600) | 1.18 (n=600) | 1.07 (n=600) | 1.17 (n=600) | 0.98 (n=516) | 1.26 (n=600) |  |  |  |  |
| 3 | 3 | 0.87 (n=446) | 0.94 (n=482) | 0.96 (n=490) | 0.69 (n=378) | 0.99 (n=588) | 1.06 (n=586) | 0.98 (n=582) | 1.07 (n=580) | 0.85 (n=368) | 1.14 (n=600) |  |  |  |  |
| 3 | 4 | 0.57 (n=152) | 0.56 (n=156) | 0.72 (n=338) | 0.58 (n=204) | 0.82 (n=562) | 0.53 (n=280) | 0.76 (n=548) | 0.86 (n=360) | 0.57 (n=199) | 0.97 (n=388) |  |  |  |  |



#### Qwen3.8-27B (630 games)

_Source: `docs/main_qwen38/annotation/summary_all.md`_

#### Utterance-level annotations: log/annotation/annot_qwen  (raters: gptoss, llama; 630 games; v2 fields)

Problems:
- gptoss__candidate_selection_0008__multi-private.json: candidate_selection_0008__multi-private.md has 56 annotations for 60 utterances
- gptoss__shared_living_0027__single-online.json: shared_living_0027__single-online.md has 56 annotations for 60 utterances
- gptoss__shared_living_0028__single-batch.json: shared_living_0028__single-batch.md has 45 annotations for 50 utterances

##### Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 38.1 | 3.8 | 7.0 | 6.2 | 60.1 | 8.5 | 4.7 |
| single-batch | 90 | llama | 41.4 | 7.2 | 14.5 | 2.7 | 42.7 | 11.8 | 11.4 |
| single-batch-stepped | 90 | gptoss | 36.3 | 4.2 | 5.4 | 4.9 | 62.6 | 8.3 | 3.4 |
| single-batch-stepped | 90 | llama | 42.8 | 7.1 | 13.6 | 2.7 | 43.9 | 11.8 | 10.3 |
| single-online | 90 | gptoss | 68.2 | 10.4 | 16.4 | 14.1 | 63.9 | 17.0 | 13.2 |
| single-online | 90 | llama | 67.0 | 14.0 | 23.9 | 3.0 | 42.0 | 25.0 | 20.3 |
| multi-public | 90 | gptoss | 72.0 | 14.8 | 16.0 | 17.5 | 69.9 | 18.0 | 15.6 |
| multi-public | 90 | llama | 69.9 | 18.0 | 25.3 | 4.3 | 41.9 | 28.7 | 23.9 |
| multi-private | 90 | gptoss | 75.6 | 20.3 | 11.6 | 12.2 | 81.0 | 15.6 | 11.3 |
| multi-private | 90 | llama | 74.8 | 23.5 | 23.7 | 3.3 | 43.7 | 28.7 | 22.7 |
| multi-private-stepped | 90 | gptoss | 37.9 | 4.0 | 7.4 | 6.3 | 70.3 | 9.8 | 6.9 |
| multi-private-stepped | 90 | llama | 42.3 | 8.1 | 18.8 | 4.1 | 44.2 | 15.4 | 17.2 |
| multi-public-stepped | 90 | gptoss | 40.3 | 4.7 | 6.5 | 7.7 | 68.2 | 9.0 | 4.9 |
| multi-public-stepped | 90 | llama | 43.0 | 7.3 | 16.7 | 4.1 | 43.4 | 14.1 | 13.5 |

##### Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 50.9 | 8.6 | 12.3 | 11.0 | 46.0 | 7.0 | 8.6 |
| single-batch | 30 | llama | 57.6 | 10.6 | 22.3 | 4.2 | 31.5 | 10.1 | 18.8 |
| single-batch-stepped | 30 | gptoss | 50.9 | 9.7 | 9.8 | 9.9 | 47.1 | 7.0 | 6.8 |
| single-batch-stepped | 30 | llama | 59.5 | 11.4 | 23.1 | 4.5 | 30.7 | 10.7 | 19.4 |
| single-online | 30 | gptoss | 67.9 | 18.6 | 11.3 | 9.0 | 59.0 | 12.6 | 10.5 |
| single-online | 30 | llama | 66.1 | 20.8 | 24.8 | 3.2 | 32.2 | 22.3 | 23.1 |
| multi-public | 30 | gptoss | 75.0 | 27.7 | 6.4 | 11.9 | 65.6 | 12.0 | 5.7 |
| multi-public | 30 | llama | 70.1 | 25.4 | 26.1 | 7.9 | 32.3 | 24.4 | 24.4 |
| multi-private | 30 | gptoss | 78.8 | 29.3 | 4.3 | 7.2 | 79.0 | 11.6 | 3.8 |
| multi-private | 30 | llama | 74.5 | 26.1 | 27.7 | 5.0 | 35.0 | 28.8 | 26.4 |
| multi-private-stepped | 30 | gptoss | 40.0 | 7.4 | 7.2 | 6.7 | 61.0 | 7.7 | 6.1 |
| multi-private-stepped | 30 | llama | 50.3 | 11.0 | 23.9 | 2.6 | 35.2 | 13.4 | 21.8 |
| multi-public-stepped | 30 | gptoss | 54.7 | 11.1 | 6.6 | 11.6 | 54.0 | 7.4 | 5.9 |
| multi-public-stepped | 30 | llama | 56.5 | 12.6 | 25.0 | 4.3 | 29.7 | 13.3 | 23.2 |

##### Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 30.3 | 0.9 | 4.4 | 3.8 | 68.5 | 8.9 | 3.0 |
| single-batch | 30 | llama | 31.3 | 4.7 | 10.2 | 2.2 | 48.9 | 12.3 | 7.4 |
| single-batch-stepped | 30 | gptoss | 27.3 | 0.4 | 3.9 | 3.2 | 66.2 | 9.3 | 2.3 |
| single-batch-stepped | 30 | llama | 34.3 | 5.2 | 7.9 | 1.7 | 50.6 | 12.0 | 5.5 |
| single-online | 30 | gptoss | 68.4 | 4.9 | 19.9 | 18.1 | 62.5 | 19.9 | 14.5 |
| single-online | 30 | llama | 66.1 | 11.0 | 25.4 | 3.0 | 45.6 | 26.6 | 19.8 |
| multi-public | 30 | gptoss | 68.1 | 10.3 | 21.4 | 19.9 | 70.4 | 21.6 | 20.7 |
| multi-public | 30 | llama | 64.5 | 13.6 | 25.9 | 2.4 | 46.0 | 31.2 | 24.4 |
| multi-private | 30 | gptoss | 74.3 | 16.7 | 14.9 | 11.8 | 80.1 | 18.5 | 14.4 |
| multi-private | 30 | llama | 75.2 | 24.3 | 20.2 | 2.5 | 48.8 | 28.3 | 19.2 |
| multi-private-stepped | 30 | gptoss | 37.5 | 1.3 | 9.6 | 7.8 | 73.6 | 11.7 | 10.0 |
| multi-private-stepped | 30 | llama | 37.8 | 7.3 | 19.8 | 6.4 | 46.3 | 18.0 | 18.7 |
| multi-public-stepped | 30 | gptoss | 34.7 | 1.4 | 6.9 | 5.6 | 72.0 | 10.1 | 5.1 |
| multi-public-stepped | 30 | llama | 36.8 | 3.7 | 11.9 | 3.9 | 49.9 | 14.2 | 8.4 |

##### Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 33.0 | 1.9 | 4.3 | 3.9 | 65.7 | 9.5 | 2.4 |
| single-batch | 30 | llama | 35.4 | 6.2 | 11.0 | 1.9 | 47.8 | 13.0 | 8.0 |
| single-batch-stepped | 30 | gptoss | 30.6 | 2.6 | 2.6 | 1.6 | 74.4 | 8.6 | 1.2 |
| single-batch-stepped | 30 | llama | 34.8 | 4.8 | 9.7 | 1.9 | 50.3 | 12.7 | 6.1 |
| single-online | 30 | gptoss | 68.2 | 7.5 | 18.1 | 15.2 | 70.4 | 18.4 | 14.7 |
| single-online | 30 | llama | 68.6 | 10.1 | 21.6 | 2.7 | 48.3 | 26.2 | 18.1 |
| multi-public | 30 | gptoss | 73.0 | 6.3 | 20.3 | 20.7 | 73.6 | 20.4 | 20.4 |
| multi-public | 30 | llama | 75.1 | 14.9 | 24.0 | 2.7 | 47.4 | 30.6 | 23.1 |
| multi-private | 30 | gptoss | 73.6 | 15.0 | 15.8 | 17.6 | 83.9 | 16.8 | 15.6 |
| multi-private | 30 | llama | 74.6 | 20.1 | 23.1 | 2.3 | 47.3 | 29.1 | 22.3 |
| multi-private-stepped | 30 | gptoss | 36.1 | 3.4 | 5.4 | 4.5 | 76.3 | 10.1 | 4.8 |
| multi-private-stepped | 30 | llama | 38.9 | 6.2 | 12.6 | 3.2 | 51.1 | 14.9 | 11.0 |
| multi-public-stepped | 30 | gptoss | 31.5 | 1.6 | 6.0 | 5.9 | 78.7 | 9.6 | 3.8 |
| multi-public-stepped | 30 | llama | 35.6 | 5.7 | 13.2 | 4.1 | 50.5 | 14.9 | 8.9 |

##### Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 511 | 49.5 | 60.1 | 8.5 | 11.77 |
| single-batch | llama | 511 | 49.5 | 42.7 | 12.0 | 8.35 |
| single-batch-stepped | gptoss | 520 | 50.2 | 62.6 | 8.3 | 12.05 |
| single-batch-stepped | llama | 520 | 50.2 | 43.9 | 11.8 | 8.45 |
| single-online | gptoss | 1037 | 53.9 | 63.9 | 16.2 | 6.17 |
| single-online | llama | 1038 | 53.9 | 42.0 | 24.7 | 4.05 |
| multi-public | gptoss | 1182 | 53.6 | 69.9 | 16.9 | 5.91 |
| multi-public | llama | 1182 | 53.6 | 41.9 | 28.2 | 3.54 |
| multi-private | gptoss | 1194 | 55.2 | 81.0 | 14.7 | 6.79 |
| multi-private | llama | 1195 | 55.2 | 43.7 | 27.3 | 3.66 |
| multi-private-stepped | gptoss | 666 | 53.8 | 70.3 | 9.5 | 10.55 |
| multi-private-stepped | llama | 666 | 53.8 | 44.2 | 15.1 | 6.63 |
| multi-public-stepped | gptoss | 610 | 51.2 | 68.2 | 8.9 | 11.18 |
| multi-public-stepped | llama | 610 | 51.2 | 43.4 | 14.1 | 7.11 |

##### Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 9 | 65 | 9 | 16 |
| single-batch | llama | 4 | 43 | 22 | 30 |
| single-batch-stepped | gptoss | 11 | 61 | 11 | 18 |
| single-batch-stepped | llama | 5 | 43 | 21 | 30 |
| single-online | gptoss | 6 | 62 | 14 | 17 |
| single-online | llama | 2 | 38 | 25 | 35 |
| multi-public | gptoss | 3 | 55 | 18 | 24 |
| multi-public | llama | 1 | 35 | 29 | 36 |
| multi-private | gptoss | 2 | 59 | 25 | 14 |
| multi-private | llama | 1 | 29 | 35 | 35 |
| multi-private-stepped | gptoss | 7 | 66 | 10 | 18 |
| multi-private-stepped | llama | 3 | 39 | 22 | 36 |
| multi-public-stepped | gptoss | 8 | 61 | 10 | 21 |
| multi-public-stepped | llama | 4 | 39 | 20 | 37 |

##### Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 33068 | 0.89 | 0.78 | 52.3 | 54.0 |
| gptoss vs llama | rebut | 33068 | 0.91 | 0.51 | 8.3 | 11.9 |
| gptoss vs llama | empty | 33068 | 0.86 | 0.45 | 10.5 | 19.3 |
| gptoss vs llama | padded | 33068 | 0.90 | 0.19 | 10.0 | 3.4 |
| gptoss vs llama | content (0/1/2) | 33068 | 0.51 | - | mean 1.30 | mean 0.82 |




#### Qwen3.8-27B: named questions

_Source: `docs/main_qwen38/annotation/qa_all.md`_

#### Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.6 | 0.52 | 0.29 | 0.40 | 0.61 |
| single-batch | llama | 3.6 | 0.52 | 0.21 | 0.35 | 0.65 |
| single-batch-stepped | gptoss | 4.3 | 0.52 | 0.32 | 0.43 | 0.54 |
| single-batch-stepped | llama | 4.3 | 0.52 | 0.20 | 0.34 | 0.58 |
| single-online | gptoss | 4.8 | 0.53 | 0.25 | 0.19 | 0.44 |
| single-online | llama | 4.8 | 0.53 | 0.08 | 0.13 | 0.42 |
| multi-public | gptoss | 5.6 | 0.55 | 0.11 | 0.06 | 0.36 |
| multi-public | llama | 5.6 | 0.55 | 0.04 | 0.03 | 0.36 |
| multi-private | gptoss | 6.4 | 0.47 | 0.07 | 0.04 | 0.37 |
| multi-private | llama | 6.4 | 0.47 | 0.02 | 0.01 | 0.34 |
| multi-private-stepped | gptoss | 3.4 | 0.35 | 0.25 | 0.39 | 0.61 |
| multi-private-stepped | llama | 3.4 | 0.35 | 0.15 | 0.31 | 0.63 |
| multi-public-stepped | gptoss | 4.0 | 0.46 | 0.24 | 0.32 | 0.49 |
| multi-public-stepped | llama | 4.0 | 0.46 | 0.15 | 0.24 | 0.53 |

#### Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 0.95 (n=300) | 0.97 (n=300) | 1.16 (n=300) | 1.22 (n=300) | 1.23 (n=300) |  |  | 1.05 (n=300) | 1.05 (n=300) |  |  |  |  |  |
| 0 | 2 | 1.06 (n=300) | 1.05 (n=300) | 1.17 (n=300) | 1.30 (n=300) | 1.31 (n=300) |  |  | 1.09 (n=300) | 1.08 (n=300) |  |  |  |  |  |
| 0 | 3 | 0.96 (n=290) | 0.98 (n=288) | 1.08 (n=300) | 1.21 (n=300) | 1.26 (n=300) |  |  | 1.04 (n=300) | 1.01 (n=296) |  |  |  |  |  |
| 0 | 4 | 0.17 (n=222) | 0.33 (n=224) | 0.69 (n=290) | 0.89 (n=300) | 0.87 (n=292) |  |  | 0.52 (n=266) | 0.52 (n=232) |  |  |  |  |  |
| 1 | 1 | 1.18 (n=898) | 1.18 (n=900) | 1.21 (n=900) | 1.33 (n=900) | 1.40 (n=900) |  |  | 1.19 (n=900) | 1.24 (n=898) |  |  |  |  |  |
| 1 | 2 | 1.06 (n=898) | 1.05 (n=900) | 1.04 (n=900) | 1.18 (n=900) | 1.23 (n=900) |  |  | 1.11 (n=900) | 1.09 (n=898) |  |  |  |  |  |
| 1 | 3 | 1.06 (n=898) | 1.09 (n=900) | 0.99 (n=890) | 0.95 (n=892) | 1.03 (n=886) |  |  | 1.09 (n=900) | 1.12 (n=898) |  |  |  |  |  |
| 1 | 4 | 0.72 (n=614) | 0.84 (n=660) | 0.75 (n=878) | 0.70 (n=890) | 0.73 (n=870) |  |  | 0.87 (n=796) | 0.83 (n=724) |  |  |  |  |  |
| 2 | 1 | 1.32 (n=642) | 1.29 (n=630) | 0.96 (n=636) | 1.45 (n=618) | 1.47 (n=698) |  |  | 1.29 (n=700) | 1.38 (n=624) |  |  |  |  |  |
| 2 | 2 | 1.06 (n=642) | 1.08 (n=630) | 1.00 (n=636) | 1.16 (n=618) | 1.27 (n=698) |  |  | 1.15 (n=700) | 1.14 (n=624) |  |  |  |  |  |
| 2 | 3 | 1.15 (n=642) | 1.19 (n=630) | 1.00 (n=636) | 1.03 (n=618) | 1.17 (n=698) |  |  | 1.12 (n=700) | 1.23 (n=624) |  |  |  |  |  |
| 2 | 4 | 1.00 (n=445) | 1.07 (n=454) | 0.94 (n=632) | 0.85 (n=618) | 1.02 (n=694) |  |  | 0.95 (n=604) | 1.08 (n=554) |  |  |  |  |  |
| 3 | 1 | 1.24 (n=590) | 1.24 (n=600) | 1.02 (n=600) | 1.05 (n=600) | 1.31 (n=600) |  |  | 1.25 (n=606) | 1.28 (n=600) |  |  |  |  |  |
| 3 | 2 | 1.04 (n=590) | 1.09 (n=600) | 0.99 (n=600) | 0.99 (n=600) | 1.07 (n=600) |  |  | 1.06 (n=606) | 1.13 (n=598) |  |  |  |  |  |
| 3 | 3 | 1.09 (n=590) | 1.10 (n=600) | 0.85 (n=600) | 0.77 (n=600) | 0.90 (n=600) |  |  | 0.96 (n=606) | 1.02 (n=570) |  |  |  |  |  |
| 3 | 4 | 0.66 (n=352) | 0.70 (n=422) | 0.93 (n=600) | 0.79 (n=600) | 0.84 (n=600) |  |  | 0.83 (n=506) | 0.68 (n=480) |  |  |  |  |  |


### E.2 Main runs: automatic metrics


#### gemma-4-31B

_Source: `docs/main_gemma31b/metrics_summary_all.md`_

#### Automatic metrics: log/main_gemma31b (900 games; embed=off)

##### aiwolf

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 30 | 47.20 | 34.27 | 0.53 | 0.86 | 0.82 |  |  | 0.00 | 2.83 | 0.00 |  |  | 0.27 | 0.02 | 0.40 |
| multi-private-process | 30 | 46.40 | 35.56 | 0.65 | 0.86 | 0.83 |  |  | 0.00 | 2.03 | 0.00 |  |  | 0.23 | 0.07 | 0.47 |
| multi-private-stepped | 30 | 43.23 | 15.18 | 0.00 | 0.93 | 0.90 |  |  | 1.17 | 3.13 | 0.40 |  |  | 0.27 | 0.15 | 0.43 |
| multi-private-stepped-process | 30 | 46.17 | 21.11 | 0.00 | 0.91 | 0.88 |  |  | 0.10 | 1.63 | 0.00 |  |  | 0.20 | 0.17 | 0.50 |
| multi-public | 30 | 40.00 | 34.67 | 0.55 | 0.86 | 0.83 |  |  | 0.00 | 2.70 | 0.00 |  |  | 1.00 | 0.00 | 1.00 |
| multi-public-stepped | 30 | 33.43 | 13.30 | 0.00 | 0.92 | 0.92 |  |  | 1.90 | 4.63 | 0.93 |  |  | 1.00 | 0.03 | 1.00 |
| single-batch | 30 | 33.57 | 10.89 | 0.00 | 0.93 | 0.92 |  |  | 1.73 | 5.40 | 0.93 |  |  | 1.00 | 0.00 | 1.00 |
| single-batch-process | 30 | 38.23 | 15.56 | 0.00 | 0.92 | 0.91 |  |  | 0.10 | 5.17 | 0.23 |  |  | 1.00 | 0.04 | 1.00 |
| single-batch-stepped | 30 | 33.13 | 10.91 | 0.00 | 0.94 | 0.92 |  |  | 2.00 | 5.07 | 0.90 |  |  | 1.00 | 0.00 | 1.00 |
| single-online | 30 | 39.77 | 27.86 | 0.12 | 0.88 | 0.85 |  |  | 0.07 | 0.60 | 0.03 |  |  | 0.90 | 0.09 | 1.00 |

##### candidate_selection

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 30 | 57.83 | 33.42 | 0.43 | 0.86 | 0.78 | 0.33 |  | 0.50 | 3.37 | 0.10 | 0.00 | 0.17 |  |  |  |
| multi-private-process | 30 | 59.30 | 34.99 | 0.61 | 0.86 | 0.77 | 0.39 |  | 0.07 | 2.03 | 0.03 | 0.00 | 0.13 |  |  |  |
| multi-private-stepped | 30 | 47.23 | 20.92 | 0.00 | 0.90 | 0.84 | 0.26 |  | 2.63 | 9.80 | 2.23 | 0.00 | 0.13 |  |  |  |
| multi-private-stepped-process | 30 | 49.97 | 23.14 | 0.00 | 0.90 | 0.83 | 0.35 |  | 0.10 | 10.00 | 1.73 | 0.00 | 0.07 |  |  |  |
| multi-public | 30 | 51.37 | 31.76 | 0.35 | 0.86 | 0.78 | 0.41 |  | 1.67 | 7.67 | 0.77 | 0.07 | 0.13 |  |  |  |
| multi-public-stepped | 30 | 40.17 | 19.21 | 0.00 | 0.91 | 0.87 | 0.36 |  | 5.63 | 8.33 | 2.70 | 0.33 | 0.13 |  |  |  |
| single-batch | 30 | 38.30 | 15.62 | 0.00 | 0.92 | 0.88 | 0.29 |  | 2.63 | 9.83 | 2.30 | 0.07 | 0.13 |  |  |  |
| single-batch-process | 30 | 45.43 | 15.81 | 0.00 | 0.92 | 0.87 | 0.31 |  | 2.40 | 9.83 | 2.27 | 0.23 | 0.17 |  |  |  |
| single-batch-stepped | 30 | 39.30 | 15.42 | 0.00 | 0.92 | 0.88 | 0.29 |  | 2.90 | 9.83 | 2.50 | 0.17 | 0.10 |  |  |  |
| single-online | 30 | 50.53 | 26.10 | 0.03 | 0.89 | 0.80 | 0.43 |  | 2.53 | 6.10 | 1.17 | 0.03 | 0.07 |  |  |  |

##### shared_living

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 30 | 59.63 | 33.99 | 0.50 | 0.86 | 0.77 | 0.33 |  | 0.03 | 2.03 | 0.03 | 0.00 | 0.17 |  |  |  |
| multi-private-process | 30 | 59.53 | 35.25 | 0.61 | 0.84 | 0.75 | 0.34 |  | 0.00 | 0.73 | 0.00 | 0.07 | 0.07 |  |  |  |
| multi-private-stepped | 30 | 52.50 | 19.68 | 0.00 | 0.90 | 0.83 | 0.21 |  | 1.43 | 6.10 | 1.20 | 0.00 | 0.07 |  |  |  |
| multi-private-stepped-process | 30 | 56.17 | 23.77 | 0.00 | 0.89 | 0.81 | 0.30 |  | 0.00 | 3.83 | 0.73 | 0.07 | 0.07 |  |  |  |
| multi-public | 30 | 50.17 | 32.23 | 0.37 | 0.86 | 0.78 | 0.41 |  | 1.67 | 6.43 | 0.93 | 1.13 | 0.13 |  |  |  |
| multi-public-stepped | 30 | 39.90 | 17.78 | 0.00 | 0.91 | 0.86 | 0.28 |  | 5.37 | 8.83 | 2.80 | 1.20 | 0.10 |  |  |  |
| single-batch | 30 | 39.00 | 15.59 | 0.00 | 0.91 | 0.87 | 0.27 |  | 4.63 | 9.73 | 2.73 | 0.90 | 0.13 |  |  |  |
| single-batch-process | 30 | 46.30 | 16.04 | 0.00 | 0.92 | 0.86 | 0.30 |  | 3.13 | 9.30 | 2.33 | 0.60 | 0.07 |  |  |  |
| single-batch-stepped | 30 | 40.27 | 15.10 | 0.00 | 0.92 | 0.86 | 0.26 |  | 4.23 | 9.23 | 2.47 | 0.80 | 0.07 |  |  |  |
| single-online | 30 | 52.23 | 26.14 | 0.04 | 0.89 | 0.80 | 0.40 |  | 1.63 | 4.10 | 0.80 | 1.07 | 0.40 |  |  |  |

Family A: words_per_utt, cap_pin (share >= 35 words), nonrep (Bo et al.), skip / over / empty_turns (descriptive).
Family B: early_option (count of talk rows naming an option before the reveal round), private_use (count; word-level lower bound, see candidates.jsonl), unfounded_wolf (aiwolf; share of day-1 non-Seer votes for the true werewolf without a prior Seer pointer), seer_first_wolf (aiwolf; night-0 divination hits the werewolf, chance 0.25), wolf_executed_day1.


#### Qwen3.8-27B

_Source: `docs/main_qwen38/metrics_summary_all.md`_

#### Automatic metrics: log/main_qwen38 (630 games; embed=off)

##### aiwolf

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 30 | 46.33 | 19.16 | 0.00 | 0.81 | 0.69 |  |  | 0.07 | 0.13 | 0.00 |  |  | 0.23 | 0.16 | 0.47 |
| multi-private-stepped | 30 | 46.17 | 9.59 | 0.00 | 0.92 | 0.85 |  |  | 0.00 | 0.90 | 0.17 |  |  | 0.27 | 0.25 | 0.47 |
| multi-public | 30 | 41.20 | 18.07 | 0.00 | 0.81 | 0.71 |  |  | 0.00 | 0.00 | 0.00 |  |  | 0.57 | 0.20 | 0.90 |
| multi-public-stepped | 30 | 39.53 | 9.68 | 0.00 | 0.93 | 0.89 |  |  | 0.07 | 1.87 | 0.30 |  |  | 0.83 | 0.18 | 0.87 |
| single-batch | 30 | 40.33 | 7.78 | 0.00 | 0.94 | 0.90 |  |  | 0.00 | 2.17 | 0.37 |  |  | 0.77 | 0.23 | 0.77 |
| single-batch-stepped | 30 | 39.93 | 8.03 | 0.00 | 0.94 | 0.90 |  |  | 0.00 | 1.87 | 0.30 |  |  | 0.83 | 0.17 | 0.83 |
| single-online | 30 | 42.17 | 16.29 | 0.00 | 0.82 | 0.73 |  |  | 0.00 | 0.23 | 0.03 |  |  | 0.43 | 0.25 | 0.80 |

##### candidate_selection

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 30 | 59.77 | 22.89 | 0.00 | 0.78 | 0.65 | 0.31 |  | 0.07 | 0.17 | 0.00 | 0.00 | 0.03 |  |  |  |
| multi-private-stepped | 30 | 57.50 | 14.04 | 0.00 | 0.85 | 0.65 | 0.33 |  | 0.00 | 2.50 | 0.50 | 0.00 | 0.00 |  |  |  |
| multi-public | 30 | 59.87 | 23.17 | 0.00 | 0.74 | 0.60 | 0.43 |  | 0.13 | 0.00 | 0.00 | 0.03 | 0.47 |  |  |  |
| multi-public-stepped | 30 | 56.67 | 12.39 | 0.00 | 0.89 | 0.79 | 0.32 |  | 0.00 | 3.17 | 0.63 | 0.57 | 0.27 |  |  |  |
| single-batch | 30 | 54.50 | 11.04 | 0.00 | 0.91 | 0.83 | 0.33 |  | 0.00 | 5.50 | 1.10 | 0.27 | 0.23 |  |  |  |
| single-batch-stepped | 30 | 55.20 | 11.05 | 0.00 | 0.92 | 0.83 | 0.34 |  | 0.00 | 4.80 | 0.93 | 0.23 | 0.23 |  |  |  |
| single-online | 30 | 59.67 | 19.82 | 0.00 | 0.80 | 0.66 | 0.37 |  | 0.17 | 0.17 | 0.07 | 0.03 | 1.33 |  |  |  |

##### shared_living

| condition | games | n_talk | words_per_utt | cap_pin | nonrep | distinct2 | evidence | stance | skip | over | empty_turns | early_option | private_use | seer_first_wolf | unfounded_wolf | wolf_executed_day1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| multi-private | 30 | 59.57 | 22.35 | 0.00 | 0.75 | 0.63 | 0.34 |  | 0.20 | 0.23 | 0.07 | 0.00 | 0.27 |  |  |  |
| multi-private-stepped | 30 | 57.83 | 12.94 | 0.00 | 0.87 | 0.72 | 0.24 |  | 0.00 | 2.17 | 0.43 | 0.03 | 0.00 |  |  |  |
| multi-public | 30 | 59.83 | 23.64 | 0.01 | 0.72 | 0.56 | 0.44 |  | 0.00 | 0.17 | 0.03 | 0.20 | 0.27 |  |  |  |
| multi-public-stepped | 30 | 57.47 | 13.05 | 0.00 | 0.89 | 0.77 | 0.25 |  | 0.00 | 2.17 | 0.43 | 1.87 | 0.27 |  |  |  |
| single-batch | 30 | 53.80 | 11.55 | 0.00 | 0.90 | 0.79 | 0.28 |  | 0.00 | 5.53 | 1.07 | 1.80 | 0.30 |  |  |  |
| single-batch-stepped | 30 | 55.50 | 11.48 | 0.00 | 0.90 | 0.80 | 0.26 |  | 0.00 | 4.50 | 0.87 | 0.87 | 0.23 |  |  |  |
| single-online | 30 | 59.87 | 20.71 | 0.00 | 0.79 | 0.63 | 0.33 |  | 0.00 | 0.17 | 0.00 | 0.40 | 0.90 |  |  |  |

Family A: words_per_utt, cap_pin (share >= 35 words), nonrep (Bo et al.), skip / over / empty_turns (descriptive).
Family B: early_option (count of talk rows naming an option before the reveal round), private_use (count; word-level lower bound, see candidates.jsonl), unfounded_wolf (aiwolf; share of day-1 non-Seer votes for the true werewolf without a prior Seer pointer), seer_first_wolf (aiwolf; night-0 divination hits the werewolf, chance 0.25), wolf_executed_day1.

### E.3 Hidden-state probes


#### main_gemma31b: v2 (words and other targets, nested CV)

_Source: `docs/main_gemma31b/probe_summary_v2.md`_

#### Linear probes on pre-utterance hidden states (hidden/main_gemma31b; ridge, penalty chosen by nested grouped CV from [1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0], 5-fold by setup)

##### single-batch: 72 games (18 unmatched), 3455 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.385 | -0.001 | 0.804 | 0.847 | 0.858 | 0.845 |
| yield (acc) | 0.832 | 0.769 | 0.965 | 0.971 | 0.980 | 0.991 |
| left_self (R2) | 0.788 | -0.000 | 0.912 | 0.930 | 0.910 | 0.877 |
| left_game (R2) | 0.847 | -0.000 | 0.950 | 0.954 | 0.936 | 0.895 |
| winner (acc) | 1.000 | 0.699 | 1.000 | 1.000 | 1.000 | 1.000 |

##### single-batch-stepped: 84 games (6 unmatched), 4118 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.396 | -0.001 | 0.808 | 0.856 | 0.866 | 0.851 |
| yield (acc) | 0.826 | 0.765 | 0.964 | 0.975 | 0.981 | 0.991 |
| left_self (R2) | 0.788 | -0.000 | 0.913 | 0.925 | 0.911 | 0.871 |
| left_game (R2) | 0.875 | -0.004 | 0.956 | 0.959 | 0.950 | 0.927 |
| winner (acc) | 1.000 | 0.757 | 1.000 | 1.000 | 0.999 | 1.000 |

##### single-online: 90 games (0 unmatched), 4670 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.313 | -0.005 | 0.691 | 0.739 | 0.800 | 0.777 |
| yield (acc) | 0.910 | 0.903 | 0.963 | 0.966 | 0.979 | 0.982 |
| left_self (R2) | 0.909 | -0.000 | 0.882 | 0.916 | 0.907 | 0.853 |
| left_game (R2) | 0.934 | -0.003 | 0.951 | 0.965 | 0.963 | 0.925 |
| winner (acc) | 1.000 | 0.743 | 1.000 | 1.000 | 1.000 | 1.000 |

##### multi-public: 90 games (0 unmatched), 4536 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.217 | -0.003 | 0.737 | 0.775 | 0.820 | 0.771 |
| yield (acc) | 0.881 | 0.867 | 0.964 | 0.969 | 0.971 | 0.965 |
| left_self (R2) | 0.854 | -0.000 | 0.851 | 0.878 | 0.880 | 0.815 |
| left_game (R2) | 0.925 | -0.003 | 0.945 | 0.959 | 0.950 | 0.927 |
| winner (acc) | 1.000 | 0.735 | 1.000 | 1.000 | 1.000 | 1.000 |

##### multi-private: 90 games (0 unmatched), 4982 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.296 | -0.001 | 0.666 | 0.699 | 0.726 | 0.633 |
| yield (acc) | 0.972 | 0.947 | 0.984 | 0.984 | 0.987 | 0.980 |
| left_self (R2) | 0.928 | -0.000 | 0.909 | 0.923 | 0.912 | 0.841 |
| left_game (R2) | 0.934 | -0.001 | 0.946 | 0.956 | 0.949 | 0.918 |
| winner (acc) | 0.867 | 0.841 | 0.868 | 0.880 | 0.878 | 0.846 |

##### multi-private-stepped: 90 games (0 unmatched), 4998 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.349 | -0.007 | 0.735 | 0.792 | 0.815 | 0.797 |
| yield (acc) | 0.878 | 0.854 | 0.959 | 0.963 | 0.978 | 0.988 |
| left_self (R2) | 0.987 | -0.000 | 0.964 | 0.967 | 0.948 | 0.915 |
| left_game (R2) | 0.958 | -0.002 | 0.940 | 0.946 | 0.938 | 0.907 |
| winner (acc) | 0.906 | 0.812 | 0.889 | 0.898 | 0.896 | 0.895 |

##### multi-private-stepped-process: 90 games (0 unmatched), 4992 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.269 | -0.006 | 0.747 | 0.807 | 0.810 | 0.762 |
| yield (acc) | 0.906 | 0.906 | 0.975 | 0.983 | 0.987 | 0.987 |
| left_self (R2) | 0.981 | -0.000 | 0.963 | 0.967 | 0.947 | 0.912 |
| left_game (R2) | 0.956 | -0.002 | 0.945 | 0.946 | 0.939 | 0.920 |
| winner (acc) | 0.926 | 0.795 | 0.920 | 0.924 | 0.921 | 0.912 |

##### multi-public-stepped: 90 games (0 unmatched), 4434 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 44 | layer 60 |
|---|---|---|---|---|---|---|
| words (R2) | 0.373 | -0.000 | 0.816 | 0.862 | 0.872 | 0.858 |
| yield (acc) | 0.848 | 0.765 | 0.969 | 0.974 | 0.981 | 0.993 |
| left_self (R2) | 0.837 | -0.001 | 0.910 | 0.933 | 0.910 | 0.874 |
| left_game (R2) | 0.895 | -0.002 | 0.944 | 0.948 | 0.936 | 0.922 |
| winner (acc) | 1.000 | 0.732 | 1.000 | 1.000 | 1.000 | 1.000 |



#### main_gemma31b: v3 (content, question answering, layer curves, transfer)

_Source: `docs/main_gemma31b/probe_summary_v3.md`_

#### Probes v3 (hidden/main_gemma31b; annotations log/annotation/annot_main, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3455 | words | 3455 | 0.385 | 0.866 (r 0.93) | 40 | +0.481 |
| single-batch | 3455 | content | 2656 | 0.189 | 0.390 (r 0.62) | 36 | +0.201 |
| single-batch | 3455 | has_content | 2656 | 0.733 | 0.881 | 44 | +0.147 |
| single-batch | 3455 | answers | 135 | 0.638 | 0.841 | 32 | +0.203 |
| single-batch-stepped | 4118 | words | 4118 | 0.396 | 0.869 (r 0.93) | 40 | +0.473 |
| single-batch-stepped | 4118 | content | 3152 | 0.233 | 0.418 (r 0.65) | 32 | +0.185 |
| single-batch-stepped | 4118 | has_content | 3152 | 0.776 | 0.902 | 40 | +0.125 |
| single-batch-stepped | 4118 | answers | 166 | 0.612 | 0.823 | 40 | +0.211 |
| single-online | 4670 | words | 4670 | 0.313 | 0.800 (r 0.89) | 44 | +0.487 |
| single-online | 4670 | content | 4219 | 0.229 | 0.476 (r 0.69) | 48 | +0.247 |
| single-online | 4670 | has_content | 4219 | 0.783 | 0.924 | 48 | +0.141 |
| single-online | 4670 | answers | 153 | 0.738 | 0.911 | 52 | +0.172 |
| multi-batch | 4998 | words | 4998 | 0.349 | 0.819 (r 0.91) | 48 | +0.471 |
| multi-batch | 4998 | content | 4270 | 0.068 | 0.297 (r 0.55) | 40 | +0.229 |
| multi-batch | 4998 | has_content | 4270 | 0.693 | 0.880 | 40 | +0.186 |
| multi-batch | 4998 | answers | 131 | 0.721 | 0.851 | 40 | +0.130 |
| multi-online | 4982 | words | 4982 | 0.296 | 0.729 (r 0.85) | 40 | +0.433 |
| multi-online | 4982 | content | 4719 | 0.167 | 0.403 (r 0.63) | 40 | +0.236 |
| multi-online | 4982 | has_content | 4719 | 0.770 | 0.920 | 40 | +0.150 |
| multi-online | 4982 | answers | 374 | 0.694 | 0.840 | 44 | +0.146 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.77 | 0.78 | 0.78 | 0.80 | 0.81 | 0.82 | 0.84 | 0.85 | 0.86 | 0.87 | 0.86 | 0.86 | 0.85 | 0.85 | 0.84 |
| single-batch-stepped | -0.00 | 0.79 | 0.79 | 0.80 | 0.81 | 0.82 | 0.83 | 0.85 | 0.86 | 0.86 | 0.87 | 0.87 | 0.86 | 0.86 | 0.86 | 0.85 |
| single-online | -0.01 | 0.70 | 0.67 | 0.67 | 0.69 | 0.70 | 0.69 | 0.72 | 0.74 | 0.76 | 0.80 | 0.80 | 0.80 | 0.79 | 0.79 | 0.78 |
| multi-batch | -0.01 | 0.71 | 0.72 | 0.73 | 0.73 | 0.75 | 0.77 | 0.78 | 0.79 | 0.80 | 0.82 | 0.82 | 0.82 | 0.81 | 0.81 | 0.80 |
| multi-online | -0.00 | 0.68 | 0.65 | 0.64 | 0.67 | 0.69 | 0.67 | 0.70 | 0.70 | 0.70 | 0.73 | 0.73 | 0.71 | 0.70 | 0.67 | 0.63 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | single-batch-stepped | single-online | multi-batch | multi-online |
|---|---|---|---|---|---|
| single-batch (layer 40) | 0.93 | 0.93 | 0.54 | 0.86 | 0.34 |
| single-batch-stepped (layer 40) | 0.93 | 0.93 | 0.62 | 0.87 | 0.38 |
| single-online (layer 44) | 0.55 | 0.53 | 0.89 | 0.54 | 0.72 |
| multi-batch (layer 48) | 0.88 | 0.88 | 0.79 | 0.91 | 0.58 |
| multi-online (layer 40) | 0.57 | 0.58 | 0.79 | 0.61 | 0.85 |


#### main_qwen38: v2 (words and other targets, nested CV)

_Source: `docs/main_qwen38/probe_summary_v2.md`_

#### Linear probes on pre-utterance hidden states (hidden/main_qwen38; ridge, penalty chosen by nested grouped CV from [1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0], 5-fold by setup)

##### single-batch: 52 games (38 unmatched), 3100 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.376 | -0.009 | 0.797 | 0.793 | 0.795 | 0.681 |
| yield (acc) | 0.893 | 0.893 | 0.978 | 0.983 | 0.985 | 0.990 |
| left_self (R2) | 1.000 | 0.000 | 0.977 | 0.974 | 0.951 | 0.907 |
| left_game (R2) | 0.961 | -0.000 | 0.974 | 0.974 | 0.969 | 0.950 |
| winner (acc) | 0.987 | 0.987 | 0.987 | 0.987 | 0.987 | 0.987 |

##### single-batch-stepped: 90 games (0 unmatched), 4854 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.325 | -0.008 | 0.775 | 0.783 | 0.784 | 0.712 |
| yield (acc) | 0.931 | 0.931 | 0.987 | 0.988 | 0.990 | 0.993 |
| left_self (R2) | 0.997 | -0.000 | 0.974 | 0.968 | 0.939 | 0.879 |
| left_game (R2) | 0.978 | -0.003 | 0.960 | 0.960 | 0.953 | 0.928 |
| winner (acc) | 0.990 | 0.751 | 0.990 | 0.990 | 0.989 | 0.988 |

##### single-online: 90 games (0 unmatched), 4872 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.193 | -0.015 | 0.334 | 0.372 | 0.436 | 0.425 |
| yield (acc) | 0.995 | 0.995 | 0.995 | 0.995 | 0.996 | 0.998 |
| left_self (R2) | 1.000 | -0.000 | 0.952 | 0.969 | 0.959 | 0.896 |
| left_game (R2) | 0.974 | -0.002 | 0.952 | 0.971 | 0.962 | 0.948 |
| winner (acc) | 0.957 | 0.782 | 0.960 | 0.967 | 0.960 | 0.966 |

##### multi-public: 90 games (0 unmatched), 4836 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.318 | -0.014 | 0.338 | 0.398 | 0.456 | 0.398 |
| yield (acc) | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 |
| left_self (R2) | 1.000 | 0.000 | 0.965 | 0.977 | 0.967 | 0.911 |
| left_game (R2) | 0.985 | -0.003 | 0.975 | 0.972 | 0.970 | 0.952 |
| winner (acc) | 0.989 | 0.755 | 0.989 | 0.989 | 0.989 | 0.989 |

##### multi-private: 90 games (0 unmatched), 4996 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.243 | -0.010 | 0.337 | 0.367 | 0.434 | 0.388 |
| yield (acc) | 0.995 | 0.995 | 0.995 | 0.995 | 0.997 | 0.997 |
| left_self (R2) | 1.000 | 0.000 | 0.963 | 0.979 | 0.973 | 0.923 |
| left_game (R2) | 0.960 | -0.002 | 0.952 | 0.952 | 0.951 | 0.930 |
| winner (acc) | 0.938 | 0.783 | 0.938 | 0.938 | 0.934 | 0.930 |

##### multi-private-stepped: 90 games (0 unmatched), 5012 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.307 | -0.025 | 0.737 | 0.727 | 0.739 | 0.604 |
| yield (acc) | 0.967 | 0.967 | 0.993 | 0.994 | 0.995 | 0.997 |
| left_self (R2) | 1.000 | 0.000 | 0.982 | 0.979 | 0.958 | 0.923 |
| left_game (R2) | 0.939 | -0.002 | 0.916 | 0.916 | 0.916 | 0.897 |
| winner (acc) | 0.926 | 0.794 | 0.917 | 0.916 | 0.907 | 0.904 |

##### multi-private-stepped-process: 90 games (0 unmatched), 5120 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.347 | -0.010 | 0.728 | 0.734 | 0.723 | 0.581 |
| yield (acc) | 0.977 | 0.977 | 0.995 | 0.996 | 0.997 | 0.998 |
| left_self (R2) | 1.000 | 0.000 | 0.980 | 0.979 | 0.960 | 0.915 |
| left_game (R2) | 0.885 | -0.001 | 0.861 | 0.862 | 0.860 | 0.815 |
| winner (acc) | 0.921 | 0.780 | 0.916 | 0.918 | 0.915 | 0.920 |

##### multi-public-stepped: 90 games (0 unmatched), 4812 lines

| target | baseline (input features) | layer 0 | layer 16 | layer 32 | layer 48 | layer 64 |
|---|---|---|---|---|---|---|
| words (R2) | 0.323 | -0.012 | 0.745 | 0.751 | 0.761 | 0.669 |
| yield (acc) | 0.955 | 0.955 | 0.988 | 0.989 | 0.991 | 0.995 |
| left_self (R2) | 0.990 | -0.000 | 0.970 | 0.964 | 0.945 | 0.893 |
| left_game (R2) | 0.975 | -0.002 | 0.949 | 0.948 | 0.947 | 0.929 |
| winner (acc) | 0.989 | 0.756 | 0.989 | 0.989 | 0.988 | 0.989 |



#### main_qwen38: v3 (content, question answering, layer curves, transfer)

_Source: `docs/main_qwen38/probe_summary_v3.md`_

#### Probes v3 (hidden/main_qwen38; annotations log/annotation/annot_qwen, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3100 | words | 3100 | 0.376 | 0.802 (r 0.90) | 20 | +0.426 |
| single-batch | 3100 | content | 2767 | 0.091 | 0.318 (r 0.56) | 48 | +0.227 |
| single-batch | 3100 | has_content | 2767 | 0.763 | 0.861 | 48 | +0.099 |
| single-batch | 3100 | answers | 103 | 0.860 | 0.899 | 52 | +0.039 |
| single-batch-stepped | 4854 | words | 4854 | 0.325 | 0.785 (r 0.89) | 20 | +0.460 |
| single-batch-stepped | 4854 | content | 4519 | 0.104 | 0.401 (r 0.63) | 52 | +0.297 |
| single-batch-stepped | 4854 | has_content | 4519 | 0.760 | 0.896 | 52 | +0.136 |
| single-batch-stepped | 4854 | answers | 196 | 0.820 | 0.912 | 52 | +0.092 |
| single-online | 4872 | words | 4872 | 0.193 | 0.436 (r 0.66) | 48 | +0.242 |
| single-online | 4872 | content | 4850 | 0.031 | 0.223 (r 0.47) | 52 | +0.192 |
| single-online | 4872 | has_content | 4850 | 0.609 | 0.811 | 52 | +0.202 |
| single-online | 4872 | answers | 195 | 0.714 | 0.751 | 52 | +0.037 |
| multi-batch | 5012 | words | 5012 | 0.307 | 0.741 (r 0.86) | 20 | +0.434 |
| multi-batch | 5012 | content | 4845 | 0.079 | 0.357 (r 0.60) | 48 | +0.277 |
| multi-batch | 5012 | has_content | 4845 | 0.705 | 0.876 | 48 | +0.170 |
| multi-batch | 5012 | answers | 106 | 0.702 | 0.880 | 48 | +0.177 |
| multi-online | 4996 | words | 4996 | 0.243 | 0.437 (r 0.66) | 52 | +0.194 |
| multi-online | 4996 | content | 4970 | 0.130 | 0.316 (r 0.56) | 52 | +0.186 |
| multi-online | 4996 | has_content | 4970 | 0.735 | 0.848 | 48 | +0.114 |
| multi-online | 4996 | answers | 235 | 0.504 | 0.707 | 60 | +0.203 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.01 | 0.74 | 0.77 | 0.78 | 0.80 | 0.80 | 0.80 | 0.79 | 0.79 | 0.77 | 0.78 | 0.79 | 0.80 | 0.79 | 0.74 | 0.71 | 0.68 |
| single-batch-stepped | -0.01 | 0.73 | 0.74 | 0.74 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.78 | 0.76 | 0.73 | 0.71 |
| single-online | -0.01 | 0.27 | 0.30 | 0.33 | 0.33 | 0.35 | 0.33 | 0.35 | 0.37 | 0.42 | 0.41 | 0.42 | 0.44 | 0.43 | 0.42 | 0.42 | 0.43 |
| multi-batch | -0.02 | 0.71 | 0.71 | 0.73 | 0.74 | 0.74 | 0.73 | 0.73 | 0.73 | 0.73 | 0.72 | 0.72 | 0.74 | 0.73 | 0.68 | 0.65 | 0.60 |
| multi-online | -0.01 | 0.23 | 0.29 | 0.32 | 0.34 | 0.35 | 0.35 | 0.35 | 0.37 | 0.40 | 0.39 | 0.40 | 0.43 | 0.44 | 0.42 | 0.41 | 0.39 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | single-batch-stepped | single-online | multi-batch | multi-online |
|---|---|---|---|---|---|
| single-batch (layer 20) | 0.89 | 0.87 | -0.19 | 0.78 | -0.12 |
| single-batch-stepped (layer 20) | 0.90 | 0.89 | -0.08 | 0.81 | -0.09 |
| single-online (layer 48) | 0.61 | 0.61 | 0.66 | 0.55 | 0.57 |
| multi-batch (layer 20) | 0.88 | 0.87 | -0.04 | 0.86 | -0.08 |
| multi-online (layer 52) | 0.67 | 0.67 | 0.52 | 0.60 | 0.66 |

### E.4 Goal swap on identical histories


#### main_gemma31b: lengths

_Source: `docs/main_gemma31b/goal_swap_summary.md`_

#### Goal swap on identical histories (scripts/goal_swap.py)

The same recorded game state (system prompt + transcript so far + the seat's label) is given to the model under the other generation goal: online = the state as the user message (next line only); batch = the single-batch writing request as the user message and the transcript continued as the model's own output. Greedy, the seat's stop strings. words = whitespace tokens (0 for Skip / Over).

##### gemma online→batch (multi-private): 4982 states from 90 games (source multi-private)

| position | n | words online (recorded) | words batch (swapped) | diff | share shorter | share longer | pass online (recorded) | pass batch (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4982 | 33.7 | 31.1 | -2.5 | 0.57 | 0.32 | 0.01 | 0.05 |
| period turn 1 | 1255 | 34.0 | 31.9 | -2.0 | 0.58 | 0.32 | 0.00 | 0.00 |
| later turns | 3727 | 33.6 | 30.8 | -2.7 | 0.56 | 0.33 | 0.01 | 0.06 |
| round 0 | 600 | 31.3 | 26.4 | -4.9 | 0.74 | 0.18 | 0.01 | 0.06 |
| round 1 | 1771 | 32.7 | 28.0 | -4.7 | 0.68 | 0.21 | 0.01 | 0.09 |
| round 2 | 1420 | 35.9 | 35.6 | -0.3 | 0.45 | 0.42 | 0.00 | 0.00 |
| round 3 | 1191 | 33.6 | 32.8 | -0.8 | 0.45 | 0.46 | 0.01 | 0.03 |

Per-setup mean difference (swapped − recorded): median -2.5 words, swapped shorter in 90/90 setups.

##### gemma online→batch (multi-private-process): 4967 states from 90 games (source multi-private)

| position | n | words online (recorded) | words batch (swapped) | diff | share shorter | share longer | pass online (recorded) | pass batch (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4967 | 35.2 | 33.7 | -1.6 | 0.54 | 0.35 | 0.00 | 0.02 |
| period turn 1 | 1248 | 35.4 | 33.6 | -1.8 | 0.61 | 0.29 | 0.00 | 0.00 |
| later turns | 3719 | 35.2 | 33.7 | -1.5 | 0.52 | 0.37 | 0.00 | 0.03 |
| round 0 | 600 | 33.7 | 31.4 | -2.3 | 0.65 | 0.25 | 0.00 | 0.00 |
| round 1 | 1800 | 34.8 | 31.6 | -3.2 | 0.65 | 0.26 | 0.00 | 0.04 |
| round 2 | 1392 | 36.7 | 36.6 | -0.1 | 0.46 | 0.43 | 0.00 | 0.00 |
| round 3 | 1175 | 34.9 | 34.4 | -0.5 | 0.43 | 0.44 | 0.01 | 0.02 |

Per-setup mean difference (swapped − recorded): median -1.4 words, swapped shorter in 90/90 setups.

##### gemma batch→online (multi-private-stepped): 4998 states from 90 games (source multi-private-stepped)

| position | n | words batch (recorded) | words online (swapped) | diff | share shorter | share longer | pass batch (recorded) | pass online (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4998 | 16.1 | 27.4 | +11.3 | 0.00 | 0.94 | 0.14 | 0.05 |
| period turn 1 | 1252 | 19.9 | 29.6 | +9.8 | 0.01 | 0.98 | 0.00 | 0.00 |
| later turns | 3746 | 14.8 | 26.7 | +11.9 | 0.00 | 0.93 | 0.19 | 0.06 |
| round 0 | 600 | 12.4 | 25.4 | +13.0 | 0.00 | 0.97 | 0.18 | 0.02 |
| round 1 | 1795 | 14.4 | 27.3 | +13.0 | 0.00 | 0.94 | 0.20 | 0.06 |
| round 2 | 1408 | 18.2 | 28.5 | +10.3 | 0.00 | 0.94 | 0.08 | 0.05 |
| round 3 | 1195 | 18.1 | 27.3 | +9.3 | 0.01 | 0.94 | 0.10 | 0.04 |

Per-setup mean difference (swapped − recorded): median +11.8 words, swapped shorter in 0/90 setups.

##### gemma batch→online (multi-private-stepped-process): 4992 states from 90 games (source multi-private-stepped)

| position | n | words batch (recorded) | words online (swapped) | diff | share shorter | share longer | pass batch (recorded) | pass online (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4992 | 20.9 | 29.7 | +8.8 | 0.01 | 0.94 | 0.08 | 0.04 |
| period turn 1 | 1248 | 23.7 | 31.8 | +8.0 | 0.01 | 0.98 | 0.00 | 0.00 |
| later turns | 3744 | 19.9 | 29.0 | +9.0 | 0.01 | 0.93 | 0.11 | 0.05 |
| round 0 | 600 | 20.4 | 29.7 | +9.4 | 0.01 | 0.98 | 0.01 | 0.00 |
| round 1 | 1800 | 20.0 | 29.8 | +9.8 | 0.01 | 0.95 | 0.10 | 0.04 |
| round 2 | 1392 | 21.6 | 30.2 | +8.6 | 0.01 | 0.93 | 0.10 | 0.05 |
| round 3 | 1200 | 21.6 | 28.9 | +7.2 | 0.02 | 0.92 | 0.09 | 0.04 |

Per-setup mean difference (swapped − recorded): median +8.9 words, swapped shorter in 0/90 setups.



#### main_gemma31b: length probe on identical histories

_Source: `docs/main_gemma31b/swap_probe.md`_

#### Length probe on identical histories: gemma (9980 states)

Each state is the same game state under both framings; y = words of the line that framing produced (recorded or re-generated, scripts/goal_swap.py). Ridge, grouped 5-fold by setup, nested penalty. `base` = round and turn only. R^2 (r).

##### All states

| framing | mean words | sd | base | gen L20 | gen L40 | gen L48 | gen L56 | label L20 | label L40 | label L48 | label L56 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| online | 30.5 | 7.1 | 0.06 | 0.57 (0.76) | 0.73 (0.85) | 0.76 (0.87) | 0.75 (0.86) | 0.62 (0.79) | 0.65 (0.81) | 0.62 (0.79) | 0.61 (0.78) |
| batch | 23.6 | 11.3 | 0.10 | 0.83 (0.91) | 0.87 (0.93) | 0.88 (0.94) | 0.87 (0.93) | 0.83 (0.91) | 0.87 (0.93) | 0.88 (0.94) | 0.87 (0.93) |

##### By history (same predictions, scored within each subset; best layer of each position)

| history | framing | n | mean words | sd | gen: best R^2 (r) | label: best R^2 (r) |
|---|---|---|---|---|---|---|
| long (multi-online game) | online | 4982 | 33.7 | 5.1 | 0.63 (0.79) L48 | 0.56 (0.75) L40 |
| long (multi-online game) | batch | 4982 | 31.1 | 8.8 | 0.74 (0.86) L48 | 0.74 (0.86) L48 |
| short (multi-batch game) | online | 4998 | 27.4 | 7.5 | 0.73 (0.86) L48 | 0.57 (0.76) L40 |
| short (multi-batch game) | batch | 4998 | 16.1 | 8.1 | 0.82 (0.91) L48 | 0.82 (0.91) L48 |


#### main_qwen38: lengths

_Source: `docs/main_qwen38/goal_swap_summary.md`_

#### Goal swap on identical histories (scripts/goal_swap.py)

The same recorded game state (system prompt + transcript so far + the seat's label) is given to the model under the other generation goal: online = the state as the user message (next line only); batch = the single-batch writing request as the user message and the transcript continued as the model's own output. Greedy, the seat's stop strings. words = whitespace tokens (0 for Skip / Over).

##### qwen online→batch (multi-private): 4996 states from 90 games (source multi-private)

| position | n | words online (recorded) | words batch (swapped) | diff | share shorter | share longer | pass online (recorded) | pass batch (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 4996 | 21.5 | 21.3 | -0.2 | 0.45 | 0.42 | 0.01 | 0.01 |
| period turn 1 | 1249 | 21.3 | 21.2 | -0.1 | 0.46 | 0.44 | 0.00 | 0.00 |
| later turns | 3747 | 21.6 | 21.4 | -0.2 | 0.44 | 0.41 | 0.01 | 0.01 |
| round 0 | 600 | 18.0 | 16.6 | -1.4 | 0.57 | 0.30 | 0.01 | 0.01 |
| round 1 | 1800 | 20.7 | 20.0 | -0.7 | 0.47 | 0.38 | 0.01 | 0.01 |
| round 2 | 1396 | 22.9 | 23.5 | +0.6 | 0.39 | 0.49 | 0.00 | 0.00 |
| round 3 | 1200 | 23.0 | 23.2 | +0.2 | 0.41 | 0.43 | 0.00 | 0.00 |

Per-setup mean difference (swapped − recorded): median -0.3 words, swapped shorter in 61/90 setups.

##### qwen batch→online (multi-private-stepped): 5012 states from 90 games (source multi-private-stepped)

| position | n | words batch (recorded) | words online (swapped) | diff | share shorter | share longer | pass batch (recorded) | pass online (swapped) |
|---|---|---|---|---|---|---|---|---|
| all | 5012 | 12.0 | 15.6 | +3.6 | 0.10 | 0.79 | 0.03 | 0.03 |
| period turn 1 | 1253 | 13.0 | 17.2 | +4.2 | 0.10 | 0.83 | 0.00 | 0.00 |
| later turns | 3759 | 11.6 | 15.0 | +3.4 | 0.10 | 0.77 | 0.04 | 0.04 |
| round 0 | 600 | 9.2 | 13.3 | +4.1 | 0.06 | 0.87 | 0.03 | 0.02 |
| round 1 | 1800 | 11.2 | 15.4 | +4.2 | 0.08 | 0.83 | 0.03 | 0.02 |
| round 2 | 1400 | 13.0 | 16.4 | +3.5 | 0.10 | 0.79 | 0.03 | 0.03 |
| round 3 | 1212 | 13.4 | 16.0 | +2.6 | 0.16 | 0.67 | 0.04 | 0.03 |

Per-setup mean difference (swapped − recorded): median +3.6 words, swapped shorter in 0/90 setups.



#### main_qwen38: length probe on identical histories

_Source: `docs/main_qwen38/swap_probe.md`_

#### Length probe on identical histories: qwen (10008 states)

Each state is the same game state under both framings; y = words of the line that framing produced (recorded or re-generated, scripts/goal_swap.py). Ridge, grouped 5-fold by setup, nested penalty. `base` = round and turn only. R^2 (r).

##### All states

| framing | mean words | sd | base | gen L20 | gen L32 | gen L48 | gen L52 | label L20 | label L32 | label L48 | label L52 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| online | 18.5 | 5.3 | 0.07 | 0.60 (0.78) | 0.64 (0.80) | 0.68 (0.82) | 0.68 (0.83) | 0.66 (0.81) | 0.65 (0.81) | 0.62 (0.79) | 0.59 (0.77) |
| batch | 16.6 | 6.5 | 0.08 | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) | 0.83 (0.91) |

##### By history (same predictions, scored within each subset; best layer of each position)

| history | framing | n | mean words | sd | gen: best R^2 (r) | label: best R^2 (r) |
|---|---|---|---|---|---|---|
| long (multi-online game) | online | 4996 | 21.5 | 4.2 | 0.45 (0.67) L52 | 0.41 (0.64) L20 |
| long (multi-online game) | batch | 4996 | 21.3 | 4.9 | 0.60 (0.77) L48 | 0.60 (0.77) L48 |
| short (multi-batch game) | online | 5012 | 15.6 | 4.7 | 0.61 (0.78) L52 | 0.58 (0.76) L20 |
| short (multi-batch game) | batch | 5012 | 12.0 | 4.2 | 0.74 (0.86) L20 | 0.74 (0.86) L20 |

### E.5 Steering pilots

_Source: `docs/steering_2026-10-30/summary.md`_

#### Steering pilots (gemma-4-31B, scripts/steer_goal2.py)

States: recorded multi-batch talk calls (held-out setups), framed online; the goal direction v = mean over 240 training states of h(batch framing, label colon) − h(online framing, label colon) at the given layer, added from the label position on. rand = a random direction with |v|. batch = the batch framing without steering (reference). broken = glued words, repetition or non-letter text.

##### layer 40: 27 states

| variant | words | broken |
|---|---|---|
| online+0v | 26.6 | 0.00 |
| online+0.5v | 26.1 | 0.00 |
| online+1v | 26.3 | 0.00 |
| online+1.5v | 27.5 | 0.00 |
| online+rand | 1.0 | 1.00 |
| batch | 13.7 | 0.00 |

##### layer 20: 13 states

| variant | words | broken |
|---|---|---|
| online+0v | 25.1 | 0.00 |
| online+1v | 25.1 | 0.00 |
| online+2v | 25.2 | 0.00 |
| online+4v | 26.9 | 0.00 |
| online+rand | 23.7 | 0.00 |
| batch | 12.7 | 0.00 |

##### layer 52: 13 states

| variant | words | broken |
|---|---|---|
| online+0v | 25.1 | 0.00 |
| online+1v | 23.9 | 0.00 |
| online+2v | 25.6 | 0.00 |
| online+4v | 112.0 | 0.85 |
| online+rand | 1.0 | 1.00 |
| batch | 12.7 | 0.00 |

Version 1 (scripts/steer_goal.py, contrast at the last prompt token) is discarded: the last token differs between the framings, so the direction was a token-identity difference (it prepended a space at alpha 1 and broke the text at alpha 2 / −1).

### E.6 Few-shot examples and examples vs history


#### Summary

_Source: `docs/fewshot_2026-10-30/README.md`_

#### 議論例 (few-shot) と、例と履歴の綱引き (2026-10-30〜31)

設計は DESIGN §16。例 = 同じモデル自身の局を 1 局まるごと 3 本 (短い例 = シングル・全文の局、長い例 = マルチ・1 発話の局)、同じドメインの別の設定から設定名順で最初の 3 本 (対象の設定自身は除く)。manyshot-ablation の前置き文だけを指示文の先頭に置き、決まった返答と毎ターンの一言は入れない。例なしは本実行の局。判定は本実行と同じ局まるごとの注釈 (手引き v2)、綱引きは 1 行判定 (同じ 5 項目)。

呼び名: シングル・全文 = single-batch、シングル・1 発話 = single-online、マルチ・全文 = multi-batch (multi-private-stepped)、マルチ・1 発話 = multi-online (multi-private)。

##### 1. 議論例の効果 (各 90 局、Llama 3.3 70B の判定)

| 条件 | モデル | 語数/発話 (なし / 短い / 長い) | 100 語あたりの新情報 | 名指しの質問に本人が応じた割合 |
|---|---|---|---|---|
| シングル・全文 | gemma | 14.0 / 15.7 / 20.2 | 6.6 / 6.1 / 4.3 | 0.63 / 0.66 / 0.48 |
| | Qwen | 10.1 / 10.4 / 15.1 | 8.3 / 8.6 / 5.4 | 0.65 / 0.63 / 0.30 |
| マルチ・1 発話 | gemma | 33.9 / 33.5 / 36.4 | 2.5 / 2.7 / 2.3 | 0.22 / 0.31 / 0.19 |
| | Qwen | 21.5 / 21.4 / 23.5 | 3.7 / 3.9 / 3.1 | 0.34 / 0.38 / 0.39 |

- 全文目標の書き手は例の文体に従う。悪い例 (長い) は密度と応答を大きく下げる。
- 1 発話目標の席は、よい例 (短い) を見せても短くならない。密度と応答がわずかに上がるだけ。gemma では譲る回数が 2.9 → 10.5 回/局に増える (譲り方は真似る)。

##### 2. 例と履歴の綱引き (同じ場面、各モデル約 5,000)

長い発話が続いたマルチ・1 発話の局の場面に、短い例 3 本を足して、次の 1 発話を生成し直した。

| モデル・目標 | 語数 (例なし → 例あり) | 100 語あたりの中身 | 水増し | 名指しの質問への応答 |
|---|---|---|---|---|
| gemma・全文 | 31.2 → 30.2 | 2.5 → 2.5 | 0.09 → 0.09 | 0.29 → 0.30 |
| gemma・1 発話 | 33.7 → 33.6 | 2.3 → 2.3 | 0.10 → 0.11 | 0.26 → 0.26 |
| Qwen・全文 | 21.3 → 21.3 | 3.2 → 3.2 | 0.05 → 0.05 | 0.32 → 0.34 |
| Qwen・1 発話 | 21.5 → 22.3 | 3.3 → 3.3 | 0.05 → 0.05 | 0.37 → 0.36 |

よい例は、悪い履歴に勝てない。手本として効くのは、例よりも一緒に話している相手の発話。

##### 3. 頭の中 (長さの読み出し、最良層の R²)

議論例 (譲った発話を除く、probe_talkonly_*.md):

| 条件 | モデル | なし | 短い例 | 長い例 |
|---|---|---|---|---|
| シングル・全文 | gemma | 0.73 | 0.74 | 0.71 |
| | Qwen | 0.67 | 0.60 | 0.67 |
| マルチ・1 発話 | gemma | 0.49 | 0.57 | 0.42 |
| | Qwen | 0.40 | 0.53 | 0.55 (基準線 0.45) |

綱引き (docs/tug_2026-10-31/probe_*.md、括弧は譲った発話を除く):

| モデル・目標 | 例なし | 短い例 |
|---|---|---|
| gemma・1 発話 | 0.62 (0.54) | 0.75 (0.66) |
| gemma・全文 | 0.75 (0.67) | 0.80 (0.65) |
| Qwen・1 発話 | 0.44 (0.40) | 0.47 (0.45) |
| Qwen・全文 | 0.58 (0.57) | 0.58 (0.57) |

- どの条件でも全文目標の方が長さを先に決めている。
- 短い例は 1 発話目標の頭の中を少し全文目標寄りにする (gemma で明確) が、行動 (長さ・中身) は変わらない。

##### 技術的な注意

- サーバは max-model-len 32768 (例で入力が伸びるため)。出力の上限は変えていない。
- 長い入力 (8,000 トークン超、綱引きは 7,000 超) の hidden states は、1,024 トークンずつ KV キャッシュを持ち越して計算した (scripts/extract_hidden.py の chunked_hidden)。1 回で流した値との一致は 20・40 層で類似度 0.9998 以上、最終層 0.993。区切った通話は索引の chunked_calls / chunked に記録。
- 短い例と長い例の生成は同じ秒に始まったため、局名 (設定・条件・時刻) が 2 つのフォルダで重なる。フォルダで区別する。

##### 出典

| 内容 | ファイル |
|---|---|
| 議論例の注釈集計 | annotation_*.md、qa_*.md |
| 議論例のプローブ | probe_*.md (全行)、probe_talkonly_*.md (譲りを除く) |
| 綱引きの頭の中 | docs/tug_2026-10-31/probe_*.md |
| ログ | log/fewshot/、log/goal_swap_ex/、log/line_judge/llama__*_ex.p*.jsonl |


#### gemma__ex-short: annotations

_Source: `docs/fewshot_2026-10-30/annotation_gemma__ex-short.md`_

#### Utterance-level annotations: log/annotation/annot_fewshot/gemma__ex-short  (raters: gptoss, llama; 180 games; v2 fields)

##### Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 47.0 | 7.1 | 2.3 | 6.3 | 49.3 | 11.5 | 1.8 |
| single-batch | 90 | llama | 50.1 | 9.4 | 14.2 | 2.0 | 34.8 | 16.9 | 10.9 |
| multi-private | 90 | gptoss | 55.6 | 11.5 | 5.7 | 7.3 | 64.8 | 25.9 | 4.9 |
| multi-private | 90 | llama | 58.7 | 16.1 | 15.8 | 5.6 | 43.3 | 38.8 | 14.1 |

##### Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 66.8 | 16.8 | 3.3 | 11.0 | 41.4 | 9.4 | 2.9 |
| single-batch | 30 | llama | 68.2 | 15.7 | 25.2 | 4.9 | 23.5 | 17.1 | 21.7 |
| multi-private | 30 | gptoss | 79.5 | 17.1 | 5.9 | 5.3 | 60.1 | 28.0 | 4.5 |
| multi-private | 30 | llama | 75.4 | 19.4 | 20.6 | 10.7 | 39.2 | 43.9 | 17.9 |

##### Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 40.5 | 1.1 | 1.9 | 4.7 | 53.1 | 12.5 | 1.6 |
| single-batch | 30 | llama | 46.2 | 3.3 | 9.9 | 0.5 | 39.9 | 16.8 | 6.5 |
| multi-private | 30 | gptoss | 44.8 | 6.4 | 9.2 | 12.9 | 58.1 | 27.8 | 8.6 |
| multi-private | 30 | llama | 48.7 | 10.2 | 18.3 | 4.1 | 40.7 | 39.2 | 17.1 |

##### Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 33.8 | 3.4 | 1.5 | 3.2 | 53.5 | 12.7 | 0.9 |
| single-batch | 30 | llama | 36.0 | 9.0 | 7.4 | 0.6 | 41.0 | 16.7 | 4.6 |
| multi-private | 30 | gptoss | 42.6 | 11.0 | 2.0 | 3.7 | 76.2 | 21.9 | 1.7 |
| multi-private | 30 | llama | 51.9 | 18.7 | 8.5 | 2.2 | 50.1 | 33.3 | 7.5 |

##### Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 567 | 35.7 | 49.3 | 11.5 | 8.69 |
| single-batch | llama | 567 | 35.7 | 34.8 | 16.3 | 6.13 |
| multi-private | gptoss | 1582 | 47.1 | 64.8 | 24.4 | 4.10 |
| multi-private | llama | 1582 | 47.1 | 43.3 | 36.5 | 2.74 |

##### Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 9 | 64 | 14 | 13 |
| single-batch | llama | 4 | 37 | 27 | 32 |
| multi-private | gptoss | 3 | 59 | 20 | 18 |
| multi-private | llama | 1 | 32 | 30 | 37 |

##### Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 7458 | 0.87 | 0.74 | 51.5 | 54.6 |
| gptoss vs llama | rebut | 7458 | 0.91 | 0.56 | 9.4 | 13.2 |
| gptoss vs llama | empty | 7458 | 0.87 | 0.26 | 4.2 | 14.6 |
| gptoss vs llama | padded | 7458 | 0.91 | 0.13 | 6.7 | 3.9 |
| gptoss vs llama | content (0/1/2) | 7458 | 0.53 | - | mean 1.38 | mean 0.94 |




#### gemma__ex-short: named questions

_Source: `docs/fewshot_2026-10-30/qa_gemma__ex-short.md`_

#### Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.8 | 0.54 | 0.33 | 0.36 | 0.60 |
| single-batch | llama | 3.8 | 0.54 | 0.18 | 0.25 | 0.66 |
| multi-private | gptoss | 5.8 | 0.54 | 0.11 | 0.08 | 0.32 |
| multi-private | llama | 5.8 | 0.54 | 0.04 | 0.04 | 0.31 |

#### Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.02 (n=300) |  |  |  | 1.05 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 2 | 1.04 (n=274) |  |  |  | 1.09 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 3 | 0.90 (n=134) |  |  |  | 0.87 (n=296) |  |  |  |  |  |  |  |  |  |
| 0 | 4 | 0.50 (n=2) |  |  |  | 0.52 (n=268) |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1.38 (n=900) |  |  |  | 1.38 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 1.12 (n=360) |  |  |  | 1.07 (n=416) |  |  |  |  |  |  |  |  |  |
| 1 | 3 | 1.08 (n=300) |  |  |  | 1.10 (n=408) |  |  |  |  |  |  |  |  |  |
| 1 | 4 | 0.93 (n=248) |  |  |  | 1.04 (n=382) |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 1.64 (n=600) |  |  |  | 1.50 (n=728) |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 0.99 (n=598) |  |  |  | 1.15 (n=728) |  |  |  |  |  |  |  |  |  |
| 2 | 3 | 1.02 (n=598) |  |  |  | 1.16 (n=728) |  |  |  |  |  |  |  |  |  |
| 2 | 4 | 0.91 (n=88) |  |  |  | 1.05 (n=716) |  |  |  |  |  |  |  |  |  |
| 3 | 1 | 1.52 (n=600) |  |  |  | 1.39 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 2 | 1.11 (n=598) |  |  |  | 1.16 (n=592) |  |  |  |  |  |  |  |  |  |
| 3 | 3 | 1.05 (n=584) |  |  |  | 1.05 (n=590) |  |  |  |  |  |  |  |  |  |
| 3 | 4 | 0.83 (n=250) |  |  |  | 0.95 (n=530) |  |  |  |  |  |  |  |  |  |



#### gemma__ex-short: probes (all lines)

_Source: `docs/fewshot_2026-10-30/probe_gemma__ex-short.md`_

#### Probes v3 (hidden/fewshot/gemma__ex-short; annotations log/annotation/annot_fewshot/gemma__ex-short, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3791 | words | 3791 | 0.482 | 0.897 (r 0.95) | 40 | +0.415 |
| single-batch | 3791 | content | 2818 | 0.207 | 0.378 (r 0.62) | 32 | +0.171 |
| single-batch | 3791 | has_content | 2818 | 0.761 | 0.889 | 48 | +0.129 |
| single-batch | 3791 | answers | 159 | 0.658 | 0.871 | 60 | +0.213 |
| multi-online | 4830 | words | 4830 | 0.422 | 0.867 (r 0.93) | 44 | +0.444 |
| multi-online | 4830 | content | 3892 | 0.093 | 0.310 (r 0.56) | 40 | +0.217 |
| multi-online | 4830 | has_content | 3892 | 0.662 | 0.885 | 44 | +0.222 |
| multi-online | 4830 | answers | 220 | 0.613 | 0.745 | 44 | +0.132 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.82 | 0.83 | 0.83 | 0.85 | 0.86 | 0.87 | 0.88 | 0.88 | 0.89 | 0.90 | 0.89 | 0.90 | 0.89 | 0.90 | 0.89 |
| multi-online | -0.00 | 0.82 | 0.80 | 0.80 | 0.81 | 0.83 | 0.82 | 0.84 | 0.84 | 0.85 | 0.87 | 0.87 | 0.87 | 0.86 | 0.85 | 0.83 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
| single-batch (layer 40) | 0.95 | 0.62 |
| multi-online (layer 44) | 0.47 | 0.93 |


#### gemma__ex-long: annotations

_Source: `docs/fewshot_2026-10-30/annotation_gemma__ex-long.md`_

#### Utterance-level annotations: log/annotation/annot_fewshot/gemma__ex-long  (raters: gptoss, llama; 180 games; v2 fields)

##### Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 49.2 | 6.9 | 3.7 | 8.3 | 60.8 | 14.7 | 2.5 |
| single-batch | 90 | llama | 49.1 | 8.6 | 16.7 | 6.7 | 37.5 | 23.6 | 12.6 |
| multi-private | 90 | gptoss | 68.0 | 13.8 | 8.3 | 11.3 | 72.5 | 29.6 | 7.6 |
| multi-private | 90 | llama | 68.3 | 17.3 | 21.7 | 10.9 | 46.2 | 46.1 | 20.1 |

##### Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 63.6 | 12.9 | 5.0 | 10.8 | 56.5 | 13.6 | 3.2 |
| single-batch | 30 | llama | 62.2 | 14.0 | 26.5 | 14.4 | 30.0 | 24.9 | 20.9 |
| multi-private | 30 | gptoss | 77.7 | 16.4 | 5.7 | 8.1 | 70.3 | 26.3 | 4.9 |
| multi-private | 30 | llama | 80.4 | 20.2 | 19.7 | 15.6 | 42.3 | 44.6 | 18.0 |

##### Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 38.8 | 2.8 | 2.8 | 8.1 | 58.3 | 15.7 | 2.1 |
| single-batch | 30 | llama | 40.5 | 4.8 | 12.4 | 1.4 | 40.5 | 22.6 | 8.6 |
| multi-private | 30 | gptoss | 60.5 | 10.8 | 13.7 | 17.5 | 64.1 | 34.7 | 12.7 |
| multi-private | 30 | llama | 60.0 | 13.1 | 26.9 | 6.7 | 45.0 | 49.9 | 24.8 |

##### Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 45.3 | 4.8 | 3.4 | 6.1 | 67.6 | 14.7 | 2.3 |
| single-batch | 30 | llama | 44.5 | 6.9 | 11.2 | 4.3 | 42.1 | 23.2 | 8.5 |
| multi-private | 30 | gptoss | 65.8 | 14.3 | 5.6 | 8.3 | 83.1 | 27.8 | 5.2 |
| multi-private | 30 | llama | 64.6 | 18.6 | 18.6 | 10.3 | 51.3 | 43.7 | 17.3 |

##### Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 868 | 42.9 | 60.8 | 14.3 | 7.00 |
| single-batch | llama | 868 | 42.9 | 37.5 | 23.1 | 4.32 |
| multi-private | gptoss | 2011 | 55.3 | 72.5 | 27.7 | 3.61 |
| multi-private | llama | 2011 | 55.3 | 46.2 | 43.5 | 2.30 |

##### Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 4 | 66 | 14 | 17 |
| single-batch | llama | 1 | 41 | 23 | 35 |
| multi-private | gptoss | 2 | 53 | 20 | 26 |
| multi-private | llama | 0 | 37 | 29 | 34 |

##### Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 8840 | 0.83 | 0.64 | 59.3 | 59.3 |
| gptoss vs llama | rebut | 8840 | 0.92 | 0.60 | 10.6 | 13.3 |
| gptoss vs llama | empty | 8840 | 0.83 | 0.29 | 6.4 | 19.6 |
| gptoss vs llama | padded | 8840 | 0.88 | 0.32 | 10.2 | 8.8 |
| gptoss vs llama | content (0/1/2) | 8840 | 0.48 | - | mean 1.36 | mean 0.85 |




#### gemma__ex-long: named questions

_Source: `docs/fewshot_2026-10-30/qa_gemma__ex-long.md`_

#### Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 4.1 | 0.56 | 0.16 | 0.17 | 0.44 |
| single-batch | llama | 4.1 | 0.56 | 0.05 | 0.08 | 0.48 |
| multi-private | gptoss | 7.5 | 0.72 | 0.06 | 0.03 | 0.21 |
| multi-private | llama | 7.5 | 0.72 | 0.01 | 0.01 | 0.19 |

#### Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.21 (n=300) |  |  |  | 1.33 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 2 | 1.24 (n=298) |  |  |  | 1.25 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 3 | 1.12 (n=298) |  |  |  | 1.22 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 4 | 0.44 (n=300) |  |  |  | 0.45 (n=300) |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1.29 (n=900) |  |  |  | 1.20 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 1.18 (n=734) |  |  |  | 1.10 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 3 | 1.05 (n=476) |  |  |  | 0.98 (n=886) |  |  |  |  |  |  |  |  |  |
| 1 | 4 | 0.95 (n=340) |  |  |  | 0.73 (n=816) |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 1.52 (n=600) |  |  |  | 1.40 (n=714) |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 1.14 (n=600) |  |  |  | 1.13 (n=714) |  |  |  |  |  |  |  |  |  |
| 2 | 3 | 1.10 (n=600) |  |  |  | 1.12 (n=714) |  |  |  |  |  |  |  |  |  |
| 2 | 4 | 0.88 (n=138) |  |  |  | 1.04 (n=714) |  |  |  |  |  |  |  |  |  |
| 3 | 1 | 1.41 (n=600) |  |  |  | 1.23 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 2 | 1.16 (n=600) |  |  |  | 1.09 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 3 | 1.03 (n=586) |  |  |  | 1.02 (n=598) |  |  |  |  |  |  |  |  |  |
| 3 | 4 | 0.79 (n=354) |  |  |  | 0.86 (n=600) |  |  |  |  |  |  |  |  |  |



#### gemma__ex-long: probes (all lines)

_Source: `docs/fewshot_2026-10-30/probe_gemma__ex-long.md`_

#### Probes v3 (hidden/fewshot/gemma__ex-long; annotations log/annotation/annot_fewshot/gemma__ex-long, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 2395 | words | 2395 | 0.541 | 0.899 (r 0.95) | 60 | +0.358 |
| single-batch | 2395 | content | 1861 | 0.185 | 0.343 (r 0.59) | 40 | +0.159 |
| single-batch | 2395 | has_content | 1861 | 0.796 | 0.903 | 36 | +0.107 |
| single-batch | 2395 | answers | 85 | – | – | – | – |
| multi-online | 4925 | words | 4925 | 0.498 | 0.813 (r 0.90) | 40 | +0.316 |
| multi-online | 4925 | content | 4600 | 0.114 | 0.351 (r 0.59) | 44 | +0.237 |
| multi-online | 4925 | has_content | 4600 | 0.732 | 0.906 | 40 | +0.174 |
| multi-online | 4925 | answers | 344 | 0.664 | 0.793 | 40 | +0.129 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.81 | 0.84 | 0.84 | 0.86 | 0.87 | 0.87 | 0.88 | 0.89 | 0.89 | 0.90 | 0.89 | 0.89 | 0.89 | 0.89 | 0.90 |
| multi-online | -0.00 | 0.74 | 0.73 | 0.74 | 0.75 | 0.77 | 0.74 | 0.78 | 0.77 | 0.79 | 0.81 | 0.81 | 0.80 | 0.78 | 0.76 | 0.71 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
| single-batch (layer 60) | 0.95 | 0.27 |
| multi-online (layer 40) | 0.49 | 0.90 |


#### qwen__ex-short: annotations

_Source: `docs/fewshot_2026-10-30/annotation_qwen__ex-short.md`_

#### Utterance-level annotations: log/annotation/annot_fewshot/qwen__ex-short  (raters: gptoss, llama; 180 games; v2 fields)

##### Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 35.8 | 3.9 | 5.0 | 5.5 | 67.6 | 8.2 | 3.2 |
| single-batch | 90 | llama | 41.4 | 6.6 | 11.1 | 3.4 | 46.3 | 11.9 | 8.8 |
| multi-private | 90 | gptoss | 65.6 | 8.2 | 5.0 | 8.3 | 81.0 | 15.0 | 4.7 |
| multi-private | 90 | llama | 64.7 | 14.1 | 19.5 | 5.7 | 45.9 | 26.7 | 17.7 |

##### Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 48.0 | 8.0 | 10.2 | 13.6 | 55.8 | 6.2 | 5.7 |
| single-batch | 30 | llama | 55.9 | 9.1 | 23.7 | 7.0 | 32.3 | 10.6 | 18.6 |
| multi-private | 30 | gptoss | 62.9 | 13.6 | 5.4 | 11.6 | 71.8 | 12.5 | 5.0 |
| multi-private | 30 | llama | 61.5 | 16.0 | 31.4 | 13.1 | 31.5 | 28.1 | 28.1 |

##### Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 26.3 | 1.2 | 3.7 | 2.3 | 75.6 | 9.5 | 3.4 |
| single-batch | 30 | llama | 32.0 | 4.8 | 8.2 | 3.1 | 49.4 | 14.0 | 6.9 |
| multi-private | 30 | gptoss | 63.4 | 4.0 | 4.1 | 5.8 | 86.1 | 16.0 | 3.9 |
| multi-private | 30 | llama | 62.2 | 12.0 | 15.1 | 3.4 | 50.1 | 26.9 | 14.6 |

##### Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 33.1 | 2.5 | 1.1 | 0.6 | 71.5 | 8.8 | 0.6 |
| single-batch | 30 | llama | 36.2 | 5.8 | 1.4 | 0.1 | 57.2 | 10.9 | 0.8 |
| multi-private | 30 | gptoss | 70.6 | 7.1 | 5.6 | 7.6 | 85.2 | 16.5 | 5.1 |
| multi-private | 30 | llama | 70.6 | 14.3 | 12.1 | 0.6 | 55.9 | 25.1 | 10.5 |

##### Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 540 | 51.0 | 67.6 | 8.0 | 12.52 |
| single-batch | llama | 540 | 51.0 | 46.3 | 11.7 | 8.57 |
| multi-private | gptoss | 1182 | 54.1 | 81.0 | 14.6 | 6.86 |
| multi-private | llama | 1182 | 54.1 | 45.9 | 25.8 | 3.88 |

##### Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 8 | 69 | 11 | 12 |
| single-batch | llama | 3 | 46 | 21 | 31 |
| multi-private | gptoss | 3 | 74 | 11 | 13 |
| multi-private | llama | 1 | 43 | 26 | 31 |

##### Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 9466 | 0.93 | 0.87 | 51.0 | 53.1 |
| gptoss vs llama | rebut | 9466 | 0.93 | 0.51 | 5.8 | 10.3 |
| gptoss vs llama | empty | 9466 | 0.88 | 0.32 | 4.8 | 14.3 |
| gptoss vs llama | padded | 9466 | 0.92 | 0.23 | 6.4 | 4.1 |
| gptoss vs llama | content (0/1/2) | 9466 | 0.48 | - | mean 1.41 | mean 0.88 |




#### qwen__ex-short: named questions

_Source: `docs/fewshot_2026-10-30/qa_qwen__ex-short.md`_

#### Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.6 | 0.59 | 0.29 | 0.37 | 0.58 |
| single-batch | llama | 3.6 | 0.59 | 0.16 | 0.23 | 0.63 |
| multi-private | gptoss | 3.2 | 0.80 | 0.14 | 0.10 | 0.40 |
| multi-private | llama | 3.2 | 0.80 | 0.03 | 0.04 | 0.38 |

#### Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.07 (n=300) |  |  |  | 1.25 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 2 | 1.21 (n=300) |  |  |  | 1.26 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 3 | 0.94 (n=300) |  |  |  | 1.06 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 4 | 0.25 (n=270) |  |  |  | 0.59 (n=290) |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1.22 (n=900) |  |  |  | 1.26 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 1.11 (n=900) |  |  |  | 1.25 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 3 | 1.15 (n=900) |  |  |  | 1.21 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 4 | 0.99 (n=736) |  |  |  | 0.91 (n=816) |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 1.25 (n=642) |  |  |  | 1.49 (n=674) |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 1.10 (n=642) |  |  |  | 1.25 (n=674) |  |  |  |  |  |  |  |  |  |
| 2 | 3 | 1.18 (n=642) |  |  |  | 1.19 (n=674) |  |  |  |  |  |  |  |  |  |
| 2 | 4 | 1.08 (n=416) |  |  |  | 1.05 (n=616) |  |  |  |  |  |  |  |  |  |
| 3 | 1 | 1.34 (n=590) |  |  |  | 1.33 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 2 | 1.13 (n=590) |  |  |  | 1.20 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 3 | 1.17 (n=590) |  |  |  | 1.13 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 4 | 1.07 (n=470) |  |  |  | 1.01 (n=600) |  |  |  |  |  |  |  |  |  |



#### qwen__ex-short: probes (all lines)

_Source: `docs/fewshot_2026-10-30/probe_qwen__ex-short.md`_

#### Probes v3 (hidden/fewshot/qwen__ex-short; annotations log/annotation/annot_fewshot/qwen__ex-short, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3432 | words | 3432 | 0.259 | 0.767 (r 0.88) | 52 | +0.508 |
| single-batch | 3432 | content | 3205 | 0.058 | 0.275 (r 0.52) | 52 | +0.216 |
| single-batch | 3432 | has_content | 3205 | 0.710 | 0.865 | 52 | +0.155 |
| single-batch | 3432 | answers | 126 | 0.682 | 0.865 | 8 | +0.184 |
| multi-online | 4896 | words | 4896 | 0.198 | 0.594 (r 0.77) | 52 | +0.396 |
| multi-online | 4896 | content | 4820 | 0.156 | 0.336 (r 0.58) | 52 | +0.181 |
| multi-online | 4896 | has_content | 4820 | 0.802 | 0.884 | 48 | +0.081 |
| multi-online | 4896 | answers | 204 | 0.532 | 0.721 | 52 | +0.189 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.71 | 0.72 | 0.72 | 0.74 | 0.75 | 0.74 | 0.74 | 0.75 | 0.75 | 0.75 | 0.76 | 0.77 | 0.77 | 0.74 | 0.73 | 0.70 |
| multi-online | -0.00 | 0.36 | 0.41 | 0.46 | 0.47 | 0.48 | 0.49 | 0.47 | 0.50 | 0.55 | 0.54 | 0.55 | 0.58 | 0.59 | 0.58 | 0.57 | 0.53 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
| single-batch (layer 52) | 0.88 | 0.56 |
| multi-online (layer 52) | 0.55 | 0.77 |


#### qwen__ex-long: annotations

_Source: `docs/fewshot_2026-10-30/annotation_qwen__ex-long.md`_

#### Utterance-level annotations: log/annotation/annot_fewshot/qwen__ex-long  (raters: gptoss, llama; 180 games; v2 fields)

##### Per 100 utterances (game mean, then condition mean; all domains)

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 90 | gptoss | 48.3 | 5.3 | 5.9 | 11.0 | 77.4 | 10.4 | 5.3 |
| single-batch | 90 | llama | 50.5 | 9.5 | 21.0 | 5.6 | 41.9 | 19.5 | 19.2 |
| multi-private | 90 | gptoss | 73.5 | 12.7 | 15.9 | 16.7 | 73.3 | 19.2 | 15.5 |
| multi-private | 90 | llama | 71.6 | 18.3 | 30.6 | 5.2 | 42.0 | 34.3 | 29.0 |

##### Per 100 utterances: aiwolf

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 53.3 | 10.5 | 3.3 | 17.8 | 66.9 | 7.7 | 2.7 |
| single-batch | 30 | llama | 55.7 | 10.6 | 29.6 | 10.4 | 29.6 | 18.2 | 27.4 |
| multi-private | 30 | gptoss | 70.8 | 20.4 | 10.9 | 17.6 | 70.3 | 14.1 | 10.1 |
| multi-private | 30 | llama | 65.9 | 18.2 | 36.2 | 9.7 | 32.3 | 31.7 | 33.2 |

##### Per 100 utterances: candidate_selection

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 43.9 | 1.9 | 9.7 | 8.5 | 82.1 | 12.1 | 8.9 |
| single-batch | 30 | llama | 47.2 | 7.0 | 21.5 | 4.0 | 47.8 | 21.2 | 19.5 |
| multi-private | 30 | gptoss | 75.8 | 7.6 | 15.8 | 13.4 | 75.8 | 21.3 | 15.6 |
| multi-private | 30 | llama | 75.3 | 15.9 | 29.3 | 3.1 | 45.3 | 37.2 | 28.2 |

##### Per 100 utterances: shared_living

| condition | games | rater | resp | rebut | empty | padded | contrib_per_game | words_per_contrib | empty_word_share |
|---|---|---|---|---|---|---|---|---|---|
| single-batch | 30 | gptoss | 47.7 | 3.3 | 4.9 | 6.5 | 83.2 | 11.3 | 4.2 |
| single-batch | 30 | llama | 48.7 | 10.9 | 11.8 | 2.3 | 48.4 | 19.0 | 10.6 |
| multi-private | 30 | gptoss | 73.9 | 10.3 | 21.0 | 19.1 | 73.9 | 22.1 | 20.7 |
| multi-private | 30 | llama | 73.7 | 20.7 | 26.2 | 2.8 | 48.4 | 33.8 | 25.6 |

##### Totals per game (condition means; content = number of new contributions)

| condition | rater | words/game | utterances/game | content/game | words per content | content per 100 words |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 781 | 50.9 | 77.4 | 10.1 | 9.91 |
| single-batch | llama | 781 | 50.9 | 41.9 | 18.6 | 5.37 |
| multi-private | gptoss | 1345 | 55.7 | 73.3 | 18.3 | 5.45 |
| multi-private | llama | 1345 | 55.7 | 42.0 | 32.0 | 3.12 |

##### Response types (share of responsive utterances; all domains)

| condition | rater | answer | add | object | agree |
|---|---|---|---|---|---|
| single-batch | gptoss | 3 | 72 | 9 | 15 |
| single-batch | llama | 1 | 40 | 23 | 37 |
| multi-private | gptoss | 2 | 62 | 15 | 21 |
| multi-private | llama | 0 | 32 | 30 | 37 |

##### Agreement between raters (utterances annotated by both; every pair)

| pair | flag | n | percent agreement | Cohen's kappa | rate A | rate B |
|---|---|---|---|---|---|---|
| gptoss vs llama | resp | 9595 | 0.95 | 0.89 | 61.6 | 61.6 |
| gptoss vs llama | rebut | 9595 | 0.89 | 0.46 | 8.6 | 14.0 |
| gptoss vs llama | empty | 9595 | 0.81 | 0.38 | 11.4 | 25.2 |
| gptoss vs llama | padded | 9595 | 0.87 | 0.21 | 13.6 | 4.8 |
| gptoss vs llama | content (0/1/2) | 9595 | 0.37 | - | mean 1.41 | mean 0.79 |




#### qwen__ex-long: named questions

_Source: `docs/fewshot_2026-10-30/qa_qwen__ex-long.md`_

#### Question -> answer rate (derived from resp_to / resp_type)

`answered` columns require resp_type = answer; `addressee's next line responds` only requires that the addressee's next utterance in the period has resp_to = the question (any response type: the type-independent definition).

| condition | rater | questions/game | addressed (@) share | answered (any) | answered by addressee | addressee's next line responds |
|---|---|---|---|---|---|---|
| single-batch | gptoss | 3.3 | 0.35 | 0.10 | 0.08 | 0.28 |
| single-batch | llama | 3.3 | 0.35 | 0.02 | 0.03 | 0.30 |
| multi-private | gptoss | 4.9 | 0.55 | 0.12 | 0.10 | 0.40 |
| multi-private | llama | 4.9 | 0.55 | 0.02 | 0.02 | 0.39 |

#### Position-aligned content (mean content per utterance, raters pooled; rows = period, turn)

| period | turn | single-batch | single-batch-stepped | single-online | multi-public | multi-private | single-batch-process | multi-private-process | multi-private-stepped | multi-public-stepped | multi-private-stepped-process | single-batch-stepped-process | single-online-process | multi-public-process | multi-public-stepped-process |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1.42 (n=300) |  |  |  | 1.19 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 2 | 1.35 (n=300) |  |  |  | 1.17 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 3 | 1.09 (n=300) |  |  |  | 0.87 (n=300) |  |  |  |  |  |  |  |  |  |
| 0 | 4 | 0.52 (n=230) |  |  |  | 0.53 (n=298) |  |  |  |  |  |  |  |  |  |
| 1 | 1 | 1.40 (n=900) |  |  |  | 1.41 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 2 | 1.24 (n=890) |  |  |  | 1.16 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 3 | 1.14 (n=890) |  |  |  | 0.86 (n=900) |  |  |  |  |  |  |  |  |  |
| 1 | 4 | 0.76 (n=696) |  |  |  | 0.49 (n=890) |  |  |  |  |  |  |  |  |  |
| 2 | 1 | 1.46 (n=624) |  |  |  | 1.53 (n=710) |  |  |  |  |  |  |  |  |  |
| 2 | 2 | 1.19 (n=624) |  |  |  | 1.23 (n=710) |  |  |  |  |  |  |  |  |  |
| 2 | 3 | 1.21 (n=624) |  |  |  | 1.12 (n=710) |  |  |  |  |  |  |  |  |  |
| 2 | 4 | 1.06 (n=594) |  |  |  | 0.79 (n=710) |  |  |  |  |  |  |  |  |  |
| 3 | 1 | 1.38 (n=590) |  |  |  | 1.30 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 2 | 1.14 (n=590) |  |  |  | 1.06 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 3 | 1.06 (n=580) |  |  |  | 0.91 (n=600) |  |  |  |  |  |  |  |  |  |
| 3 | 4 | 0.98 (n=430) |  |  |  | 0.75 (n=600) |  |  |  |  |  |  |  |  |  |



#### qwen__ex-long: probes (all lines)

_Source: `docs/fewshot_2026-10-30/probe_qwen__ex-long.md`_

#### Probes v3 (hidden/fewshot/qwen__ex-long; annotations log/annotation/annot_fewshot/qwen__ex-long, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3552 | words | 3552 | 0.296 | 0.759 (r 0.87) | 20 | +0.463 |
| single-batch | 3552 | content | 3365 | 0.144 | 0.462 (r 0.68) | 52 | +0.318 |
| single-batch | 3552 | has_content | 3365 | 0.791 | 0.925 | 36 | +0.133 |
| single-batch | 3552 | answers | 90 | – | – | – | – |
| multi-online | 4820 | words | 4820 | 0.418 | 0.534 (r 0.73) | 48 | +0.116 |
| multi-online | 4820 | content | 4811 | 0.249 | 0.415 (r 0.64) | 52 | +0.167 |
| multi-online | 4820 | has_content | 4811 | 0.814 | 0.887 | 52 | +0.073 |
| multi-online | 4820 | answers | 201 | 0.449 | 0.772 | 56 | +0.323 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.02 | 0.73 | 0.73 | 0.73 | 0.75 | 0.76 | 0.76 | 0.76 | 0.75 | 0.75 | 0.74 | 0.75 | 0.75 | 0.73 | 0.69 | 0.67 | 0.65 |
| multi-online | -0.01 | 0.43 | 0.45 | 0.46 | 0.47 | 0.47 | 0.47 | 0.47 | 0.48 | 0.50 | 0.50 | 0.51 | 0.53 | 0.51 | 0.50 | 0.49 | 0.46 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|
| single-batch (layer 20) | 0.88 | 0.40 |
| multi-online (layer 48) | 0.40 | 0.73 |


#### gemma-none: length probe, talk lines only

_Source: `docs/fewshot_2026-10-30/probe_talkonly_gemma-none.md`_

#### Probes v3 (hidden/main_gemma31b; annotations log/annotation/annot_main, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 2656 | words | 2656 | 0.430 | 0.734 (r 0.86) | 40 | +0.304 |
| multi-online | 4719 | words | 4719 | 0.218 | 0.489 (r 0.70) | 40 | +0.271 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.61 | 0.63 | 0.65 | 0.66 | 0.66 | 0.68 | 0.70 | 0.71 | 0.73 | 0.73 | 0.71 | 0.70 | 0.69 | 0.68 | 0.64 |
| multi-online | -0.00 | 0.36 | 0.36 | 0.37 | 0.38 | 0.39 | 0.40 | 0.44 | 0.46 | 0.48 | 0.49 | 0.49 | 0.49 | 0.48 | 0.47 | 0.46 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|


#### gemma-short: length probe, talk lines only

_Source: `docs/fewshot_2026-10-30/probe_talkonly_gemma-short.md`_

#### Probes v3 (hidden/fewshot/gemma__ex-short; annotations log/annotation/annot_fewshot/gemma__ex-short, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 2818 | words | 2818 | 0.452 | 0.736 (r 0.86) | 36 | +0.284 |
| multi-online | 3892 | words | 3892 | 0.277 | 0.568 (r 0.75) | 40 | +0.291 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.01 | 0.64 | 0.63 | 0.65 | 0.67 | 0.69 | 0.69 | 0.72 | 0.73 | 0.74 | 0.73 | 0.72 | 0.72 | 0.71 | 0.71 | 0.68 |
| multi-online | -0.00 | 0.45 | 0.43 | 0.44 | 0.45 | 0.46 | 0.47 | 0.50 | 0.52 | 0.55 | 0.57 | 0.56 | 0.55 | 0.54 | 0.53 | 0.49 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|


#### gemma-long: length probe, talk lines only

_Source: `docs/fewshot_2026-10-30/probe_talkonly_gemma-long.md`_

#### Probes v3 (hidden/fewshot/gemma__ex-long; annotations log/annotation/annot_fewshot/gemma__ex-long, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 1861 | words | 1861 | 0.432 | 0.708 (r 0.84) | 36 | +0.276 |
| multi-online | 4600 | words | 4600 | 0.180 | 0.416 (r 0.65) | 48 | +0.237 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.00 | 0.59 | 0.61 | 0.62 | 0.64 | 0.64 | 0.66 | 0.68 | 0.70 | 0.71 | 0.71 | 0.69 | 0.68 | 0.67 | 0.66 | 0.62 |
| multi-online | -0.00 | 0.32 | 0.30 | 0.31 | 0.32 | 0.32 | 0.32 | 0.36 | 0.37 | 0.39 | 0.41 | 0.42 | 0.42 | 0.41 | 0.40 | 0.37 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|


#### qwen-none: length probe, talk lines only

_Source: `docs/fewshot_2026-10-30/probe_talkonly_qwen-none.md`_

#### Probes v3 (hidden/main_qwen38; annotations log/annotation/annot_qwen, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 2767 | words | 2767 | 0.310 | 0.667 (r 0.82) | 20 | +0.357 |
| multi-online | 4970 | words | 4970 | 0.253 | 0.404 (r 0.64) | 48 | +0.151 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.02 | 0.62 | 0.63 | 0.63 | 0.66 | 0.67 | 0.67 | 0.65 | 0.65 | 0.61 | 0.61 | 0.62 | 0.63 | 0.61 | 0.51 | 0.42 | 0.35 |
| multi-online | -0.01 | 0.25 | 0.29 | 0.31 | 0.33 | 0.34 | 0.34 | 0.34 | 0.34 | 0.38 | 0.38 | 0.38 | 0.40 | 0.39 | 0.38 | 0.37 | 0.36 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|


#### qwen-short: length probe, talk lines only

_Source: `docs/fewshot_2026-10-30/probe_talkonly_qwen-short.md`_

#### Probes v3 (hidden/fewshot/qwen__ex-short; annotations log/annotation/annot_fewshot/qwen__ex-short, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3205 | words | 3205 | 0.268 | 0.597 (r 0.77) | 20 | +0.329 |
| multi-online | 4820 | words | 4820 | 0.245 | 0.528 (r 0.73) | 48 | +0.283 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.01 | 0.57 | 0.57 | 0.57 | 0.59 | 0.60 | 0.59 | 0.58 | 0.59 | 0.58 | 0.57 | 0.57 | 0.60 | 0.57 | 0.52 | 0.47 | 0.41 |
| multi-online | -0.01 | 0.38 | 0.40 | 0.42 | 0.43 | 0.43 | 0.42 | 0.43 | 0.46 | 0.50 | 0.50 | 0.50 | 0.53 | 0.51 | 0.50 | 0.48 | 0.45 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|


#### qwen-long: length probe, talk lines only

_Source: `docs/fewshot_2026-10-30/probe_talkonly_qwen-long.md`_

#### Probes v3 (hidden/fewshot/qwen__ex-long; annotations log/annotation/annot_fewshot/qwen__ex-long, rater llama)

Ridge, grouped 5-fold by setup, nested penalty choice. R^2 (r) for words / content, AUC for has_content / answers. `base` = input features only. Names: multi-batch = multi-private-stepped, multi-online = multi-private.

##### A. Best layer per condition and target

| condition | lines | target | n | base | hidden (best layer) | layer | gain |
|---|---|---|---|---|---|---|---|
| single-batch | 3365 | words | 3365 | 0.348 | 0.669 (r 0.82) | 20 | +0.321 |
| multi-online | 4811 | words | 4811 | 0.445 | 0.545 (r 0.74) | 48 | +0.100 |

##### B. Layer curve, words (R^2)

| condition | 0 | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 40 | 44 | 48 | 52 | 56 | 60 | 64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single-batch | -0.03 | 0.64 | 0.65 | 0.64 | 0.66 | 0.67 | 0.66 | 0.64 | 0.63 | 0.62 | 0.61 | 0.61 | 0.61 | 0.56 | 0.48 | 0.44 | 0.40 |
| multi-online | -0.01 | 0.46 | 0.47 | 0.49 | 0.49 | 0.49 | 0.48 | 0.49 | 0.50 | 0.51 | 0.51 | 0.52 | 0.54 | 0.53 | 0.52 | 0.50 | 0.48 |

##### C. Transfer of the words probe (Pearson r on held-out setups; rows = fitted on, columns = applied to)

| fitted on \ applied to | single-batch | multi-online |
|---|---|---|


#### examples vs history, gemma: length probe on identical states

_Source: `docs/tug_2026-10-31/probe_gemma.md`_

#### Length probe, long-history states with / without 3 short examples: gemma

Same states (multi-online games). gen = last prompt token. R^2 (r) at each stored layer; `talk` = Skip / Over lines dropped.

| goal | examples | n | mean words | L20 | L40 | L48 | L56 | best (talk only) |
|---|---|---|---|---|---|---|---|---|
| online | none | 4982 | 33.7 | 0.43 (0.66) | 0.59 (0.77) | 0.62 (0.79) | 0.62 (0.79) | 0.54 |
| online | 3 short | 4982 | 33.6 | 0.54 (0.74) | 0.71 (0.84) | 0.75 (0.86) | 0.74 (0.86) | 0.66 |
| batch | none | 4982 | 31.1 | 0.64 (0.80) | 0.73 (0.85) | 0.75 (0.87) | 0.75 (0.87) | 0.67 |
| batch | 3 short | 4982 | 30.2 | 0.66 (0.81) | 0.77 (0.88) | 0.79 (0.89) | 0.80 (0.89) | 0.65 |


#### examples vs history, qwen: length probe on identical states

_Source: `docs/tug_2026-10-31/probe_qwen.md`_

#### Length probe, long-history states with / without 3 short examples: qwen

Same states (multi-online games). gen = last prompt token. R^2 (r) at each stored layer; `talk` = Skip / Over lines dropped.

| goal | examples | n | mean words | L20 | L32 | L48 | L52 | best (talk only) |
|---|---|---|---|---|---|---|---|---|
| online | none | 4996 | 21.5 | 0.35 (0.60) | 0.37 (0.61) | 0.43 (0.66) | 0.44 (0.66) | 0.40 |
| online | 3 short | 4996 | 22.3 | 0.35 (0.59) | 0.38 (0.62) | 0.46 (0.68) | 0.47 (0.69) | 0.45 |
| batch | none | 4996 | 21.3 | 0.57 (0.75) | 0.58 (0.76) | 0.58 (0.76) | 0.57 (0.75) | 0.57 |
| batch | 3 short | 4996 | 21.3 | 0.57 (0.75) | 0.58 (0.76) | 0.57 (0.75) | 0.56 (0.75) | 0.57 |

### E.7 Japanese summaries written along the way

_Source: `docs/progress_report_2026-10-29/hidden_states_2026-10-30.md`_

#### 生成目標の分析 (2026-10-30): プローブの追加、目標の入れ替え、介入

前日のまとめ (hidden_states.md) の続き。生成目標を主軸にした構成 (single-batch / single-online / multi-batch / multi-online の 2×2) に合わせて、3 つの分析を足した。
呼び名: multi-batch = multi-private-stepped、multi-online = multi-private (コード上の名前は変えていない)。

##### 1. プローブの追加 (docs/main_*/probe_summary_v3.md)

生成直前の hidden states から、これから書く 1 発話の性質を線形 (リッジ) で読み出す。設定単位の 5 分割、入れ子で正則化を選ぶ。基準線は入力特徴だけの回帰。

###### 1a. 長さ以外も読めるが、生成目標による差はない

| 条件 | 新しい内容の数 R² (gemma / Qwen) | 内容があるか AUC | 質問に答えるか AUC |
|---|---|---|---|
| single-batch | 0.39 / 0.32 | 0.88 / 0.86 | 0.84 / 0.90 |
| single-online | 0.48 / 0.22 | 0.92 / 0.81 | 0.91 / 0.75 |
| multi-batch | 0.30 / 0.36 | 0.88 / 0.88 | 0.85 / 0.88 |
| multi-online | 0.40 / 0.32 | 0.92 / 0.85 | 0.84 / 0.71 |

- どの条件でも基準線より読める。ただし全文目標の方が読みやすい、という差は両モデルともない。
- 「質問に答えるか」は条件あたり 100〜370 例と少なく、AUC はぶれが大きい。

###### 1b. 長さの読み出し方は、生成目標で分かれる (転移)

ある条件で学習した「長さの読み出し」を別の条件に当てたときの相関 (Pearson r)。行が学習した条件、列が当てた条件。

gemma:

| 学習 \ 適用 | single-batch | single-batch-stepped | single-online | multi-batch | multi-online |
|---|---|---|---|---|---|
| single-batch | 0.93 | 0.93 | 0.54 | 0.86 | 0.34 |
| single-online | 0.55 | 0.53 | 0.89 | 0.54 | 0.72 |
| multi-batch | 0.88 | 0.88 | 0.79 | 0.91 | 0.58 |
| multi-online | 0.57 | 0.58 | 0.79 | 0.61 | 0.85 |

Qwen:

| 学習 \ 適用 | single-batch | single-batch-stepped | single-online | multi-batch | multi-online |
|---|---|---|---|---|---|
| single-batch | 0.89 | 0.87 | −0.19 | 0.78 | −0.12 |
| single-online | 0.61 | 0.61 | 0.66 | 0.55 | 0.57 |
| multi-batch | 0.88 | 0.87 | −0.04 | 0.86 | −0.08 |
| multi-online | 0.67 | 0.67 | 0.52 | 0.60 | 0.66 |

- 全文目標の条件で学んだ読み出しは、書き手が 1 人でも席ごとでも、全文目標の条件どうしで通じる (0.78〜0.93)。
- 1 発話目標の条件には通じない。Qwen ではほぼ 0 か負。
- 平たく言うと、同じ「長さ」でも、全文目標と 1 発話目標でモデル内部の表し方が違う。分かれ目は書き手ではなく生成目標。
- 層ごとの曲線: gemma は 40〜48 層、Qwen は全文目標で 20 層、1 発話目標で 48〜52 層が最もよく読める (最良層そのものが目標で違う)。

##### 2. 目標の入れ替え (docs/main_*/goal_swap_summary.md)

記録済みの場面 (参加者の指示 + ここまでの会話 + 自分の札) を、履歴をまったく同じにしたまま、生成目標の指示だけ入れ替えて次の 1 発話を生成し直した。温度 0、両モデルとも全件 (筋書きなしの局、各方向約 5,000 場面)。

| 入れ替えの向き | gemma: 元 → 後 | Qwen: 元 → 後 | 長くなった場面 (gemma / Qwen) | 同じ向きの設定 |
|---|---|---|---|---|
| 全文目標 → 1 発話目標 (短い履歴) | 16.1 → 27.4 (+11.3) | 12.0 → 15.6 (+3.6) | 94% / 79% | 両モデルとも 90/90 で長くなる |
| 1 発話目標 → 全文目標 (長い履歴) | 33.7 → 31.1 (−2.5) | 21.5 → 21.3 (−0.2) | 32% / 42% | gemma 90/90、Qwen 61/90 で短くなる |

読み:
- 短い発話が続く会話でも、指示を「次の 1 発話」に替えるだけで、その場で発話が長くなる。生成目標は長さの直接の原因。
- 長い発話が続く会話で全文目標に替えても、ほとんど短くならない。全文目標のモデルは履歴の文体に合わせて書く。
- したがって冗長さは 2 段で生じる: (1) 1 発話目標が発話を長くする、(2) 長い発話が履歴にたまり、文体として固定される。
- 目標の直接の効果が全体の差に占める割合: gemma は 11.3 / 17.6 ≒ 64%、Qwen は 3.6 / 9.5 ≒ 38%。残りは履歴の積み重ね。

##### 3. 介入 (方向の加算) (docs/steering_2026-10-30/summary.md)

対比による活性化の加算 (Contrastive Activation Addition)。同じ場面を 2 つの枠組みで与え、両方に共通するトークン (札の「:」) での表現の差を平均して「生成目標の方向」とした。それを 1 発話目標の枠組みの生成中に足し、全文目標並みに短くなるかを見た (gemma、学習 60 設定・試験 30 設定の一部)。

| 層 | そのまま | 方向を足す (壊れない範囲の最大) | 全文目標の枠組み (参考) |
|---|---|---|---|
| 40 | 26.6 語 | 27.5 語 (×1.5) | 13.7 語 |
| 20 | 25.1 語 | 26.9 語 (×4) | 12.7 語 |
| 52 | 25.1 語 | 25.6 語 (×2)。×4 で崩壊 | 12.7 語 |

- どの層・大きさでも、1 本の方向を足すだけでは長さは動かなかった。求めた方向は足しても出力が壊れない自然な方向だった (同じ大きさの無作為な方向は層 40・52 で崩壊)。
- 生成目標の効果は、1 か所の 1 本の方向では運べない。指示の文脈全体 (多くの位置・層) に分散していると考えられる。
- 最初の版 (最後のトークンの位置で差を取る) は、2 つの枠組みで最後のトークン自体が違うため、トークンの違いを拾って出力を壊した。破棄。

##### 蒸留への示唆

- 教師 = multi-batch、生徒 = multi-online の組み合わせは、行動・表現の両面で支持される (1b の転移、2 の入れ替え)。
- 介入が効かなかったので、生成直前の表現を 1 点で合わせる蒸留は弱いと予想される。**出力 (教師の行の確率分布) を合わせる蒸留**を第一候補にする。表現を合わせるなら、多層・多位置で合わせる。
- 2 の結果から、会話の最初の数発話を短くできれば、履歴の積み重ねを通じて残りも短くなる。学習データは会話の早い場面を厚めにする価値がある。
- 入れ替え実験の出力 (同じ場面での全文目標の行) は、そのまま蒸留の教師データとして使える (gemma・Qwen 各約 5,000 場面)。

##### 出典

| 内容 | ファイル |
|---|---|
| プローブ | docs/main_gemma31b/probe_summary_v3.md、docs/main_qwen38/probe_summary_v3.md、scripts/probe_hidden2.py |
| 入れ替え | docs/main_gemma31b/goal_swap_summary.md、docs/main_qwen38/goal_swap_summary.md、scripts/goal_swap.py、scripts/goal_swap_summary.py |
| 介入 | docs/steering_2026-10-30/summary.md、scripts/steer_goal2.py (scripts/steer_goal.py は破棄した版) |

## F. Reproducibility notes

- Determinism: gemma outputs are identical across instances under `VLLM_BATCH_INVARIANT=1`; Qwen only within an instance (every call of a setup pinned to one instance). Judges are not batch invariant (temperature 0).
- Hidden states are replays of the recorded token ids (`scripts/extract_hidden.py`); sequences over 8,000 tokens (7,000 in `swap_hidden.py`) are computed in 1,024-token chunks with the KV cache carried over (cosine to the one-pass value ≥ 0.9998 at layers 20/40, 0.993 at the last layer); such calls are listed in the index files.
- Excluded: single-batch games whose script lines could not be matched to the gen-point positions (gemma 18, Qwen 38) in the probes; unparsed line-judge replies (gemma 0.5%, Qwen 1.1%).
- Plan conditions for Qwen were first generated with gemma's plans; those games are set aside in `log/main_qwen38_gemmaplans/` and not used. Qwen's own plans passed validation for 56/90 setups only; the plan conditions are reported for gemma.
- The short- and long-example runs started in the same second, so a game id can occur in both folders; the folder tells them apart.
- Annotation outputs and the session's orchestration scripts are kept in `log/annotation/` and `log/stage_scripts/`.


#### Implementation notes

_Source: `docs/IMPLEMENTATION_NOTES.md`_

#### 実装契約 (server / agent / single / convert の共通ルール)

DESIGN.md (v0.4) が仕様。ここは実装者間の取り決め。`common/` は既に実装済みで、変更する場合はこのファイルと DESIGN.md も直す。

##### 0. 環境

- `uv` プロジェクト。`.venv/bin/python` を使う (`export PATH="$HOME/.local/bin:$PATH"; uv run ...` でもよい)。
- import は `from common.protocol import ...` の形 (リポジトリ直下が sys.path。scripts/ からは `sys.path.insert(0, ROOT)`)。
- テストは `tests/` に pytest。LLM を呼ぶテストは書かない (台本エージェント・固定文字列で代替)。
- 外部 API は呼ばない。vLLM も起動しない (パイロットは人間が行う)。

##### 1. 共通 API (実装済み)

- `common.setup.GameContext.load(setup_id | path)` : setup + personas + roles + rules + instance。
  `ctx.names` (席順), `ctx.speaking_order_names`, `ctx.name_of_seat`, `ctx.seat_of_name`, `ctx.role_of_name`,
  `ctx.problem_of_seat`, `ctx.card_pool()`, `ctx.card_by_title`, `ctx.options()`, `ctx.option_labels()`,
  `ctx.fixed_cards_of_seat`, `ctx.check_dynamic_ready()`。
- `common.render.make_env(*extra_dirs)`, `shared_block(env, ctx, block, **kw)`, `identity_block(env, ctx, seat)`,
  `rules_context(ctx)` (rules.yml の全変数 + roster, speaking_order_names, topic, options, card_titles, Period,
  action_request_sentences, vote_request_sentence ...)。
- `common.logwriter.GameLogWriter(game_dir, game_id, names)`: `status / talk / pass_ / vote / action / result`
  (CSV 行、seq 自動) と `header / llm_call / record(kind, ...)` (jsonl)。`read_log`, `read_jsonl`。
- `common.tiebreak.tally(votes: {voter: target|None}, setup_id, round_no) -> Tally(counts, top, chosen, tie)`。
- `common.protocol`: `Request`, `Packet`, `Info`, `Setting`, `Talk`, `Judge`, `Vote`, `Role`, `Status`,
  `T_SKIP / T_OVER / T_FORCE_SKIP / ACK`。

##### 2. game_id とログ置き場

- `game_id = f"{setup_id}__{method}__{model_tag}__{YYYYmmddTHHMMSS}"`。`model_tag` は models.yml のモデル名の最後のパス要素を `[^A-Za-z0-9.-]` → `-` にしたもの。台本エージェントは `scripted`。
- `log/<domain>/<method>/<game_id>/` に `<game_id>.log`, `<game_id>.jsonl`, `raw/`。
- jsonl header (server または single が書く): `game_id, setup_id, domain, method, model (models.yml のフルネーム), model_tag,
  info_mode, setup_path (リポジトリ相対), setup_sha1 (setup JSON の sha1), started_at, finished_at (tz 付き UTC ISO),
  participants=[{seat,name,role_slot,persona:{name,age,gender,personality},private_seed}], speaking_order (席番号),
  card_pool (domain のみ、card_id/title/origin_seat。aiwolf は `[]`), n_options, n_unique_cards (aiwolf は 0), outcome,
  rules_hash (rules.yml の sha1)`。
- `--info-mode dynamic|fixed` は server / agent / single / run_multi の全 CLI にあり、`GameContext.load` 直後に
  `ctx.setup.info_mode` を上書きする。multi では server と 5 agent に同じ値を渡す (run_multi が転送する)。
  header の `info_mode` が実際の値で、`convert_logs.py` はこれで GameContext を組む。

##### 3. サーバの進行 (server/base)

要求列 (全ドメイン): `NAME` → `INITIALIZE` → 各ラウンド [`DAILY_INITIALIZE` → `TALK`×最大4ターン → (`VOTE`) → (ACTION) → `DAILY_FINISH`] → `FINISH`。

- 接続: websocket サーバ (`websockets`)。5 本の接続を待ち、`NAME` を送って応答を接続名とする。接続名は `seat1..seat5`
  のいずれかで重複不可。それ以外は拒否 (接続を閉じて待ち直す)。全席そろってから開始。
- `info.agent` は席のペルソナ名。`info.profile` は INITIALIZE のみ、ペルソナの4項目だけ ("Name: ..\nAge: ..\nGender: ..\nPersonality: .."、
  4 行)。非公開種 (役職 / 困りごと) の行は含めない (agent の identity ブロックが持つ。domain は `info.problem`)。
  `info.role_map` は自席の役職のみ (aiwolf)。domain では `role_map` は `{name: "PARTICIPANT"}` 自席のみ、`info.problem` に困りごと、
  `info.card_titles` (dynamic のみ) にタイトル一覧。
- `talk_history`: その席に**まだ送っていない** talk の差分 (Go サーバと同じ)。Skip/Over も Talk として含める (`skip`/`over` フラグ、text は "Skip"/"Over")。
- TALK: `speaking_order` の順に、生存かつ Over していない席に送る。turn は 1..4。応答を strip し、空なら Over (`empty:true`)、
  `ForceSkip` なら Skip (`forced:true`)、`Skip`/`Over` (大文字小文字と末尾の句読点は許容し正規化、`pass_punct` は後段の violations が数える) 。
  それ以外は発話。語数は切らない。`info.remain_count` = 残りターン数、`info.remain_skip` = 99。
- VOTE (aiwolf: day ≥ 1、domain: round 3 のみ): 生存席全員に送る。応答 strip、aiwolf は生存者名 (自分含む可)、domain は選択肢ラベル
  (大文字小文字無視、"A"/"A."/"Option A"/"Candidate A" も受理)。不正は `valid:false`, target 空。集計は `tally()`。
  aiwolf: 処刑 → `action` 行 (`action: execute`, agent "", target 名, text 名, extra role, tie)。domain: `result` 行は FINISH 時。
  aiwolf の DAILY_INITIALIZE (day ≥ 2) と FINISH には前日の有効票を `info.vote_list` (席順) に入れる。
- ACTION: aiwolf `DIVINE` (SEER 生存時、毎夜)、`ATTACK` (WEREWOLF、day ≥ 1、処刑後生存者から)。domain `INVESTIGATE` (round 1 の後、全員、dynamic のみ。
  fixed は要求を送らず `fixed_assignment` を割り当て、action 行に `parse: "fixed"`)。
  INVESTIGATE 応答: 行ごとに strip、`- `/数字./引用符を剥がし、タイトルと大文字小文字無視で照合。先頭2件の一致を採用、重複は1件に。
  0件/1件なら `parse: fail/partial`。cards は card_id のリスト。
- DAILY_FINISH: その席にまだ送っていない差分を載せる。FINISH: 全席に送り、勝者/採択を `info` に入れる
  (aiwolf: 標準の `status_map`/`role_map` 全公開; domain: `info.options` と採択ラベルを `executed_agent` には入れず、`info` に `adopted` キーを足してよい)。
- status 行: 各ラウンド開始時と FINISH 直前に全席分。aiwolf は Day 0 から。
- aiwolf 勝敗: 人狼死亡 → VILLAGE。人狼数 ≥ 人間数 (生存) → WEREWOLF。`max_day` 超過 (Day 3 の夜が終わっても未決着) → `NONE` ではなく、
  **Day 3 終了時点で決着していなければ `winner: NONE`, reason "max_day"**。切断・タイムアウトも `NONE` (reason に書く)。
- domain 終局: Round 3 の VOTE 後。`result` 行 text = 採択ラベル、extra `{adopted, tally, tie}`。
- タイムアウト: `--timeout` 秒 (既定 600)。TALK/VOTE/ACTION のタイムアウトは `forced` Skip / 無効票 / 行動なし として続行。接続断は対局中止。
- 終局 (finalize): header → raw/agent.*.jsonl のマージ → `violations` レコード (`find_violations(rows, ctx)` +
  `find_truncations(マージ済み llm_call)`) の順で jsonl に書く。
- CLI: `python -m server --setup <setup_id|path> --port 10000 --log-dir log [--timeout 600] [--model-tag scripted]
  [--model <フルネーム>] [--info-mode dynamic|fixed]`。`--model` は header の `model` (既定は model_tag)。
  終了コード 0 = 正常終局 (NONE 含む)、1 = 中止。標準出力に game_id と結果を1行。

##### 4. エージェントの組み立て (agent/base)

- 1 席 = 1 プロセスでも 1 スレッドでもよいが、**席ごとに独立した会話履歴**。
- system = role (`common/prompts/role.jinja`, method=multi: "You are <name>, one of the participants ...") + 空行 + setting + 空行 + structure + 空行 + schedule + 空行 + action + 空行 + identity (すべて `shared_block` / `role_block`)。
- 2026-10-27 (DESIGN §7.4): 履歴は積まない。`common.transcript.SeatTranscript` に席ビューを保持し、毎回 `[system, user]` を組み直す。
  通知 (INITIALIZE / DAILY_INITIALIZE / DAILY_FINISH / FINISH) は席ビューを更新するだけで、サーバへ静的 "Acknowledged." を返す (LLM は呼ばない。jsonl には書かない)。
  TALK の user = 席ビュー + "\n- **<name>**:"。VOTE / ACTION の user = 要求文 + 候補 + 空行 + 席ビュー + "\n### Vote\n- <name> ->" / "\n### Action\n- divine: <name> ->"。
  (以下の payload の記述は旧 chat 形式のもの。席ビューでは同じ情報が台本の行として入る。)
  payload: aiwolf DAILY_INITIALIZE = 前夜の結果 (day ≥ 2: "X was executed." / "No one was executed."、"Y was attacked." /
  "No one was attacked last night." (day 1 の朝は夜 0 に処刑も襲撃もないので何も出さない。DESIGN §4.7) / 前日の票 "Votes: A -> B, C -> D, ..." (`info.vote_list`、席順) /
  "Divine result: Z is HUMAN|WEREWOLF." 自席のみ) + 差分発話があれば先に "Name: text" 行。
  domain r=2 = "What you looked into:\n- title: text" (title が空なら "- text")、r=3 = "The candidates|options are:\n- A: name. summary"。
  DAILY_FINISH = 差分発話のみ。
- TALK: `talk_request.jinja` (差分 + position + output_rules)。VOTE: `vote_request.jinja` (差分 + vote_request_sentence + Candidates)。
  ACTION: `action_request.jinja` (差分 + action_request_sentences[request] + 候補リスト: DIVINE/ATTACK は生存他者名、INVESTIGATE はタイトル)。
- 応答は**生のまま** (strip せず) サーバへ返す (サーバが strip・正規化して `raw` を持つので `raw_differs` / `pass_punct` が
  multi でも意味を持つ)。自席の履歴には strip した形を積む。LLM エラー時は TALK → `ForceSkip`、VOTE/ACTION → 空文字。
- jsonl: 席ごとに `<log_dir>/<domain>/multi/<game_id>/raw/agent.<seat>.jsonl` に `llm_call` を追記
  (`seq (席内カウンタ), seat, request, round, turn, ts (UTC), messages, response, usage, finish_reason, error, truncated, latency_ms`)。
  サーバは FINISH 後に raw/agent.*.jsonl を `<game_id>.jsonl` へマージ: (round, 要求の段階 TALK<VOTE<DIVINE/INVESTIGATE<ATTACK,
  turn, 発言順位/席, ts) で時系列に並べ、`seq` を 0..n-1 に付け直し、席内カウンタは `seat_seq` に残す。game_id は INITIALIZE の `info.game_id` (`<setup>__<条件札>__<model_tag>__<ts>`)。
- LLM: `openai` SDK、`config/models.yml` の endpoint/model/temperature/max_tokens (multi_talk / multi_vote / multi_action)。
- CLI: `python -m agent --url ws://127.0.0.1:10000 (--seat 3 | --seats all) --setup <id> --log-dir log [--model default]
  [--reveal] [--writer] [--scenario auto|PATH] [--temperature T] [--top-p P] [--top-k K]`。
  `scripts/run_multi.py --setup <id> [--port] [--model] [--reveal] [--writer] [--scenario auto]` がサーバ + エージェントを起動して終局まで待つ
  (`--writer` / `--stepped` は 1 プロセス `--seats all`、それ以外は 5 プロセス)。サーバには `--condition` (札) と `--scenario` を渡す。ログは `log/<domain>/<札 (plan 抜き)>/`。
  `--stepped` (single-batch-stepped): messages = single-batch の [system, user] + assistant (書き手ビュー + 札)、`OpenAILLM.complete_continuation(messages, prefix, ...)` が vLLM `/tokenize` で [system, user] の生成プロンプトのトークン列と prefix のトークン列を取り、連結して `/v1/completions` に渡す (chat template の `continue_final_message` は Gemma 4 の空の思考チャネルを落とすので使わない)。TALK の停止列は共通、票・行動は `\n`。FakeLLM は assistant の最終行の札から返答を作る。
  筋書きの種類は `--plan-granularity process|outcome|outline|turn` (既定 process; process 以外は `--reveal` が要る)。
- 2026-10-28: setup の `option_perm` で選択肢の表示順を並べ替え (`ctx.options()` が A, B, … と付け直す)。サーバの VOTE / INVESTIGATE は発話順。header に `option_perm`、`vllm_version`、`hf_revision`、`chat_template_sha1`、`config_sha1`、`model_root` (common/llm_meta.py)。
- 2026-10-28 (DESIGN §13): system は `common.render.system_prompt` (role + 共通 4 ブロック + 自席 profile | `## Participants` ×5 + `## Hidden information` | + `## Plan`)。
  writer モードは `make_game_agents` で 5 席が `SeatTranscript(ctx, None)` と lock を共有。票は `match_candidate` で候補に一致した場合だけ暫定行にする (不一致なら行なし = ログと同じ)。
  サーバは VOTE / INVESTIGATE を席順に逐次問い合わせ、夜の DIVINE / ATTACK パケットに `executed_agent` を載せる。FINISH で最終期間の票・処刑・採択を書き手ビューへ (`on_finish`)。

##### 5. 単体 (single)

- system = `common.render.system_prompt(env, ctx, "single", scenario=...)` (role (method=single: "You are the writer ...") / setting / structure / schedule / action / `## Participants` identities×5 / `## Hidden information` (議論ドメイン, `common/prompts/hidden.jinja`) / `## Plan`) + `user.jinja` (request sentence / format_spec)。マルチと同じ system/user 分割と同じ並び (役割文 → ルール・進行 → 人物) (監査 A3)。
  format_spec は `format_aiwolf.jinja` または `format_discussion.jinja`。
- 1 回の呼び出し (max_tokens single_full)。原本を `raw/transcript.md`、プロンプトを `raw/prompt.json` に保存。
  `llm_call` には multi と同じく `model` (フルネーム) と `ts` を入れる。
- 変換: `common/convert/single_markdown.py: convert(markdown, ctx, game_id) -> (rows, violations, outcome)`。
  投票集計・処刑・採択・勝敗は票と行動から `tally()` で再計算し、書き手の値との不一致は `tally_mismatch`。
  同票で書き手の値が最多得票候補のときは書き手の値で再生し `tie_choice_differs` (DESIGN §8)。
- `violations` レコードは変換器の構造違反 + `find_violations(rows)` + `find_truncations` を `merge_violations` で
  1 つにまとめたもの。
- CLI: `python -m single --setup <id> --log-dir log [--model default] [--dry-run] [--fake] [--info-mode M] [--scenario auto|PATH] [--temperature T] [--top-p P] [--top-k K]`
  (dry-run はプロンプトだけ書く。どのモードでも `check_dynamic_ready()` を通る)。
  `scripts/run_single.py` は同じものの薄いラッパ。条件札は `single-batch` / `single-batch-<plan>`; header に `pipeline: batch`、`condition`、`axes`、`scenario`; violations に `scenario_deviation`。
- 筋書きの生成: `scripts/gen_scenarios.py --setups a,b | --domain d | --all [--attempts 4] [--force] [--dry-run] [--fake] [--out-dir DIR]` → `scenarios/<domain>/<setup_id>.json` (+ `.attempts.json`)。
- `config/models.yml`: `temperature` / `top_p` / `top_k` (null = サーバ既定)、`timeout_s: {multi, single}`、`gemma_default` エントリ (1.0 / 0.95 / 64)。

##### 6. 違反会計 (common/violations.py)

- 入力: `.log` の rows + ctx。出力: `[{seq, code, detail}]`。両方式共通コード (DESIGN §8)。
  `early_reveal`: domain で round < 3 の talk に選択肢の name (大文字小文字無視、語境界) が出たら記録。カード本文の言及は round 1 の talk に
  カード text の 6 語以上の連続一致があれば記録 (粗い指標で可)。
  `early_reveal_partial`: 同じ条件で選択肢 name の語 1 つ (5 文字以上、`PARTIAL_STOPWORDS` 以外) の単語一致。全名一致した選択肢は重ねて数えない。
  `trailing_over`: 本文の末尾が `Over` / `Skip` (`.`/`!` 可、大文字小文字無視) で終わる talk。記録のみ。
- 復元 (name_label 除去など) は violations では行わず、分析時に行う。記録のみ。

