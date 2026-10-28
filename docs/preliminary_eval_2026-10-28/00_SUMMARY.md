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

## 方向の修正 (ユーザの指摘、2026-10-28)

上の「読み」は判定者の価値判断をそのまま書いたもので、研究が良しとする方向とは逆である。研究が重視するのは、人間の議論らしいテンポ、状況に応じて長さと中身が変わること、話すことがなければ Skip / Over でターンを適切に消費すること (ターンが残っているからと冗長に続けない) であり、判定者は「長く・多く話す」ことをほぼ一貫して高く評価していた (両採点者が長さの影響を自己申告)。パイロット 6 全 72 局の機械指標:

| 条件 | 平均語数 | 上限張りつき (≥35 語) | 新規内容語の割合 | 自己反復 (Jaccard) | 定型句 | Skip / Over | 全員パスのターン |
|---|---|---|---|---|---|---|---|
| multi-private | 33.0 | 0.38 | 0.52 | 0.071 | 0.07 | 2 / 28 | 0 |
| multi-private-process | 33.2 | 0.37 | 0.53 | 0.070 | 0.06 | 2 / 38 | 0 |
| multi-public | 30.4 | 0.18 | 0.52 | 0.086 | 0.05 | 12 / 33 | 1 |
| single-online | 24.4 | 0.02 | 0.59 | 0.055 | 0.03 | 18 / 28 | 8 |
| single-batch | 14.7 | 0.00 | 0.74 | 0.040 | 0.00 | 82 / 210 | 56 |
| single-batch-process | 16.4 | 0.00 | 0.72 | 0.031 | 0.02 | 35 / 104 | 25 |
| single-batch-stepped | 13.6 | 0.00 | 0.76 | 0.031 | 0.00 | 39 / 104 | 27 |

multi は発話の 4 割弱が語数上限に張りつき、内容語の半分は既出で、「おやすみなさい」「見守ります」の類の定型句が 5〜7%、Skip はほぼ使わない。single-batch は上限張りつきゼロ、新規内容語 7 割超、定型句ゼロ、Skip / Over を使って Day 0 後半や Round 1 後半を畳む。判定者は前者を「応答が豊か」、後者を「薄い」と見たが、研究の価値基準では前者が「冗長で中身が薄い」、後者が「密度が高くテンポが良い」になりうる。両方の見方が同じデータから出るので、**評価は「量」と「質」を分ける設計にする**:

- 密度とテンポの機械指標 (上に挙げたもの): 新規内容語率、上限張りつき率、自己反復、定型句率、Skip / Over の適切さ (新規性の低い発話を続けたか、Skip / Over を選んだか)、全員パスのターン数 (畳みすぎの側の指標)。
- 人手評価の指示に「長さや量で評価しない。状況に合った長さか、話すことがないときに適切に譲っているか、人間の議論として自然なテンポか」を明記し、長さの近い対で比べる。LLM 判定も同じ指示で、長さバイアスの残り具合を人手との一致で測る。
- 情報の忠実さ (他人の秘密・未公開情報の使用、票と発言の整合) は機械 + 人手で独立に測る (上の「読み」4 はこの軸として有効)。
- 仮説の書き方: 「multi は応答が豊か」ではなく「multi は長く冗長で上限に張りつき、batch は短く密度が高い。どちらを人間らしいと見るかは評価軸で分ける」。先出し・全知の漏れは batch 側の弱点として残す。
