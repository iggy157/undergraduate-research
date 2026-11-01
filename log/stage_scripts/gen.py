import re,glob,json
R='/diskthalys/ssd14ta/yharada/aiwolf/undergraduate_research/docs'
G={'gemma':R+'/main_gemma31b/annotation','qwen':R+'/main_qwen38/annotation'}
def parse(m,s,c):
    d={}
    for l in open(f'{G[m]}/games/{s}__{c}.md'):
        x=re.match(r'- \[(\d+)\] \*\*(.+?)\*\*: (.*)',l.rstrip('\n'))
        if x: d[int(x[1])]=(x[2],x[3])
    return d
def ann(m,s,c):
    v=list(json.load(open(f'{G[m]}/out/llama__{s}__{c}.json')).values())[0]
    return {x['seq']:x for x in v}
pat=re.compile(r"\b(fair point|valid point|fair question|I understand|I appreciate|I respect|I agree)\b",re.I)
def stats(m,c):
    n=k=w=0
    for f in glob.glob(f'{G[m]}/games/*__{c}.md'):
        for l in open(f):
            x=re.match(r'- \[(\d+)\] \*\*(.+?)\*\*: (.*)',l)
            if x: n+=1; w+=len(x[3].split()); k+=bool(pat.search(x[3]))
    return n,w/n,k/n
def excerpt(m,s,c,stage,a,b,notes):
    d=parse(m,s,c); A=ann(m,s,c); out=[f'**{c}** ({stage}, [{a}]–[{b}])\n','| id | 話者 | 発話 (原文) | 語数 | resp_to |','|---|---|---|---|---|']
    ws=[]
    for i in sorted(d):
        if a<=i<=b:
            sp,t=d[i]; w=len(t.split()); ws.append(w)
            rt=A.get(i,{}).get('resp_to'); rt='–' if rt is None else f'[{rt}]'
            out.append(f'| [{i}] | {sp} | {t.replace("|","/")} | {w} | {rt} |')
    out.append(f'\n平均 {sum(ws)/len(ws):.1f} 語 (範囲 {min(ws)}–{max(ws)})\n')
    out+= [f'- {n}' for n in notes]
    return '\n'.join(out)+'\n'
P=[]
P.append('# 発話例: single-batch と multi-private の比較 (2026-10-29 進捗報告用)\n')
P.append('出典: `docs/main_gemma31b/annotation/games/` と `docs/main_qwen38/annotation/games/` の描画済みトランスクリプト (原文のまま引用)。'
 '`resp_to` は `annotation/out/llama__<setup>__<condition>.json` の LLM 注釈 (その発話がどの発話に応答しているか)。語数は空白区切りの単語数。\n')
P.append('参考 (全 90 ゲームの集計, 同じ数え方):\n')
P.append('| モデル | 条件 | 発話数 | 平均語数 | 同意・承認語句を含む発話の割合* |\n|---|---|---|---|---|')
for m,cs in [('gemma',['single-batch','multi-private']),('qwen',['multi-private','multi-private-stepped'])]:
    for c in cs:
        n,w,k=stats(m,c); P.append(f'| {"gemma-4-31B" if m=="gemma" else "Qwen3.8-27B"} | {c} | {n} | {w:.1f} | {k*100:.1f}% |')
P.append('\n\\* 正規表現 `fair point|valid point|fair question|I understand|I appreciate|I respect|I agree` (大文字小文字無視) に一致する発話の割合。粗い目安。\n')
P.append('注意: multi-private は話者が固定順で 1 発話ずつ回るため、宛先の人の「次の発話」は通常 4 発話後になる。single-batch でも回答が 2–3 発話後に来る例がある ([36]→[39] など)。以下の「答えていない」は、宛先の人の次の発話が問いの内容に触れていないことを本文で確認したもの。\n')

P.append('\n## 例 1: 人狼 (aiwolf_0001, gemma-4-31B, Day 1)\n')
P.append('両条件とも Benjamin が占い結果を出した直後の場面。他の参加者が「占い師を名乗るのか」と問う。\n')
P.append(excerpt('gemma','aiwolf_0001','single-batch','Day 1',34,40,[
 '[36] で Minako が @Benjamin に「Seer を名乗るのか」と質問 → Benjamin の次の発話 [39] "I am indeed the Seer." で即答。[35] Kenji の "are you sure?" にも [39] "My divination was clear." が対応している。',
 '全発話 8–13 語。相手を評価・承認する前置きはない。']))
P.append(excerpt('gemma','aiwolf_0001','multi-private','Day 1',39,45,[
 '[40] Kenji (@Benjamin "Does that mean you\'re the Seer…?") と [41] Minako (@Benjamin "Are you officially claiming the Seer role?") が同じことを質問 → Benjamin の次の発話 [44] は @Mizuki ([43]) の「なぜ Kenji を選んだか」にだけ答え、Seer かどうかには答えない。以降の Benjamin の発話 [49][54] でも明言せず、[54] で "I shall use my vision" と婉曲に触れるのみ。',
 '定型的な前置き: [42] "It is quite a bold and helpful thing to do, Benjamin." / [44] "@Mizuki, a fair question." / [45] "@Benjamin, you\'re so nice!" — 相手への評価・承認から入る。',
 '冗長: [41] と [43] がほぼ同じ二択の論法 ("If you are the Seer, … if you are not / If you aren\'t, …") を繰り返し、直後の [46] で Minako が同じ論法をもう一度述べる。7 発話すべて 33–39 語。']))

P.append('\n## 例 2: 助成金審査会 (candidate_selection_0007, gemma-4-31B, Round 2)\n')
P.append('両条件とも各自が調べた記録の結果を出し合った直後の場面 (交通計画の審査)。\n')
P.append(excerpt('gemma','candidate_selection_0007','single-batch','Round 2',30,36,[
 '[30] May → @Benjamin「要員が薄いなら時間延長は無理か」 → 直後の [31] Benjamin "It makes it very risky." で回答 (注釈 resp_type=answer)。',
 '[32] Midori → @Jonathan「単一プラットフォームで予算は助かるか」 → Jonathan の次の発話 [34] "It might, but …" で回答。[33] Shizue → @May の質問 → May の次の発話 [35] で回答 (注釈 resp_type=answer)。',
 '3 つの @ 質問がすべて宛先の次の発話で答えられている。全発話 12–17 語。']))
P.append(excerpt('gemma','candidate_selection_0007','multi-private','Round 2',40,46,[
 '[40] May → @Jonathan "are we just pretending the old pilots\' successes are repeatable?" → Jonathan の次の発話 [44] は pilot の話に触れず、[42][43] の synchronization の話と自分の契約費の懸念を述べるだけ (注釈も [44] の resp_to は [43])。',
 '定型的な前置き: [41] "It is a delightful irony, isn\'t it?" / [43] "I agree with @Midori. It would be a shame to …" / [45] "@Jonathan, you\'re so cautious! But …"。この Round の締め [51]–[54] は全員が "I concur." / "I agree." で始め "I am ready (…)." で終わる。',
 '冗長: Jonathan は [39] "our long-term commitments to contractors are swelling" → [44] "without addressing the swelling contractor fees" → [49] "if we ignore the structural financial leaks" と同じ懸念を 3 回言い直す。7 発話すべて 32–36 語。']))

P.append('\n## 例 3: サークルの会費決め (shared_living_0016, gemma-4-31B, Round 2)\n')
P.append('両条件とも調査結果を出し合った後、分割払いか年会費かを議論している場面。\n')
P.append(excerpt('gemma','shared_living_0016','single-batch','Round 2',35,41,[
 '[35] Minato → @Ryuji「小分けの支払いの方がいいのでは?」 → 直後の [36] Ryuji "@Minato, that\'s the dilemma. But …" で応答 (注釈 resp_to=[35])。',
 '[37] Minako → @May「定額制自体が問題では?」 → 直後の [38] May "@Minako, but the turnout dropped when we added charges." で応答 (注釈 resp_to=[37])。',
 '全発話 15–19 語。']))
P.append(excerpt('gemma','shared_living_0016','multi-private','Round 2',43,49,[
 '[43] May → @Minako "aren\'t we just encouraging people to treat the club as a casual hobby …?" → Minako の次の発話 [47] は "@Minato, …" と Minato の [45] (年会費案) に答え、May の問いには触れない (注釈も [47] の resp_to は [46])。',
 '定型: 「@相手, A は〜だが (but) …」の譲歩型が 3 連続 — [46] "a single yearly fee is the most stable, but" / [47] "might be the simplest for the treasurer, but" / [48] "accessibility is fine, but"。[44] "@May, you\'re finally hitting on something." も評価から入る前置き。',
 '冗長: Shunichi の [44] と [49] は同じ主張 (常連が働き、来ない会員を支えている) の言い直し ([39][54] でも同じ)。Ryuji の [46] も固定費の話を [36][41] に続いて繰り返す。7 発話すべて 36–40 語 ([45] は上限の 40 語ちょうど)。']))

P.append('\n## 例 4: 人狼 (aiwolf_0008, Qwen3.8-27B, Day 1): multi-private vs multi-private-stepped\n')
P.append('両条件とも Day 1 の冒頭で占い結果が出て、他の参加者が「誰を占ったのか」と問う場面。ただし占いを名乗る人物は条件で異なる (multi-private は Minako、stepped は Sakura)。\n')
P.append(excerpt('qwen','aiwolf_0008','multi-private','Day 1',33,39,[
 '[34] Takumi "Who did you check last night?" / [35] Misaki "@Minako, who else did you check?" / [36] Sakura "@Minako … who should we check next?" と同じ質問が 3 回続く → Minako の次の発話 [37] は @Sakura 宛てに "I will not reveal my method." と言うだけで、誰を占ったかには答えない。',
 '[38] Victoria (@Minako "Please consider sharing more") と [39] Takumi ("@Minako, stop hiding!") の要求 → Minako の次の発話 [42] は Takumi の Sakura 攻撃をたしなめるだけで、情報共有の要求には触れない。',
 '定型: [33] "@Minako, that is a crucial piece of information. Thank you for sharing it." / [38] "@Minako, I respect your caution. However, …"。冗長: 範囲外だが Misaki の [40] と [45] はほぼ同文 ("Let’s focus on the facts we have, not baseless suspicion." で終わる)。']))
P.append(excerpt('qwen','aiwolf_0008','multi-private-stepped','Day 1',34,40,[
 '[34] Takumi "Who did you check, Sakura? Tell us!" → Sakura の次の発話 [36] "I checked @Minako. She is human!" で回答 (占ったと言ったのは [31])。',
 '全発話 5–7 語。[37] "Thank you, Sakura. I appreciate the trust." の謝辞はあるが短く、同じ論点の言い直しはない。']))
open(R+'/progress_report_2026-10-29/examples.md','w').write('\n'.join(P))
