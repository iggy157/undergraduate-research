# 監査 E: 横断的検閲 (研究計画・実装・結果を通して) — 2026-10-28

対象: docs/paper_draft.md v3、DESIGN §0/§6/§7/§13/§14、前回検閲 00_SUMMARY、pilot5_inspect.txt、common/conditions.py・render.py・scenario.py、agent/base/seat.py、log/_pilot5 (全 63 局の違反・正規化集計、aiwolf_0001 と candidate_selection_0001 は全条件の台本を通読、batch vs stepped はトークン id 列で照合)。

## 結論 (3 行)

1. 基盤の統制 (共通ブロックのバイト一致、席ビュー/書き手ビューの復元一致 2688/2688 call、batch と stepped のトークン列一致) は確認でき、強みとして書ける。ただし梯子は「5 要因を 1 つずつ」ではなく、stepped→online に 2 要因 (論文も認める)、online→public に少なくとも 3 要因 (役割文・文脈分割・動的情報の可視性。論文は未記載) が同居する。
2. 致命的なのは筋書き: 現行の process 筋書き 9 本すべてが役職 (人狼 3/3 で Seer と Werewolf の名前)・最終選好 (議論 6/6 で A 等の支持)・未公開の選択肢名を含み、multi-private-process は実質 public + 未来情報になっている (夜 0 の占いが人狼に命中 0/3 → 3/3、先出し 3 → 22 件)。DESIGN §13 末尾で把握済みだが、語リストの強化では足りない。
3. 評価未設計のまま本実験に進むのは危険: 条件が長さ (13 語 vs 32 語)・Over 率 (106 vs 20) から一目で分かり盲検化が崩れる、選択肢 A が 34/42 局で採択され結末に分散がない、aiwolf は全知条件で 12/12 局が夜 0 に人狼を占い Day 1 で終局する。一次指標・提示形式・ラベル順の釣り合いを先に決める必要がある。

## 発見した問題 (深刻度順)

| # | 深刻度 | 項目 | 証拠 | 影響 | 修正案 |
|---|---|---|---|---|---|
| 1 | Critical | process 筋書きが秘密と結末を含む | scenarios/aiwolf/000{1,2,3}.json の Day 1 public 行 (「Benjamin reveals his divination of Shizue as the Werewolf」「Toshio knows Kenji is the werewolf」)、seats 行 (「to protect his werewolf ally」)。議論 6 本の seats 行が「shifts to supporting A」「supports the Study Commons」。`_validate_prose` (common/scenario.py `_OUTCOME_WORDS`) は executed/adopted/wins 等しか見ない。`scenario_context` は public 行を席で絞らない (render.py `scenario_block` → 全席同文) | multi-private-process の全席が人狼・占い師を system で知る。pilot: 夜 0 占いの人狼命中 multi-private 0/3 → -process 3/3、early_reveal(_partial) 3 → 23 件。RQ2 の「結末を含まない筋書き」「private + process」「process と outcome の分離」(貢献 4) が成立しない | 語リストでは防げない (「誰が疑われるか」は 2 日で終わる人狼では結末そのもの)。(a) process 筋書きは**公開情報だけ**のプロンプト (役職・カード本文・選択肢を見せない書き手) から生成する、または席ごとの筋を各席の private view から生成する。(b) 生成後に漏洩テスト (筋書きだけから役職/採択を LLM に当てさせ、偶然水準との差を報告)。(c) 直せないなら multi-private-process を落とし、筋書き条件は public 限定と明記する |
| 2 | Major | batch vs stepped の分岐は早く、雑音の基準線がない | 9 設定の最初の分岐: 行 4〜21 (全 64〜97 行)。トークン照合では 4/9 が数値的反転 (両側の chosen logprob −0.65〜−0.84、ほぼ同確率)、5/9 がサーバ側 (Skip.→Skip 正規化、investigate 行の席順、Over 後の Turn 省略)。batch と stepped は同時刻に並走 (ts 031549/031550) | 「stepped と batch の差 = 数値誤差」を示す対照 (同条件の 2 回走行) がない。stepped 以降は別軌道なので、恒等性は冒頭 5〜25% の行に限られる | single-batch を同設定で 2 回走らせ雑音の下限を取る (全 90 設定でも 4k tok/局で安価)。vLLM の batch-invariant モードが使えるなら有効化し、batch と stepped を他ジョブと並走させない。top-k (k≥2) logprob を記録して余裕 (margin) を直接測る |
| 3 | Major | online→multi-public は 3 要因が同居 | role.jinja: writer 文 vs participant 文 (目標も変わる)。online の user は書き手ビュー (全席の `- divine/attack/investigate` 行を発生時点で含む: seat.py `writer_mode` + `upsert_action`)、public の user は席ビュー (他席の行動は公開まで見えない)。system は同一 | 「1 つの文脈か席ごとか」の段に「書き手か参加者か」「動的な秘密 (占い結果・調査結果) を見るか」が混入。multi-public は「全情報」ではなく「静的な秘密のみ公開」 | 書き方で対応可 (§3.2 の表に明記) だが、分解したいなら「participant 役割文 + 書き手ビュー」の 1 条件を足す (diagnostic)。最低限、paper の梯子表を 3 要因に書き直す |
| 4 | Major | 条件が台本から判別でき、盲検が成立しない | pilot5: 平均語数 single-batch 13.2 / stepped 12.6 / online 24.6 / multi 32; Over 回数 (9 局) batch 106 / multi 20; batch は Turn 3 で全員 Over → Turn 4 で全員 Skip (cs_0001 raw/transcript.md)。multi は trailing_over 正規化で同一ターンに「発話 + Over」の 2 行 (17〜24 件/9 局) | 人手対比較で評価者が条件を推定できる。LLM 判定は長文選好 (Samanta et al.) で multi に傾く | 評価設計で (a) 評価者に条件推定を回答させ一致率を報告、(b) 長さ・Over 率を共変量、(c) 長さを揃えた部分集合、(d) 提示形式 (正規化後の行、Over 行の表示、行動行の有無) を全条件同一に固定 |
| 5 | Major | 結末の分散がほぼゼロ | 議論 42 局中 A 採択 34 (cs 19/21、sl 15/21)。筋書き生成も 6 本中 5 本が A。aiwolf は全知 5 条件 (batch/stepped 除く) 12/12 局で夜 0 に人狼を占い、27 局中 25 が VILLAGE、Day 1 終局 | 「正解のない議題」の前提が崩れる (ラベル順バイアス)。多様性軸・プローブのラベル (最終投票先・採択・勝敗) に分散がなく、前回 B6 の指摘が全ラベルに広がる | setups でラベル↔選択肢の対応を設定ごとに置換 (counterbalance)。aiwolf は全知条件で退化することを明記し、Day 1 終局率を手続き指標に。必要なら aiwolf を主系から層別因子の 1 つに下げる |
| 6 | Major | 評価が未設計 (一次指標・提示・規模) | paper §4.2 は軸と測り方の表のみ。6 軸 × 5 対 × 30 設定 × 3 評価者 = 2,700 対比較/台本 1〜2k 語 | 本実験後に指標を決めると探索的分析との区別が消える (論文は事前固定を約束) | 下の「必須」4 を参照 |
| 7 | Minor | stepped→online に未記載の差 | stepped の user は batch の出力形式 + 内容制約 (「dead players have no further lines」「divine result must match the true role」; single/prompts/format_*.jinja)。online/multi の VOTE/ACTION は要求文 + 候補一覧 (agent/base/prompts.py `build_vote_message`)、stepped は札のみ | 小さな指示差・情報差 (生存者一覧) | §8 限界に 1 行。候補一覧は「サーバが候補を提示する」として設計差に含める |
| 8 | Minor | header に版・精度・revision がない | 全局の header キー: model_info (vLLM `/models` の id/root/max_model_len) と models_yml_sha1 のみ。vLLM 版・dtype・HF revision・chat template hash・GPU 構成なし。paper §7 は「固定記録」と書く | 再現性の主張と記録が食い違う | header に vllm version / dtype / revision / template sha1 / tensor_parallel を追加 |
| 9 | Minor | 設計文書の矛盾 | DESIGN §13 L485「private + 筋書きは作らない」 vs L479/487「process は private にも可」。conditions.py `PRIVATE_SAFE_PLANS` の「no outcomes, no secrets」は検証されない | 第三者が読むと設計が揺れて見える | L485 を削除し、「process は漏洩テスト合格を条件に private 可」に |
| 10 | Minor | 先出し検出の語が汎用的 | early_reveal_partial の上位トークン: Location, Campus, Structure, Study, Upgrade (common/violations.py `PARTIAL_STOPWORDS` に無い) | 先出し率が偽陽性を含む。single-online 18 件 vs single-batch 1 件の差も要精査 | stopword の拡張 + 人手検証 (paper 付録 D と整合)。「先出しは一括生成に固有」(claim f) は現時点で逆向き |
| 11 | Minor | ペルソナ・言語・ドメインの非対称 | 24 ペルソナを 90 設定 × 3 ドメインで再利用 (aiwolf_0001 と cs_0001 に Benjamin/Kenji)。日本語名 + 英語本文 + 「-san」。aiwolf は 2 期間、議論は 3 ラウンド。aiwolf に先出し指標なし | 混合効果にペルソナの変量効果が要る。情報忠実さ軸の中身がドメインで異なる | ペルソナを変量効果に、ドメイン別報告 (既定) を一次に |

## 設問への回答

**(1) 梯子の分離**: 設計した要因ごとに、混入している差を列挙する。
- batch→stepped: 設計 = 結末・構造の決め手。混入 = (a) vLLM の数値的非決定性 (致命ではないが基準線が要る: #2)、(b) 接頭辞の正規化 (Skip.→Skip) と行順 (サーバが「構造を決める」の一部として許容)、(c) 行ごとの停止列と max_tokens (無害)。トークン列は分岐まで完全一致 (確認済み: aiwolf_0001 で prompt 1554 + 接頭辞 190 トークンまで同一)。
- stepped→online: 設計 = 目標 + 履歴の置き場 (論文が認める 2 要因)。混入 = 役割文の文面差、出力形式・内容制約の有無、候補一覧の有無 (#7)。許容 (明記すれば)。
- online→multi-public: 設計 = 文脈の分割。混入 = 役割の枠組み (書き手→参加者)、動的な秘密の可視性 (他席の行動行) (#3)。**明記が必須**。分離したいなら 1 条件追加。
- multi-public→multi-private: 設計 = 情報量。混入 = system の長さ (5 人物 + 隠し情報 vs 1 人物)、人狼では「ゲームの性質」(論文は明記済み)。許容。
- 筋書き条件: 「全条件に同文」は private では自席の筋のみで不成立 (設計どおり)。ただし #1 により現状は private でも秘密が入る。

**(2) 「分割自体は効かない」の論理と実証**: 論理 (greedy + 同一トークン列 → 同一続き) は自明で査読者も受け入れるが、それゆえ「実証」を**貢献**に数えると弱く見える。トークン列一致と cos ≥ 0.9998 は実装の検証 (sanity check) として付録に置くのが妥当。査読者が突くのは (i) 分岐が 4〜21 行目と早く、同一区間が短い、(ii) 「差は数値誤差と同程度」を言うには同条件 2 回走行の雑音下限が要る (#2)、(iii) 4/9 設定で chosen logprob が両側 −0.65〜−0.84 の近接確率で反転しており、「greedy の再現性」を前提にする記述全体に但し書きが要る。batch-invariant な推論が使えれば (i)(ii) は大きく改善する。

**(3) 筋書き設計**: process を主系・outcome を未来情報の効果とする構造は妥当だが、現行の筋書きではその分離が成立しない (#1)。さらに構造的な非対称がある: 筋書きは生成モデル自身が single-batch の system (全知) から greedy で書くため、single-batch にとっては「自分がどうせ書く話」の明示 (pilot: single-batch-process の結末・乖離は single-batch と同一、乖離 0) であり、multi にとっては「書き手の物語の注入」になる。したがって測れるのは「明示的な計画の効果」ではなく「単一書き手の筋を逐次方式に与える効果」。公開情報のみから筋書きを生成する (または別モデル・人手) ことで、この非対称を弱められる。乖離率 0/63 局は筋書きの拘束力の指標としては使えるが、「筋書きどおり」であることが結末の漏洩によるのか計画の効果なのかは区別できない。

**(4) 評価未設計のリスクと最小限**: 本実験 (990 局) を回してから指標を決めると、事前固定を謳う §4.2 の統計方針が空文になり、長さ・ラベル順・Over パターンの交絡 (#4, #5) を後から外せない。先に決める最小限: (a) 一次指標 2〜3 軸 (人手) と主要比較 5 対、同等性マージンの数値、(b) 評価者に見せる描画 (writer view の正規化後、行動行・票行の表示有無、Over 行の扱い) を 1 本に固定、(c) 盲検性の監査 (条件推定の回答)、(d) 長さの共変量と長さ揃え部分集合の定義、(e) ラベル順の釣り合い (setup 生成時)、(f) LLM 判定の順序入替と人手との一致率の算出手順、(g) 除外規則 (error / truncated / 早期終局)。ログ側はこれらに必要な情報 (行・語数・正規化・違反・トークン id) を揃えている (確認済み)。

**(5) 実装の統制の主張**: バイト一致の自動検証、席ビューの決定的復元 (2688/2688 call で一致)、vLLM が見たトークン id の記録は、ACL 系の再現性要件を超える水準で、強みとして**短く**主張できる (基盤の貢献 (1) の中の 1 文 + 付録)。過剰ではないが、貢献の見出しにすると「工学的」と評される。欠けているのは header の版情報 (#8) と top-k logprob (#2)。

**(6) 主張の過大な点**: (i) 第一候補タイトルの「Generation Granularity」は本文の主張 (粒度自体は効かない) と矛盾する — 第二候補が整合。(ii) 貢献 (2)「5 条件で 5 要因を 1 つずつ分離」は 2 段で複数要因が同居する (#3, §8 の admission は stepped→online のみ)。(iii) 貢献 (4)「process と outcome の分離」は #1 が直るまで導けない。(iv) 貢献 (5)「先出しは一括生成に固有」は pilot で逆 (online 18 件 vs batch 1 件) で、仮説として書く。(v) 「同一の情報公開スケジュール」は文面の同一性であり、書き手が見る情報は条件で違う (そこが研究対象) — 表現を「同一のスケジュール文」に。(vi) 「3 ドメイン」は aiwolf が全知条件で退化 (Day 1 終局) するため、結果の大半は議論 2 ドメイン由来になる見込み。(vii) 結論 §9 は仮置きの向きで書かれており、「向きは実測で決まる」と一貫させる。

**(7) 部分検閲が見落としやすい横断的問題**: ラベル順バイアスと結末の無分散 (#5)、筋書き生成モデル = 生成モデル = プローブ対象モデルの自己一致 (すべて gemma-4-31b)、ペルソナ再利用と文化的表層 (#11)、aiwolf と議論ドメインの構造差 (期間数、先出し指標の有無、全知条件の退化)、正規化の方式非対称 (batch は pass_after_over 20 / over_repeat 5: 書き手が Over の意味を守らない; multi はサーバが強制。評価者に見せるのは正規化後か生出力か)、同時走行によるバッチ構成の違い (#2)、stepped の継続生成が Gemma の空の思考チャネルに依存する点 (Qwen3.8 では /tokenize + completions の再現性を別途検証する必要)、DESIGN の内部矛盾 (#9)。

## 優先順位

**本実験に進む前の必須修正**
1. process 筋書きの作り直し: 公開情報のみから生成 (役職・カード本文・選択肢を見せない) + 漏洩テスト + 検証規則の再設計。直せなければ multi-private-process を落とし、筋書きは public 限定と宣言する (#1)。18 局の回し直しだけでは不十分。
2. 雑音の基準線: single-batch を各設定 2 回 (少なくとも 30 設定)。batch-invariant 推論の可否を確認し、batch/stepped は他ジョブと並走させない。top-k logprob の記録 (#2)。
3. setup 生成でラベル順を釣り合わせる (選択肢↔ラベルの置換)。aiwolf の Day 1 終局率と夜 0 命中率を手続き指標に加え、主系に残すか決める (#5)。
4. 評価の最小設計を文書化して固定: 一次指標・主要比較・同等性マージン・描画形式・盲検監査・長さ共変量・除外規則 (#4, #6)。
5. header に vLLM 版・dtype・revision・template hash を追加 (#8。90 設定を回す前に入れないと記録が二層になる)。

**進めながら直せるもの**
6. online→public の 3 要因を §3.2 の表に明記、必要なら診断条件 (participant 役割文 + 書き手ビュー) を 10 設定で追加 (#3)。
7. stepped→online の未記載差 (出力形式・内容制約・候補一覧) を限界に追記 (#7)。
8. early_reveal の stopword 拡張と人手検証、single-online の先出しの中身の確認 (#10)。
9. DESIGN §13 L485 の削除と conditions.py の docstring 修正 (#9)。混合効果モデルにペルソナを変量効果として追加 (#11)。
10. 人手評価の規模: 人手は 2〜3 軸に絞り、残りは LLM 判定 + 一致率で補う。

**論文の書き方で対応するもの**
11. タイトルは第二候補系に。貢献 (2) は「検証」に格下げし、(4)(5) は結果次第の仮説として書く。「5 要因を 1 つずつ」は「隣接条件ごとに 1〜3 要因、表に列挙」に。
12. multi-public = 静的な秘密の公開、online = 動的な秘密も見る書き手、と定義を分けて書く。筋書きは「単一書き手の筋」であることと、single にとってほぼ無変化である非対称を限界に。
13. 「greedy で再現可能」は「同一トークン列の範囲で一致、近接確率での反転を n/N 局で観測、雑音下限は X」と数値で書く。

## 確認した範囲と確認していない範囲

- 確認済み (実ログ・コード): 全 63 局の violations / normalized / deviation の集計、header のキー、sampling、aiwolf_0001 と candidate_selection_0001 の全条件台本、batch vs stepped のトークン id 照合 (9 設定) と分岐点の logprob、夜 0 占い先と人狼の照合 (全 aiwolf 局)、議論 42 局の採択ラベル、process 筋書き 9 本の prose、`## Plan` の実描画 (single-batch-process と multi-private-process の system)、scenario.py の検証語リストと席フィルタ、seat.py / prompts.py の user 構成、models.yml。
- 確認していない: verify_prompt_control.py と tests の再実行 (前回検閲と pilot5_inspect の結果を信用)、hidden states の cos 値 (DESIGN §14 の記述を信用)、shared_living の台本通読 (集計のみ)、vLLM の版と batch-invariant モードの可否 (推測: 環境依存)、Qwen3.8 での継続生成の再現性 (未実施、推測)。
- 推測を含む判断: #2 の「同時走行がバッチ構成を変えた」は timestamp からの推測。#5 の「ラベル順バイアス」は A 偏重の観測からの推測で、置換実験で確かめる必要がある。#1 の漏洩の影響度 (占い命中・先出し) は 3 設定のみの観測。
