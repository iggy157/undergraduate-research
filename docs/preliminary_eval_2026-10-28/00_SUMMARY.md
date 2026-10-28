# 予備評価 (2026-10-28): パイロット 6 の台本をサブエージェントに読み比べさせた結果

目的: 本評価の設計前に「条件がどう見えるか」の感覚を得る。論文には使わない。
材料: パイロット 6 の 3 設定 (aiwolf_0001 / candidate_selection_0001 / shared_living_0002) × 7 条件の台本 (書き手ビュー、条件名を伏せて A〜G)。`scripts/render_blind_pairs.py --seed 7`。鍵は *.key.json。
判定者: 自由記述 (順位) と 6 軸採点表 × Opus / Sonnet の 4 本 (free_*.md, rubric_*.md)。鍵は見せていない。

## 鍵

| 設定 | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| aiwolf_0001 | single-batch-stepped | single-online | single-batch-process | multi-private | single-batch | multi-private-process | multi-public |
| candidate_selection_0001 | single-batch | single-online | single-batch-stepped | multi-private-process | multi-private | single-batch-process | multi-public |
| shared_living_0002 | multi-public | single-batch-stepped | single-batch-process | multi-private-process | multi-private | single-online | single-batch |

## 順位 (条件名に戻したもの)

| 設定 | Sonnet 自由記述 | Opus 自由記述 | Sonnet 採点表 (最高) | Opus 採点表 (最高) |
|---|---|---|---|---|
| aiwolf | private > batch-process > online > public > private-process > stepped = batch | private > public > private-process > batch-process > online > batch > stepped | private | 整合性: batch-process, public / 自然さ: online, private |
| candidate_selection | online > private > batch-process > stepped > private-process > public > batch | private > online > private-process > public > batch-process > stepped > batch | private | private |
| shared_living | online > private-process > batch-process > public > private > stepped > batch | online > private-process > private > public > batch-process > batch > stepped | private-process | 推論: private-process / 自然さ・情報: online |

## 読み

1. **方向**: 4 本中 3 本以上で、最上位は multi-private か single-online (または private-process)、最下位は single-batch か single-batch-stepped。草稿 v3 の「全体整合性は batch が高く、応答性は multi が高い」という想定に対し、**整合性でも batch は上位に来ていない** (Opus 採点表で batch-process と public が整合性最高とされた aiwolf だけ例外)。batch の減点理由は、短い発話、全員一斉の Skip / Over、未公開情報の使用 (Kenji が他人の調査結果を根拠にする = 書き手の全知の漏れ)。
2. **判定者間の一致**: 最上位と最下位はおおむね一致 (private / online が上、batch / stepped が下)。中位の順序は判定者とプロンプトで入れ替わる。Samanta et al. の警告どおり、順位全体の一致は低い。
3. **作り方の推測**: 4 本すべてが「一括生成の 3 本 (batch, stepped, batch-process)」を 3 設定とも正確に見分けた (12/12)。根拠は全員一斉の Skip / Over、短さ、冒頭の逐語一致 (batch と stepped は同じプロンプトなので冒頭が同文)。**盲検は長さと Skip / Over の形で破れる**。Opus 採点表は残りを「全員の情報を知る書き手らしさ (狼の自己投票、根拠なしの真狼への収束、選択肢の先取り)」で online + public と private + private-process に分けており、これは条件の情報軸と一致する。
4. **情報の忠実さ**: 具体的な指摘が条件と整合する: batch 系 = 他人の調査結果を使う (全知の漏れ)、online = 狼が自分に投票・根拠なしに真狼を疑う (全知の文脈)、public = 公開前の選択肢に言及、private = 票が議論と噛み合わない (aiwolf F: 誰も疑っていない Mizuki に 4 票)。この軸は事実照合で機械化できる (調査結果の出所、票と発言の整合、公開前の選択肢語)。
5. **長さの影響**: 両採点者が「長い台本を応答性・自然さ・多様性で有利に、短い台本を情報の正確さで有利に付けた」と自己申告。長さを共変量にするか、長さを揃えた対で比べる必要がある。
6. **batch と stepped の見え方**: 冒頭が逐語一致し、全体の印象も同じ群。「分割は効かない」の定性的な裏づけ。

## 評価設計への含意

- 一次軸: 情報の忠実さ (機械 + 人手検証)、局所応答性、相互作用の自然さ、全体整合性。多様性は長さ補正が難しいので従。
- 対比較は長さの近い対を優先し、長さの差を共変量として報告。全員一斉の Skip / Over は条件の署名なので隠さず、別途「内容ゼロのターン」として数える。
- LLM 判定は順位の中位で不安定。人手評価を主にし、LLM 判定は最上位・最下位の一致率で補助的に使う。
- 仮説の書き方 (v4): 「batch は整合的」ではなく「batch は短く結論に直行し、全知の情報が漏れる。1 行ずつの条件は応答と対立が豊かで長い」。トレードオフの向きは実測で決める。
