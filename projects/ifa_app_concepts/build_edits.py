import json, re, unicodedata, sys
def syl(w):
    if 'IFA.ng' in w: return 4
    b = ''.join(c for c in unicodedata.normalize('NFD', w) if not unicodedata.combining(c)).lower()
    return max(1, len(re.findall(r'[aeiouy]+', b)))
def words_of(VO):
    out = []
    for k, (g0, phr) in VO.items():
        for a, b, text in phr:
            ws = text.split(); n = [syl(w) + (0.5 if re.search(r'[,.!?…:]$', w) else 0) for w in ws]; tot = sum(n); t = a
            for w, s in zip(ws, n):
                d = (b - a) * s / tot; out.append([w, round(g0 + t, 3), round(g0 + t + d, 3), k]); t += d
    return out
def lines_of(words):
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(w); nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None or nxt[3] != w[3] or re.search(r'[.!?…:]$', w[0]) or (nxt and nxt[1] - w[2] > .3):
            chunks.append(cur); cur = []
    return [[c[0][1], c[-1][2], ' '.join(x[0] for x in c), [[x[1], x[2]] for x in c]] for c in chunks]
variant = sys.argv[1] if len(sys.argv) > 1 else 'evergreen'
# ---------- A: The Cast ----------
VA = {
 'A1': (1.0,  [(0.03, 1.43, "For centuries…"), (2.04, 4.33, "Ifá has spoken through the ọpọ́n.")]),
 'A2': (6.6,  [(0.03, 0.96, "Today…"), (1.30, 3.50, "the ọpọ́n fits in your hand.")]),
 'A3': (11.2, [(0.03, 1.22, "The first mark."), (1.75, 3.56, "Share what is on your mind.")]),
 'A4': (16.0, [(0.03, 1.23, "The second mark."), (1.80, 4.38, "Choose your Babaláwo or Ìyánífá."), (4.99, 5.79, "Every one…"), (6.18, 6.88, "verified.")]),
 'A5': (24.2, [(0.03, 1.12, "The third mark."), (1.70, 3.58, "Sit together on Google Meet…"), (3.81, 5.50, "from anywhere in the world.")]),
 'A6': (30.8, [(0.03, 1.09, "The fourth mark."), (1.66, 2.32, "Your Odù."), (2.84, 3.51, "Your ẹbọ."), (4.09, 4.84, "Your path…"), (5.25, 6.08, "written down,"), (6.33, 7.30, "and approved.")]),
 'A7': (39.6, [(0.19, 2.29, "The cast is complete."), (2.96, 4.46, "Hear Ifá speak."), (4.95, 6.44, "IFA.ng.")]),
}
wa = words_of(VA); la = lines_of(wa)
def at(words, w, clip, nth=0): return [x for x in words if x[3] == clip and x[0].strip(',.!?…:').lower() == w.lower()][nth][1]
QA = {'m1': 11.2, 'm2': 16.0, 'm3': 24.2, 'm4': 30.8, 'complete': 39.79, 'hear': at(wa, 'Hear', 'A7'), 'brand': at(wa, 'IFA.ng', 'A7'), 'end': 47.0, 'window': 6.6,
      'verified': at(wa, 'verified', 'A4'), 'meet': at(wa, 'Google', 'A5'), 'anywhere': at(wa, 'anywhere', 'A5'), 'odu': at(wa, 'Odù', 'A6'), 'ebo': at(wa, 'ẹbọ', 'A6'), 'path': at(wa, 'path', 'A6'), 'approved': at(wa, 'approved', 'A6'), 'choose': at(wa, 'Choose', 'A4')}
json.dump({'total': 52.5, 'src_dur': 52.5, 'outro': 0, 'vo': {k: v[0] for k, v in VA.items()}, 'lines': la, 'cues': QA, 'variant': variant}, open('A/edit.json', 'w'), ensure_ascii=False, indent=1)
# ---------- B: Voice Note ----------
VB = {
 'B1': (1.6,  [(0.03, 6.40, "Mummy! I need to consult a Babaláwo about this new job offer… but I'm in London! What do I do?")]),
 'B2': (10.6, [(0.03, 0.54, "Ah,"), (0.80, 3.68, "my daughter, calm down."), (4.16, 5.77, "Use IFA.ng."), (6.29, 10.04, "You can consult a verified Babaláwo online, on Google Meet."), (10.44, 11.13, "Let me show you.")]),
 'B3': (37.6, [(0.03, 0.55, "Ehn!"), (0.75, 2.07, "No app to install?"), (2.29, 6.92, "And I keep the notes? Mummy, you're too sharp! I'm booking now!")]),
 'B4': (47.4, [(0.03, 0.75, "Àṣẹ o!"), (1.14, 2.80, "Greet the Babaláwo for me.")]),
}
wb = words_of(VB)
json.dump({'total': 56.0, 'src_dur': 56.0, 'outro': 0, 'vo': {k: v[0] for k, v in VB.items()}, 'vowords': {k: [[w[0], w[1], w[2]] for w in wb if w[3] == k] for k in VB}, 'vodur': {'B1': 6.43, 'B2': 11.47, 'B3': 7.24, 'B4': 2.85}, 'cues': {'end': 50.4}, 'variant': variant}, open('B/edit.json', 'w'), ensure_ascii=False, indent=1)
print('A lines'); [print(f"  {l[0]:6.2f} {l[2]}") for l in la]; print('A cues', QA)
