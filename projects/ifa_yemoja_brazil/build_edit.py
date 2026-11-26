import json, re, unicodedata
def syl(w):
    b=''.join(c for c in unicodedata.normalize('NFD',w) if not unicodedata.combining(c)).lower()
    return max(1,len(re.findall(r'[aeiouy]+',b)))
VO = {  # clip: (global start, [(phrase_start, phrase_end, text), ...])  — phrase spans from silencedetect
 1:(0.30,[(0.05,2.13,"Wait… this is not Lagos."),(2.57,3.80,"This is BRAZIL!")]),
 2:(5.00,[(0.05,3.11,"That giant goddess pouring water over the crowd?"),(3.51,5.06,"That is Yemọja."),(5.48,6.56,"OUR Yemọja."),(7.00,9.25,"The Yoruba mother of the waters.")]),
 3:(15.20,[(0.05,2.86,"Her home is the Ògùn River, in Nigeria."),(3.24,8.42,"But centuries ago, our ancestors were chained and carried across the Atlantic…"),(8.93,10.28,"and they carried her with them."),(10.88,11.81,"In their songs."),(12.23,13.25,"In their prayers.")]),
 4:(29.60,[(0.05,1.49,"They lost their names."),(1.77,2.72,"Their land."),(2.97,4.58,"Almost everything."),(5.31,7.50,"But they never let go of Yemọja.")]),
 5:(38.60,[(0.05,7.55,"And today? Brazil throws her a carnival! Water pouring like a river… and a whole stadium on its feet!")]),
 6:(47.80,[(0.05,0.75,"So tell me…"),(1.23,4.48,"if the world can celebrate our heritage this loudly,"),(5.07,6.79,"why should we ever whisper it?"),(7.31,15.99,"Yorùbá, wherever you are… Lagos, London, Houston, Bahia… speak the language. Wear it. Teach your children."),(16.19,19.98,"Be proud of who you are! Ẹ jẹ́ ká gbé àṣà wa ga!"),(20.55,21.04,"Àṣẹ!")]),
}
words=[]
for k,(g0,phr) in VO.items():
    for a,b,text in phr:
        ws=text.split(); n=[syl(w)+(0.6 if re.search(r'[,.!?…]$',w) else 0) for w in ws]; tot=sum(n); t=a
        for w,s in zip(ws,n):
            d=(b-a)*s/tot; words.append([w,round(g0+t,3),round(g0+t+d,3),k]); t+=d
# caption lines: break at sentence ends / commas, max 6 words
chunks=[]; cur=[]
for i,w in enumerate(words):
    cur.append(w); nxt=words[i+1] if i+1<len(words) else None
    if nxt is None or nxt[3]!=w[3] or re.search(r'[.!?…]$',w[0]) or (nxt and nxt[1]-w[2]>0.3) or (re.search(r',$',w[0]) and len(cur)>=4):
        chunks.append(cur); cur=[]
lines=[]
for c in chunks:
    while len(c)>7:
        h=(len(c)+1)//2; lines.append(c[:h]); c=c[h:]
    lines.append(c)
caps=[[l[0][1],l[-1][2],' '.join(x[0] for x in l),[[x[1],x[2]] for x in l]] for l in lines]
def at(word, clip, nth=0):
    hits=[w for w in words if w[3]==clip and w[0].strip(',.!?…').lower()==word.lower()]
    return hits[nth][1]
cues={
 'brazil': at('BRAZIL',1), 'yemoja1': at('Yemọja',2), 'our': at('OUR',2),
 'ogun': at('Ògùn',3), 'atlantic': at('Atlantic',3), 'carried2': at('carried',3,1),
 'lost': at('lost',4), 'never': at('never',4),
 'today': at('today',5), 'water': at('Water',5), 'stadium': at('stadium',5),
 'world': at('world',6), 'whisper': at('whisper',6), 'yoruba': at('Yorùbá',6),
 'lagos': at('Lagos',6), 'london': at('London',6), 'houston': at('Houston',6), 'bahia': at('Bahia',6),
 'speak': at('speak',6), 'wear': at('Wear',6), 'teach': at('Teach',6),
 'proud': at('Be',6), 'eje': at('Ẹ',6), 'ase': at('Àṣẹ',6),
}
E={'total':73.5,'vo':{k:v[0] for k,v in VO.items()},'lines':caps,'cues':cues,'replay_start':51.37}
json.dump(E,open('build/edit.json','w'),ensure_ascii=False,indent=1)
for c in caps: print(f"{c[0]:6.2f}-{c[1]:6.2f} {c[2]}")
print(cues)
