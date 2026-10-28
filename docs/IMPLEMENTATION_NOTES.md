# 実装契約 (server / agent / single / convert の共通ルール)

DESIGN.md (v0.4) が仕様。ここは実装者間の取り決め。`common/` は既に実装済みで、変更する場合はこのファイルと DESIGN.md も直す。

## 0. 環境

- `uv` プロジェクト。`.venv/bin/python` を使う (`export PATH="$HOME/.local/bin:$PATH"; uv run ...` でもよい)。
- import は `from common.protocol import ...` の形 (リポジトリ直下が sys.path。scripts/ からは `sys.path.insert(0, ROOT)`)。
- テストは `tests/` に pytest。LLM を呼ぶテストは書かない (台本エージェント・固定文字列で代替)。
- 外部 API は呼ばない。vLLM も起動しない (パイロットは人間が行う)。

## 1. 共通 API (実装済み)

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

## 2. game_id とログ置き場

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

## 3. サーバの進行 (server/base)

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

## 4. エージェントの組み立て (agent/base)

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

## 5. 単体 (single)

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

## 6. 違反会計 (common/violations.py)

- 入力: `.log` の rows + ctx。出力: `[{seq, code, detail}]`。両方式共通コード (DESIGN §8)。
  `early_reveal`: domain で round < 3 の talk に選択肢の name (大文字小文字無視、語境界) が出たら記録。カード本文の言及は round 1 の talk に
  カード text の 6 語以上の連続一致があれば記録 (粗い指標で可)。
  `early_reveal_partial`: 同じ条件で選択肢 name の語 1 つ (5 文字以上、`PARTIAL_STOPWORDS` 以外) の単語一致。全名一致した選択肢は重ねて数えない。
  `trailing_over`: 本文の末尾が `Over` / `Skip` (`.`/`!` 可、大文字小文字無視) で終わる talk。記録のみ。
- 復元 (name_label 除去など) は violations では行わず、分析時に行う。記録のみ。
