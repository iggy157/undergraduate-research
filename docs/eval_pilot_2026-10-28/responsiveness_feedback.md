# 応答性 (Bo et al. の Responsiveness) の注釈の妥当性 — 読み合わせメモ (2026-10-28)

対象: パイロット 8 (会話文 + @Name) の single-batch、shared_living_0001 / 0002 の Round 2〜3 を、Opus / Sonnet の発話単位の注釈と突き合わせて読んだ。結論: 判定は定義どおりで概ね妥当。single が不利になる箇所が 2 種類あり、1 つは定義のあいまいさ、1 つは single の本当の癖。

## 妥当な箇所
- 各ラウンドの第 1 ターン (各自が調査結果を並べる) は両判定者とも 0。multi の同じ構造の行も 0 で、条件間で公平。
- @ を使った第 2 ターン (例: 「@May, if it takes an hour, that's a long time to stand outside!」「@Asuka, if the paperwork is hard and the cost is high, maybe a permanent structure isn't the best?」) は両者とも 1。実際にやり取りになっている。
- 自分の調査結果の言い直し (「I don't want a smelly bin house! Let's not do that.」「If we go inland, we might end up exhausted from poor sleep again.」) は 0 または空回り 1 で妥当。

## 定義があいまいで判定者が割れる箇所 (single に不利)
- Round 3 の「合唱」: 1 人が「ローテーションに投票する」と言った後、全員が自分の理由を付けて同調する行 (「Rotating seems the most budget-friendly, though Asuka mentioned the space issue.」「I'll vote for B too. It's the safest for our wallets.」)。Opus は前の発言を受けたとして 1、Sonnet は並列の表明として 0。Bo の定義 (直前の発言に取り組んでいるか) では 1 でもよい。判定者間の不一致 (κ 0.78) はここに集中。

## single の本当の癖 (妥当に減点されている箇所)
- 呼びかけはするが、呼びかけられた本人が答えない・反対しない。例: shared_living_0002 R3T2 Midori「@Asuka, do you think we can make rotation work despite the narrow spots?」に Asuka は答えず「It's the most logical choice if we want to avoid long-term resentment.」。代わりに Shunichi が答える。反論率が候補者選定で 2 vs 10 なのはこの反映 (結論ありき)。

## multi 側の注意
- multi の応答性には儀礼的な受け (「That is a very fair point, Mio. However, ...」) が含まれ、Bo の定義ではそれも 1。内容に取り組んだ応答に絞ると multi の数値は下がり、差は縮まる。

## 提案 (今回は採らず、本実験の設計時に再検討)
1. **質問への返答率**: 誰かに向けられた質問 (@ 付きで「?」で終わる等) のうち、本人が次の自分の発話で答えた割合。「呼びかけたが答えがない」を捉える。
2. **同調のみ**: 直前の発言に賛成するだけで新しい理由も反対も加えない行の率 (空回りの一種として別立て)。「合唱」を判定者の解釈に任せずに数える。
これで「single は呼びかけるが答えない・反対しない、multi は答えるが冗長」を判定者の揺れに依存せず示せる。
