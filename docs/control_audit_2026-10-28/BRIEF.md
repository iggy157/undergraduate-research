# 検閲 (audit 2) の共通ブリーフ — 2026-10-28

対象リポジトリ: /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research (git 管理なし)。変更は加えないこと (読むだけ)。
実行結果: log/_pilot5/ (パイロット 5、gemma-4-31B-it、greedy、3 ドメイン × 3 setup × 5 条件 + 筋書き条件)。
筋書き: scenarios/<domain>/<setup_id>.json (+ .attempts.json)。
設計文書: docs/DESIGN.md (§13 条件、§14 hidden states)、docs/IMPLEMENTATION_NOTES.md、docs/paper_draft.md (v3: 論文の狙い・条件・評価・限界)。
前回の検閲 (2026-10-27) と結果: ../undergraduate_research_archive/2026-10-28_pre_pilot6/docs_control_audit_2026-10-27/00_SUMMARY.md (リポジトリ外に退避)。

研究の狙い (要約): 1 つの LLM が議論台本を一括生成する方式と、席ごとの LLM がサーバ経由で 1 行ずつ生成する方式の差を、
5 つの要因 (結末と構造の決め手 / プロンプトの目標と履歴の置き場所 / 1 つの文脈か席ごとの文脈か / 情報量 / 明示的な筋書き) に
分解して測る。条件札: single-batch / single-batch-stepped / single-online / multi-public / multi-private (+ -process 等)。
投稿先は ARR 経由のトップ会議 (ACL/EMNLP/NAACL) を想定。評価は本検閲の対象外 (未設計) だが、ログに評価に必要な情報が
揃っているかは対象。

判定の観点 (各報告で必ず答える):
1. 統制: 条件間で「設計した差以外」が混入していないか (プロンプトの文面、トークン列、サーバの手続き、記録)。
2. 正しさ: 実装が設計文書の記述どおりか。ログが実際の入出力を忠実に残しているか。
3. 査読耐性: トップ会議の査読者がこの部分に対して指摘しそうな点と、その深刻度 (Critical / Major / Minor)。
4. 再現性: 第三者が同じ結果を再現できる情報が残っているか。

報告の書式: Markdown。冒頭に「結論 (3 行以内)」、次に「発見した問題」を深刻度順の表 (項目 / 証拠 (ファイルと行、または log のパス) /
影響 / 修正案)、最後に「確認した範囲と確認していない範囲」。推測と確認済みを分けて書くこと。長さは 150 行以内。
出力先: /diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research/docs/control_audit_2026-10-28/<番号>_<名前>.md
(ディレクトリは作ってよい)。

便利なコマンド (リポジトリ直下で):
- .venv/bin/python scripts/verify_prompt_control.py --setups aiwolf_0001,candidate_selection_0001
- .venv/bin/python -m agent.base.dump --setup aiwolf_0001 --seat 3 [--reveal|--writer|--stepped]
- .venv/bin/python -m single --setup aiwolf_0001 --dry-run (プロンプトを表示)
- ログの読み方: log/_pilot5/<domain>/<condition>/<game_id>/<game_id>.log (CSV: seq,round,turn,type,agent,target,text,extra) と
  <game_id>.jsonl (header / llm_call (messages, response, tokens, prompt_token_ids) / violations)。raw/ に原本。
- 共通ログの行ビュー: from common.logwriter import read_log; from common.transcript import view_from_rows
