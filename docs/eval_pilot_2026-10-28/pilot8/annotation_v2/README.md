# パイロット 8 の発話単位注釈 v2 (63 局、4 注釈者)

- games/: 注釈用の描画 (`scripts/render_annotation.py --stable-names`)。games.json に条件・語数・位置。
- ANNOTATION_INSTRUCTIONS.md: 指示文 v2 (content 0/1/2, resp + resp_to, resp_type, rebut, padded)。
- out/: Llama 3.3 70B (llama_NNN.json; bf16, TP=2, temperature 0, バッチ不変) と gpt-oss-120b (gptoss_NNN.json; MXFP4, temperature 0, バッチ不変なし: MoE カーネルが非対応) の出力。raw/ は返答の原文。
- out_claude/: Claude Opus / Sonnet のサブエージェント注釈 (設計確認用。論文には載せない)。
- summary_4raters.md: 4 注釈者の集計 (`scripts/annotation_summary.py --by-position`)、qa_summary_4raters.md: 質問への返答と位置別 content (`scripts/annotation_qa.py`)。
- summary_claude_only.md / qa_summary_claude_only.md: Claude 系 2 者だけの集計 (先に出した版)。
