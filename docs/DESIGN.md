# 設計文書: 単体エージェント vs マルチエージェントによる議論生成 (3ドメイン)

作成 2026-10-26。**v0.4** (v0.2 = 独立レビュー2本の反映。v0.3 = §10 の最終未決を確定。v0.4 = 2026-10-27、3ドメインを同一の Python サーバ基盤に載せる構成に変更)。
v0.1 からの主な変更: 情報公開スケジュールの共通化 (§5, §6.2)、違反会計の両方式化 (§8)、同票規則の決定論化 (§6.1)、
Skip 改造の撤回 (§4.5)、単体 Markdown の節順修正 (§7.2)、指標の分母定義 (§11)。
v0.3: panel の選択肢は 4 のまま (§10)、カード書き直しは表現調整のみ (§9-9)。
v0.4: ディレクトリを common / server / agent / single に再編 (§2)、aiwolf の Go 改造をやめて 3 ドメインとも Python サーバ (§4.5)、ドメイン名を `aiwolf` / `candidate_selection` / `shared_living` に変更、要求名を aiwolf-nlp-common の語彙に統一 (§5)。
v0.4.1 (2026-10-27、実装レビューとパイロット監査の反映): 投票内訳と襲撃なしの通知 (§5)、生応答をワイヤに流す (§4.5-5)、`trailing_over` / `early_reveal_partial` / `tie_choice_differs` (§8)、jsonl の時系列 seq と setup_sha1 (§3.2)、`--info-mode` 上書き。実装状況は §12。

---

## 0. 目的と原則

- **比較するもの**: 単体 (single: 1つの LLM が議論全文を一括生成) と マルチ (multi: 席ごとに独立した LLM が1発話ずつ生成)。
- **統制**: 両方式の差を「生成単位」だけに絞る。ルール文・ペルソナ・役職・議題・発話順・語数・Over/Skip の説明・情報公開スケジュールは、すべて**同じ設定ファイルと同じ Jinja ブロック**から展開し、文言をバイト一致させる。
- **据え置く差 (研究テーマ)**: 単体は全席の非公開情報を一度に見る (全知性)。投票・調査などの行動も単体は一括で書く。
- **ドメイン**: `aiwolf` / `candidate_selection` (移植元の panel) / `shared_living` (移植元の living) の3つ。本文では短く panel / living とも書く。candidate_selection と shared_living は同じ進行、aiwolf だけ異なる進行 (意図した設計)。ドメインは比較軸ではなく**層別因子**。
- **持ち込まないもの**: 失敗モードの指示文、投票宣言ナッジ、発話カウンタの使用数・残数、シナリオ注入、factors、cache、tactics、mixed、コスト台帳、サーバ側の文字数打ち切り。
- **モデル**: ローカル vLLM の OpenAI 互換エンドポイント。思考トークンを出力に含むモデルは使わない。

## 1. 用語

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

## 2. ディレクトリ構成

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

## 3. 共通ログスキーマ

### 3.1 `<game_id>.log` (CSV、固定8列、標準クォート)

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

### 3.2 `<game_id>.jsonl`

- `{"kind":"header", ...}`: game_id, setup_id, domain, method, model (models.yml のフルネーム), model_tag, info_mode, setup_path, setup_sha1 (setup JSON のバイト列の sha1), started_at / finished_at (**tz 付き UTC ISO**、両方式), participants (seat, name, role_slot, persona 4項目, private seed), card_pool (aiwolf は `[]`), **n_options**, **n_unique_cards** (dynamic で実際に引かれた一意カード数。aiwolf は 0), outcome, config ハッシュ。
- `{"kind":"llm_call", ...}`: seq (**対局内の時系列通し番号 0..n-1**。multi は server がマージ時に付け直し、agent 側の席内カウンタは `seat_seq`), seat (single は `writer`), request (§1 の要求名。単体は `FULL`), round, turn, ts (UTC), model, messages, response (**生応答**), usage, **finish_reason**, **error**, truncated (= finish_reason が length), latency_ms。
- `{"kind":"violations","items":[...]}`: §8 の違反 (**両方式とも**、1 レコード)。multi は server が終局時に `find_violations` + `find_truncations` で書く。single は変換器の構造違反と共通コードを合わせて 1 レコードに書く。`scripts/convert_logs.py` は共通コードだけを再計算し、構造違反 (行番号付き) と `llm_error` 等は保持する。

### 3.3 書き出しと変換器 `common/convert/`

| 方式 | 書き手 | 備考 |
|---|---|---|
| multi (3ドメイン) | **server/base の logwriter が共通形式を直接書く** | 変換なし。無効票・強制 Skip・空応答は server が extra に記録する。jsonl の llm_call は agent 側が送信メッセージと生応答を書き、server が game_id で突合する (agent は `<log_dir>/<domain>/multi/<game_id>/raw/agent.<seat>.jsonl` を書き、終局後に server がマージ) |
| single (3ドメイン) | Markdown 原本 → `single_markdown.py` | 厳密パース (§8)。採択・処刑・勝者は**票から再計算**して書き手の値と照合 |
| Go サーバ (互換テスト) | サーバ CSV + JSON → `aiwolf_go.py` | `scripts/compat_aiwolf_go.py` が同じ台本エージェントを Go サーバと Python サーバにつなぎ、共通形式で突合する。CSV の talk 行はカンマ非エスケープなので type 別 maxsplit |
| 移植元 result.json | `legacy_resultjson.py` | テスト専用 |

## 4. 設定ファイル

### 4.1 `data/personas.yml`

24人。項目は本家 aiwolf-nlp-server の custom_profile と同じ **name / age / gender / personality** のみ。出典は移植元の英語サーバ config。persona_id = name。職業は持たない。panel の context は「各部門の審査員」風だが肩書は与えない。**話者間の事実整合性は従属変数に使わない** (§11)。

### 4.2 `data/<domain>/roles.yml`

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

### 4.3 `data/<domain>/instances.json` (panel / living)

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

### 4.4 `setups/<domain>/<setup_id>.json`

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

### 4.5 サーバ (`server/`、3ドメイン共通の Python 実装)

Go 製 aiwolf-nlp-server は改造せず (このマシンの Go は 1.22 で、ビルドにも 1.24 が要る)、`server/base` に進行ループを Python で書き、3ドメインを同じ基盤に載せる。5人村に必要な人狼ロジック (役職・固定順 Talk・投票・処刑・占い・襲撃・勝敗・max_day) は小さい。

1. **ワイヤ形式は aiwolf-nlp-common 0.7.0 と互換**。パケットは `{request, info, setting, talk_history, whisper_history}`。`info` は `game_id, day, agent, profile, status_map, role_map, divine_result, executed_agent, attacked_agent, vote_list, remain_count, remain_skip` を同名で持ち、ドメイン拡張として `problem` (INITIALIZE)、`card_titles` (INITIALIZE)、`investigate_result` (DAILY_INITIALIZE、本人のみ)、`options` (DAILY_INITIALIZE、Round 3) を加える。aiwolf-nlp-common の `Info.from_dict` は未知キーを捨てるので、既存エージェントもそのまま接続できる。
2. 要求列: `NAME` → `INITIALIZE` → 各ラウンド `DAILY_INITIALIZE` → `TALK`×最大4 → (`VOTE`) → (`DIVINE` / `ATTACK` / `INVESTIGATE`) → `DAILY_FINISH` → `FINISH`。`day` 列はドメインを問わずラウンド番号 (aiwolf は 0 始まり、他は 1 始まり)。
3. 席固定: `AIWOLF_SETUP_FILE` (環境変数) または `--setup` で setup を読み、接続名 (`NAME` 応答) を `seat1..seat5` と照合して席を決める。配役・ペルソナ・発話順は setup の値をそのまま使い、乱数は使わない。
4. Talk: 固定順 × 4 ターン。Skip はターンを消費し回数無制限 (`max_skip` 相当なし)。Over でそのラウンド離脱。空応答・応答不能 (タイムアウト・切断以外のエラー) は `Over` (`empty:true`) / `Skip` (`forced:true`) として記録。切断は対局中止 (`winner: NONE`)。
5. **発話の正規化**: 前後空白の除去のみ。agent は LLM の生応答をそのままワイヤに流し、server が strip して `raw` と比較する。発話末尾に埋め込まれた "Over." は剥がさず talk として記録する (移植元は剥がしていた。`trailing_over` で数える、§8)。`@名前` の再構成 (Go の `processText`) は**行わない**。語数の切り捨ても行わない (word_cap はプロンプト上の指示であり、超過は §8 の `over_cap` として記録)。`raw_differs` は端の空白 (strip) では true にならず (2026-10-28: 続き書きの先頭スペースを差としないため)、正規化で本文が変わった場合と空→Over の場合に true。
6. 投票: 無効票 (不正名・死者・自分以外が禁止のとき自分・パース不能) は不算入で `valid:false`。再投票なし。同票は §6.1 の決定論規則。
7. aiwolf 固有: `allow_self_vote: true`、`max_day: 3`、襲撃は Day 1 以降、襲撃対象が不正なら不成立 (`attack` 行の `no_target:true`)、勝敗は村 = 人狼が死亡、人狼 = 人狼数 ≥ 人間数。
8. ログは `common/logwriter` で共通形式 (§3) を直接書く。Go 版との互換は `scripts/compat_aiwolf_go.py` で確認する (同じ台本エージェント、`@` を含む発話は空白を正規化して比較)。

### 4.6 発話の正規化 (両方式共通、2026-10-27)

`common/normalize.py` の `normalize_talk` を server (multi) と単体変換器の両方が呼ぶ。議論の質と無関係な表記ゆれはここで吸収し、
**必ず記録する** (行の extra.norm と violations の `kind: normalized`)。

- 前後の空白・句読点: 除去 (発話内の改行は両方式とも保持。複数行の発話は許可。単体の台本では次の箇条書き/見出しまでの行を直前の発話に連結)
- Skip/Over の表記ゆれ ("Over." / "skip" / '"Over"'): トークンに正規化 (`pass_punct`)
- 発話全体を囲む引用符や `**`: 外す (`format_noise` kind=wrap)
- 先頭の自分の名前ラベル ("Kenji: …", "**Kenji**: …"): 外す (`name_label` self=true)。他人の名前ラベルはそのまま残し、`speak_for_others` (本物の違反) として後で判定
- 本文の末尾に付いた正確なトークン ("… see you tomorrow. Over."): 外し (`trailing_over`)、Over なら次ターン以降その席は離脱 (pass 行 `trailing:true` を直後に書く。他席には "Name: text" と "Name: Over" の 2 行として見える)。大文字小文字を区別するので "turn it over." は文として扱う

違反 (`kind: violation`) として残るのは、over_cap / 他人の名前ラベル (name_label, speak_for_others) / multi_utt / 残りの format_noise (ト書き・見出し等) / early_reveal(_partial) / truncated。
`scripts/convert_logs.py` は `#violation` と `#normalized` の列で両者を分けて集計する。

### 4.7 通知の原則 (multi、2026-10-27)

進行表で「あるはず」のものだけを報告し、あるはずなのに無いときは「ありませんでした」を出す。文言は rules.yml `notice_sentences`。
- 1 日目の朝: 処刑・襲撃・投票内訳は出さない (夜 0 にはない)。占い師にだけ占い結果 (失敗なら "No divination result last night.")。
- 2 日目以降の朝: "X was executed." / "No one was executed."、"Y was attacked." / "No one was attacked last night."、"Votes: …"、占い師には占い結果。
- discussion の Round 2 開始: 調査結果 ("What you looked into:") か、何も調べられなかった席には "Nothing was looked into; there are no findings."。Round 3 開始: 選択肢。
- 占い師が死亡している場合は報告先がないので何も出ない (全員に「占いなし」を出すと占い師の死亡が漏れる)。

## 5. ラウンド構造・要求列・情報公開スケジュール

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

## 6. ルール変数と共通ブロック

### 6.1 `data/<domain>/rules.yml`

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

### 6.2 共通ブロック (英語文言案。両方式でバイト一致させる部分)

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

### 6.3 文言の統制

- `scripts/verify_prompt_control.py` が、同一 setup_id について single と multi の全プロンプトを dry-run レンダし、共通ブロックの展開結果が**バイト一致**することを検証する。position は両方の文字列を並記して記録する。
- 語数・Over/Skip・通知・スケジュールの文言は rules.yml からしか書かない。テンプレートに数値や制約文をハードコードしない。
- Skip を抑制する文 (「新しいことがなければ Skip」等) は入れない (ナッジ禁止と整合)。

## 7. プロンプト組み立て

### 7.1 マルチ (席ごとに独立した会話履歴)

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

### 7.4 台本文法と席ビュー (2026-10-27。大会出場と蒸留を見据えた決定)

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

### 7.2 単体 (1回の呼び出し)

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

### 7.3 共通 / 方式固有の対応表

| ブロック | single | multi | 判定 |
|---|---|---|---|
| identity / setting / structure / schedule / action / output_rules | 同文 | 同文 | **共通 (バイト一致を検証)** |
| position | 見出し `#### Turn t of 4` と `## Round r` | TALK 要求の1行 | 情報等価 (同じ文字列を含む) |
| notice (ROUND_START / END) | なし | あり | 方式固有 |
| 執筆者枠づけ / Markdown 構造指定 / hidden.jinja | あり | なし | 方式固有 |
| 非公開情報の見え方 | 全席分 | 自席分 | 方式固有 (研究テーマ) |
| 投票・行動の決定 | 全席分を一括で書く | 席ごとに要求 | 方式固有 (研究テーマ) |

## 8. 違反会計 (両方式共通) とパース仕様

品質指標は**復元後の発話**で計算し、違反率は別表で報告する。復元不能で捨てた行は感度分析 (含む / 含まない) を付ける。

**両方式共通の違反コード**: `over_cap` (語数超過、記録のみ)、`name_label` (発話頭の名前ラベル、除去して復元)、`multi_utt` (1 応答に複数発話、先頭のみ採用)、`pass_punct` (`Over.` 等、正規化)、`trailing_over` (発話本文の末尾に `Over` / `Skip` が付く、記録のみ。本文は削らない)、`speak_for_others` (他者の発話を含む、記録のみ)、`format_noise` (見出し・ト書き、除去)、`early_reveal` (スケジュール前の選択肢名 (全名一致)・カード内容の言及、記録のみ)、`early_reveal_partial` (選択肢名の 5 文字以上の語 1 つ (ストップワード除く) の単語一致、記録のみ、粗い指標)、`truncated` (finish_reason=length)。

**単体のみ** (構造違反): `name_case` (復元)、`unknown_name` (捨てる)、`dup_turn` (同一ターン重複、先頭採用)、`talk_after_over` (Over 後の発話、捨てる)、`over_repeat` (Over の再記載、正規化)、`pass_after_over` (Over 後の `Skip` 行。書き手が残りターンを埋める癖で、捨てて正規化として記録)、`missing_turn` (Over していないのに行がない、記録)、`dead_actor` (死者の発話・投票、捨てる)、`order` (ターン内順序違い、復元)、`extra_round` (`## Day 4` 以降、捨てる)、`bad_card` (タイトル不一致、その席はカードなし)、`vote_count` (票数不足)、`tally_mismatch` (票から再計算した採択・処刑と書き手の値の不一致 (書き手の値が最多得票の候補でない)、再計算値で上書き)、`tie_choice_differs` (同票で、書き手の処刑・採択が最多得票の候補ではあるが共通タイブレーク規則の選択と異なる。**書き手の値を保って再生**し、execute / result 行に `tie:true` と `rule_choice:<規則の選択>` を付ける。規則で上書きすると以降の transcript が `dead_actor` / `missing_turn` の連鎖になるため)、`divine_mismatch` (占い結果と真役職の不一致、真値で上書き)。

**パース文法** (単体): 見出しは `## <Period> <int>`、`### Talk|Vote|Action`、`#### Turn <int> of 4`。発話は `- **<Name>**: <text>`。Vote は `- <Name> -> <Target>`、`- execution: <Name>`、`- adopted: <Label>`。Action は `- divine: <Name> -> <Name> (human|werewolf)`、`- attack: <Name> -> <Name>`、`- investigate: <Name> -> <title>; <title>`。Result は `- winner: village|werewolves` / `- adopted: <Label>`。

## 9. 実装の順序

1. 雛形: `pyproject.toml`、`data/personas.yml`、3ドメインの `roles.yml` / `rules.yml`、2ドメインの `instances.json` (カード本文は移植元のまま、タイトルは §9-9 で付与)、`config/`。
2. `common/`: protocol、schema、logwriter、setup、tiebreak、render、violations、convert (single_markdown / aiwolf_go / legacy_resultjson)。テスト: 移植元の aiwolf CSV/JSON、result.json、単体 Markdown の往復。
3. `scripts/make_setups.py` と設定ファイル生成。
4. `common/prompts` の共通ブロックと両方式の組み立て、`verify_prompt_control.py`。
5. `server/base` + 3ドメイン。台本エージェント (LLM なし) で進行とログを検証。`compat_aiwolf_go.py` で Go サーバと突合。
6. `agent/base` + 3ドメイン (vLLM)。
7. `single/` (3ドメイン)。
8. パイロット (各ドメイン single / multi 2 局ずつ、dynamic と fixed の両方) → 文言・パース仕様の修正。
9. カードの書き直し (別作業、承認後)。**範囲は表現の調整のみ**: 本文を第三者視点に改め、タイトルを付与する。議題・選択肢・困りごとの数と内容、点数行列は変えない (panel の選択肢 4 もそのまま)。

## 10. 未決事項

なし。

v0.2 の未決 1 点 (panel の選択肢 4 を living の 3 に揃えるか) は **4 のまま残す** で確定 (2026-10-26、ユーザ判断)。理由: 議題は選択肢込みで設計されており、候補削除は内容の再設計になる。ドメインは層別因子なので、ヘッダの `n_options` で層別し、投票系指標 (過半数到達率・票の割れ方) のドメイン間比較は主張しない。カード書き直しも表現の調整に留める (§9-9)。

v0.1 の他の 6 点は次で確定: 文言は §6.2 案 (パイロット後に見直し) / カード 2 枚・プール 10 枚 / position は情報等価 (1 始まり) / 天井はマルチ発話 1024・投票行動 64・単体 16384、`models.yml` で方式別、打ち切りは除外数として報告、vLLM の `max_model_len` ≥ プロンプト + 天井を確認 / N=30、10 の倍数 / aiwolf は `max_day: 3` を両方式のルール文に書き、整合性は §8 で検証。

## 11. 指標の前提 (分析時の規則)

- 情報共有の分母は **(席, カード) 対**。dynamic では `n_unique_cards` を共変量にする。パイロットで fixed も回し、一意数の低下を数値で把握する。
- 統計の単位は setup (single と multi の対応のある比較)。インスタンスは変量効果。ドメインは層。
- 話者間の事実整合性 (肩書や設定の矛盾) は従属変数にしない (ペルソナに職業がないため)。
- 形式違反率と議論の質は別の表で報告する。

## 12. 実装状況 (2026-10-27)

- 実装済み: §2 の全ディレクトリ。テスト 179 本。`verify_prompt_control.py --all` で 90 setup の共通ブロックがバイト一致、単体プロンプトにルール文の言い換えがないことも検証。
- パイロット: gemma-4-31B-it (vLLM) で 3ドメイン × single / multi を各 1 局。candidate_selection と shared_living は **fixed** モード (カードのタイトルが未作成のため dynamic は未実行、§9-9 待ち)。
- Go サーバとの互換テスト (`scripts/compat_aiwolf_go.py`) は同じ台本エージェントで実行し、想定内の差 (空応答後の扱い、`Over.` の扱い、日次シャッフル) 以外の差なし。
- 2026-10-27: §9-9 完了。200 枚にタイトルを付与、78 枚の本文を第三者視点に調整 (一人称の置換のみ、事実・数値・bearing は不変)。元の本文は instances.json の `text_source` に保持。下書き・検査記録・検査スクリプトは ../undergraduate_research_archive/2026-10-28_pre_pilot6/docs_control_audit_2026-10-27/card_rewrite_drafts/、反映は scripts/apply_card_rewrite.py。dynamic モードの dry-run が通る (check_dynamic_ready OK)。
- 2026-10-27 パイロット 3 (台本文法 §7.4、dynamic、gemma-4-31b、3 ドメイン × single/multi): 6 局とも正常終局。multi の全 TALK の user が ログ由来の席ビューとバイト一致 (167/167)。token id + logprob、sampling、model_info を記録。stop 境界が効き複数行の逸脱なし。末尾 "Over." は 5 件 (cs multi) で、正規化してラウンド離脱扱い。ログは log/ (前回は log/_pilot2)。
- 未実施: N=30 の本実験 (temperature 0.7) とプローブ用の greedy 対局。
- 2026-10-28 パイロット 4 (single, greedy, 3 ドメイン × 5 setup, log/_single_t0): 15/15 終局、繰り返し崩壊なし。議論 10 局中 7 局で選択肢内容語の先出し (書き手の全知性の現れ、記録)。全員 Over 後の埋め行は `pass_after_over` / `over_repeat` (正規化)。
- 2026-10-28 実験条件の実装 (§13): M1 (`--reveal`)、S-online (`--writer`)、筋書き (`scenarios/`, `--scenario`)、sampling の記録 (top_p / top_k、方式別 timeout)、`mentions` を素の名前で再定義 (発話者自身を除く)、`verify_prompt_control.py` が全条件の system を検証 (`--info-mode fixed` も)。テスト 196 本。未実施: 4 条件のパイロット (scratchpad pilot5)、筋書きの生成 (GPU)、評価、hidden states。

## 13. 実験条件 (2026-10-28)

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

## 14. hidden states の取得 (2026-10-28)

- `scripts/extract_hidden.py` (vllm-server の venv: transformers 5.8 / torch)。記録済みの `prompt_token_ids` (vLLM `/tokenize` を生成時に呼んで保存) と生成トークン id から列を組み直すので、chat template の再現は不要 (vLLM の描画は HF テンプレートと system 末尾のスペース 1 トークン分ずれる)。single-batch は prompt + 応答トークン (teacher forcing)、single-batch-stepped は prompt + 書きかけ (そのまま `/v1/completions` に渡した列)、online / multi は prompt。
- 位置: `label` = 札 `- **X**:` の最終トークン (`**:`; batch と stepped では次の行の最初のトークンを予測する位置)、`prompt` = 生成プロンプト末尾 (`<channel|>`: Gemma 4 は thinking 無効でも空の思考チャネルが生成プロンプトに付く)。出力は `<game_id>.npz` (`h` [位置, 層, 5376], float16, 既定は 4 層おき + 最終層) と `.index.json`。
- 検査 (aiwolf_0001, 5 条件): prompt_token_ids の長さ = usage.prompt_tokens が全呼び出しで一致。**恒等性**: single-batch と single-batch-stepped の札位置の表現は、台本が同一な区間で全層 cos ≥ 0.9998 (bf16 の誤差)、分岐後は 0.85〜0.92 に低下。single-batch と single-online は同じ札トークンでも cos 0.6〜0.8 (プロンプトの目標と履歴の置き場所の差)。
- vLLM の greedy は決定的でない: single-batch と stepped は接頭辞のトークン列が同一でも、近接確率の反転 (logprob 差 0.1 未満) で数行以内に分岐する。サーバの正規化 (`Skip.` → `Skip`) と行の順序 (調査行は席順) でも分岐する。
- 2026-10-28 パイロット 5 の発見 (筋書き): 最初の process 筋書き 9 本は、公開の筋と席の筋に選択肢名・ラベル (「Option A emerges as the most stable choice」「supports the Study Commons」) や人狼の被疑者名が入っており、process 条件で先出し違反が増えた (candidate_selection_0003 の multi-private-process で 16 件)。これは「結末を含まない筋書き」の定義に反する。対処: `_validate_prose` を強化 (結末・選好の語、選択肢名・ラベル・議題素材に無い選択肢語、人狼では他の参加者名を公開の筋と席の筋で禁止; ターン行は対象外)、生成要求文も同じ規則に。9 本は再生成し、process 条件 18 局は回し直す。
- 2026-10-28 検閲 (docs/control_audit_2026-10-28/) への修正: (1) 選択肢ラベルの並べ替え: setup に `option_perm` (seed からの決定的な順列、既存 60 setup に移行追加)、`ctx.options()` は表示順に A, B, C … と付け直し `orig_label` を保持、header に `option_perm`。議論 42 局中 34 局で A が採択されたラベル順の偏りへの対処。(2) 名前照合が末尾の括弧 (`Shizue (werewolf)`) を許容 (stepped の占いが全て無効だった)。(3) サーバの投票・調査の問い合わせと行の順序を発話順に (batch の書き手の習慣に合わせ、stepped との分岐要因を減らす)。(4) `raw_differs` は端の空白を無視 (stepped の先頭スペース)。(5) header に vLLM 版・model_root・hf_revision・chat_template_sha1・config_sha1 (`common/llm_meta.py`)。(6) 筋書き生成の記録に messages・sampling・token id、空ターンの修復。(7) hidden states の index に `gen_point` (条件間比較はこの位置で行う: online / multi の札トークンは文末記号を予測する位置なので比較に使わない)。(8) 先出し検出の素材語に議題タイトルを追加。
- online → multi-public の段には、役割文と文脈の分割に加えて**他席の夜の行動・調査の可視性** (書き手ビューは全席の divine / attack / investigate 行を見る; multi-public の席ビューは自席分だけ) が含まれる。論文では「書き手 1 人の全知の文脈 vs 席ごとの文脈 (他席の動的な秘密は見えない)」として明記する。
- 2026-10-28 パイロット 6 (修正版、log/_pilot6、72 局 + 筋書き 9 本、`VLLM_BATCH_INVARIANT=1`、2 台): 72/72 終局。**single-batch の反復 2 回は 9/9 setup で全文一致** (バッチ不変モードで決定的)。stepped の占いは 3/3 有効。ビューのバイト一致 45/45 局、prompt_token_ids = usage.prompt_tokens 2730/2730。議論ドメインの採択ラベルは A/B/C/D に分散 (option_perm の効果)。process 条件の先出し違反は multi-private-process 合計 1 件 (第 1 ラウンドは 27 件)。batch と stepped: cs_0002 は全文一致、他 8 setup は 5〜26 行目で分岐。分岐の原因: (i) 同一接頭辞からの近接確率の反転 4 件 (logprob 差 ≤ 0.06、aiwolf_0003 は完全同値) — バッチ不変でも **prefill (stepped は接頭辞を再計算) と decode (batch は 1 トークンずつ) の数値経路が違う**ため。(ii) サーバの正規化 (`Skip.` → `Skip`) 1 件、(iii) 書き手の空行や全員 Over 後の構造をサーバが矯正 3 件。報告の形: 「反復は同一 (決定的)。batch と stepped の差は、近接確率の反転 (実装の数値解像度以下) とサーバの構造矯正に限られる」。


## 15. multi-*-stepped: 全文の生成目標を席ごとの生成に移植する条件 (2026-10-29)

- 条件札 `multi-private-stepped` / `multi-public-stepped` (`common.conditions`、`-<plan>` も可)。席ごとの 5 プロセス (`python -m agent --seat N --seat-stepped`、`scripts/run_multi.py --seat-stepped [--reveal]`)。
- 各席: system = その席の参加者プロンプト (multi-private / multi-public と同一)、user = single-batch の書き手への要求 (`single/prompts/user.jinja` + 出力形式、single-batch-stepped と同一)、assistant = 自席ビューの台本 + 自分の札 (`- **X**:`)。`/tokenize` + `/v1/completions` の続き書き (single-batch-stepped と同じ経路) で、停止列は次の台本要素。モデルは他席の行まで書き続けうるが、サーバが受け取るのは自席の 1 行だけ。票・夜の行動も同じく自席ビューの札 (`- X ->`) の続き書き。
- 目的: 密度・譲りの差が「全文を 1 回で書く生成目標」によるものか、「1 人が全員分を書く (文脈の非分割)」によるものかを分ける。multi-private との差が目標の効果、single-batch-stepped との差が分割 (+ 情報) の効果。hidden states の gen_point (札トークン) は single-batch-stepped と同じ位置。
- 記録: llm_call に `continuation`, `prompt_ids`, `prefix_ids` (stepped と同形)。`scripts/extract_hidden.py` は kind = stepped として扱う。

## 16. 議論例 (few-shot) の条件 (2026-10-30)

- 目的: 会話の前に議論例を与えると、生成目標を変えずに発話の長さ・密度・頭の中の長さの読み出しが変わるか。今日の結果 (履歴の文体が長さを決める) との対応を見る。
- 条件: single-batch と multi-online (multi-private) に、例を 3 本与える。短い例 = 同じモデルの single-batch の局、長い例 = 同じモデルの multi-online の局。どちらも同じドメインの別の設定から、設定名の順で最初の 3 本 (対象の設定自身は除く)。例なしは既存の本実行の局を使う。
- 入れ方 (common/examples.py、環境変数 UGR_EXAMPLES で有効化): manyshot-ablation の前置き文 (書式の注意の一文は除く) + 発話行だけの台本 3 本を、指示文の先頭に置く。single の書き手にも multi の各席にも同じ文面。manyshot-ablation の決まった返答と毎ターンの一言は入れない (案 A: 違いは例の有無だけ)。
- サーバ: 例で入力が伸びるので max-model-len を 32768 にした (本実行は 20480)。出力の上限は変えていない (single_full 16384)。温度 0 では上限に届かない限り出力は変わらない。
- ログ: log/fewshot/<model>__ex-<short|long>/ (局名の条件部分は single-batch / multi-private のまま、フォルダで区別)。例の文面は各通話の記録に指示文として残る。
