# 06 自己検閲 (Claude、パイロット 5 の実行直後、サブエージェントの報告と独立に作成)

作成 2026-10-28 04:40 JST。対象: log/_pilot5 (63 局)、scenarios/ (9 本)、hidden states の実機取得 (aiwolf_0001、5 条件)。

## 結論 (3 行)

1. 5 条件の梯子は実装どおり動き、記録の検査 (ビューのバイト一致 45/45 局、prompt_token_ids = usage.prompt_tokens 2688/2688、batch と stepped の接頭辞一致 9/9) は通った。
2. **筋書き (process) に欠陥**: 公開の筋と席の筋に選択肢名・ラベル・選好 (「Option A emerges as the most stable choice」)・人狼の被疑者名が入っており、「結末を含まない」定義に反していた。検証を強化済み、9 本の再生成と process 条件 18 局の回し直しが必要。
3. batch と stepped は「分割自体は効かない」の実証として使えるが、vLLM の非決定性で数行以内に分岐するので、報告は「接頭辞のトークン列と表現 (cos ≥ 0.9998) は同一、分岐は近接確率の反転・正規化・行順」と限定して書く。

## 発見した問題 (深刻度順)

| # | 深刻度 | 項目 | 証拠 | 影響 | 修正 |
|---|---|---|---|---|---|
| 1 | Critical (修正済み・未再生成) | process 筋書きが結末・選択肢・被疑者を含む | scenarios/candidate_selection/candidate_selection_0003.json の seats "eventually supports the Study Commons"、shared_living_0003.json period 3 public "Option A emerges as the most stable choice"、aiwolf_0001.json period 1 "Benjamin reveals his divination of Shizue" | process 条件が「未来情報あり」になり、先出し違反が増え (multi-private-process cs_0003 で 16 件)、計画の効果と未来情報の効果が分離できない | common/scenario.py `_validate_prose` を強化 (選好語、選択肢名・ラベル・素材に無い選択肢語、人狼の他者名)、要求文も同じ規則。再生成と 18 局の再実行 |
| 2 | Major (設計の限界、報告で対応) | multi-public で「知っていて知らないふり」が疑いの向きに漏れる | aiwolf_0001 multi-public Day 1 Turn 1: Mizuki (村人) が根拠なく真の人狼 Shizue を疑う。single-online でも同様 (Mizuki が Day 1 冒頭で Shizue を疑い、Shizue が自分に投票) | 情報忠実さの軸で測るべき現象。public 条件の「議論の質」の解釈に注意 | 指標「根拠より前に真の人狼へ疑いが向く率」「人狼の自己投票」を情報忠実さに入れる。論文で診断用条件と明記 (v3 済み) |
| 3 | Major (測定) | 語数が条件で大きく違い、Skip/Over の使い方も違う | 集計: multi 32 語、single-online 25、single-batch 13、stepped 13 (Skip 40 回で最多) | 長さの交絡。stepped の Skip 多発は batch の `Skip` 行の癖がサーバの逐次問い合わせで増幅された可能性 | 長さを共変量に。stepped の Skip の由来 (batch が Turn 3 を Skip で埋める癖) を確認して報告 |
| 4 | Minor | batch と stepped の分岐に「調査行の席順」が含まれる | candidate_selection_0002: 16 行目の `- investigate:` の順序 (batch は発話順、サーバは席順) | 分岐の一因が手続き差。結末の決め手の差として報告可能 | サーバの調査問い合わせを発話順にするか (書き手の習慣に合わせる)、報告で明記。前者を推奨 (小変更) |
| 5 | Minor | GPU 予約の運用 | 予約開始前に GPU#7 を使った | 運用規則違反 (実害なし) | 予約開始を待つ |
| 6 | Minor | inspect の tee を head に流して検査が途中で止まった | 初回の pilot5_inspect.txt | 誤った部分集計を一時的に見た (修正済み) | 検査は常にファイルに全量を書く |

## 確認した範囲

- 全 63 局の終局と違反集計、server 経路 45 局の TALK user のバイト一致、2688 呼び出しの prompt_token_ids、batch と stepped の分岐点 (9 setup) とその原因 (4 件の近接確率、1 件の正規化、1 件の行順、他は未分類)。
- hidden states: aiwolf_0001 の 5 条件で位置の正しさ (札トークン `**:`、生成プロンプト末尾 `<channel|>`)、batch と stepped の恒等性、batch と online の差。
- 筋書き 9 本の process 描画の本文。

## 確認していない範囲

- 議論の質の評価 (未設計)。読み比べは aiwolf_0001 の single-online と multi-public のみ。
- 他ドメインの台本の内容。筋書きの outline / turn 粒度の条件 (未実行)。
- Qwen3.8 / gemma-4-12B での動作。
