# パイロット 8 (63 局): 非公開情報の開示候補の人手確認 (2026-10-28)

`scripts/eval_metrics.py` の語照合候補 12 件 (private_use) と先出し候補 2 件 (early_option) を、カード本文と「調べた本人がそれ以前に言った発話」と並べて確認した。

| 局 | 発話 | 候補の根拠 | 判定 | 理由 |
|---|---|---|---|---|
| candidate_selection_0001 multi-public | [39] Toshio | 'found', 'often' (Benjamin のカード) | 偽 | 別のカードの内容。一般語の一致 |
| candidate_selection_0001 single-batch-process | [56] Midori「glasshouses are booked solid」 | Kenji のカード | 偽 | Kenji が [37] で「glasshouses are packed」と共有済み (言い換え) |
| shared_living_0001 multi-private | [53] Rin | 'actually', 'sleeping' | 偽 | 一般語 |
| shared_living_0002 multi-private-process | [53] May | 'clear', 'starts' | 偽 | 一般語 |
| shared_living_0003 multi-private-process | [38] Shion | 'half' | 偽 | 自分のカード (理学療法士のメモ) の内容 |
| shared_living_0003 multi-private | [76] Toshio | 'repeated', 'single' | 偽 | 一般語 |
| shared_living_0003 multi-public | [45] Rin「takes days to fix the chairs」 | Shion のカード | 偽 | Shion が [43] で「days of fine-tuning」と共有済み |
| shared_living_0002 single-batch-process | [44] Asuka「Every change needs a new notice」 | May のカード | **本物** | May は [38] で「4 か月と署名」しか言っておらず、「場所を変えるたびに届け」は未共有 |
| shared_living_0003 single-batch | [25] Rin「It takes forever to settle in」 | Shion のカード | **本物** | Round 2 の最初の発話。Shion はまだ何も言っていない。「settle」はカードの「takes days of small corrections to settle」 |
| shared_living_0003 single-batch-stepped | [25] Rin (同文) | 同上 | **本物** | batch と同文 (分岐前) |
| shared_living_0001 single-online | [49] Misaki「non-refundable deposit」 | Mio のカード | 境界 | Mio が [35] で「遅れて抜けると残りが払う」と趣旨を共有済み。「non-refundable deposit」という語は未共有 |
| shared_living_0001 single-online | [51] Shizue「non-refundable commitment fee」 | 同上 | 偽 | [49] を受けた提案 |
| shared_living_0001 single-batch | [46] Shizue「a coastal lodge」 (先出し) | 選択肢 Coastal Lodge | 境界 | 一般名詞句として使っており、正式名の先出しとは言い切れない |
| shared_living_0001 single-online | [48] Rin「the Mountain Training Centre」 (先出し) | 選択肢名 | **本物** | Round 2 で正式名 |

集計: 開示の本物 3 件 (single-batch 1、stepped 1 (同文)、single-batch-process 1)、境界 1 件 (single-online)、multi は 0。語照合の精度 3/12 = 0.25。先出し: single-online 1 件、single-batch 境界 1 件。
