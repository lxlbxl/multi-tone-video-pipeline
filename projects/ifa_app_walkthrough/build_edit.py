"""Timeline + word-timed captions for the IFA.ng app video."""
import json, re, unicodedata, sys
def syl(w):
    if 'IFA.ng' in w: return 4
    b = ''.join(c for c in unicodedata.normalize('NFD', w) if not unicodedata.combining(c)).lower()
    return max(1, len(re.findall(r'[aeiouy]+', b)))
# clip -> (global start, [(phrase start, phrase end, caption text)])
VO = {
 1: (0.40, [(0.03, 1.40, "You've got a question…"), (1.78, 3.28, "only Ifá can answer."), (3.57, 4.94, "But the nearest Babaláwo?"), (5.25, 6.17, "Miles away."), (6.44, 7.58, "Days of waiting.")]),
 2: (8.70, [(0.03, 4.22, "Not anymore! IFA.ng puts a verified Babaláwo…"), (4.40, 5.85, "right in your pocket.")]),
 3: (15.70, [(0.03, 0.72, "Step one:"), (1.11, 2.38, "tell us what's on your mind."), (2.73, 5.49, "Your concern. Your language. Your budget.")]),
 4: (22.50, [(0.03, 0.76, "Step two:"), (1.05, 3.10, "pick your Babaláwo or Ìyánífá."), (3.45, 5.53, "Every single one is verified."), (5.79, 8.37, "Compare languages, specialties and fees…"), (8.58, 10.08, "all shown up front.")]),
 5: (33.60, [(0.03, 0.88, "Step three:"), (1.06, 4.92, "sign in with just your phone, pick a time, and pay securely."), (5.16, 8.12, "Your Google Meet link arrives as soon as payment clears."), (8.34, 9.45, "Nothing to install!")]),
 6: (44.40, [(0.03, 0.92, "Step four:"), (1.31, 2.37, "after your reading,"), (2.63, 3.62, "keep your notes."), (4.03, 4.79, "Your Odù."), (5.25, 6.02, "Your ẹbọ."), (6.43, 7.35, "What to gather."), (7.69, 9.34, "Approved by your Babaláwo,"), (9.54, 10.75, "and saved for you.")]),
 7: (56.30, [(0.03, 0.88, "New to Ifá?"), (1.26, 3.63, "Explore the sixteen principal Odù…"), (3.87, 5.56, "before you even consult.")]),
 8: (63.10, [(0.03, 1.04, "From Lagos…"), (1.27, 1.99, "to London…"), (2.22, 3.09, "to Houston."), (3.42, 4.51, "Wherever you are…"), (4.83, 6.20, "hear Ifá speak."), (6.63, 8.14, "IFA.ng."), (8.60, 9.16, "Àṣẹ!")]),
}
words = []
for k, (g0, phr) in VO.items():
    for a, b, text in phr:
        ws = text.split(); n = [syl(w) + (0.5 if re.search(r'[,.!?…:]$', w) else 0) for w in ws]; tot = sum(n); t = a
        for w, s in zip(ws, n):
            d = (b - a) * s / tot; words.append([w, round(g0 + t, 3), round(g0 + t + d, 3), k]); t += d
chunks, cur = [], []
for i, w in enumerate(words):
    cur.append(w); nxt = words[i + 1] if i + 1 < len(words) else None
    if nxt is None or nxt[3] != w[3] or re.search(r'[.!?…:]$', w[0]) or (nxt and nxt[1] - w[2] > .3) or (w[0].endswith(',') and len(cur) >= 3):
        chunks.append(cur); cur = []
lines = []
for c in chunks:
    while len(c) > 6:
        h = (len(c) + 1) // 2; lines.append(c[:h]); c = c[h:]
    lines.append(c)
caps = [[l[0][1], l[-1][2], ' '.join(x[0] for x in l), [[x[1], x[2]] for x in l]] for l in lines]
def at(word, clip, nth=0):
    hits = [w for w in words if w[3] == clip and w[0].strip(',.!?…:').lower() == word.lower()]
    return hits[nth][1]
cues = {k: at(*v) for k, v in {
  'q_only': ('only', 1), 'miles': ('Miles', 1), 'days': ('Days', 1),
  'notanymore': ('Not', 2), 'pocket': ('pocket', 2),
  'concern': ('concern', 3), 'language': ('language', 3), 'budget': ('budget', 3),
  'pick2': ('pick', 4), 'verified': ('verified', 4), 'compare': ('Compare', 4), 'fees': ('fees', 4), 'upfront': ('up', 4),
  'signin': ('sign', 5), 'picktime': ('pick', 5), 'pay': ('pay', 5), 'meet': ('Google', 5), 'install': ('Nothing', 5),
  'reading': ('after', 6), 'notes': ('keep', 6), 'odu': ('Odù', 6), 'ebo': ('ẹbọ', 6), 'gather': ('gather', 6), 'approved': ('Approved', 6), 'saved': ('saved', 6),
  'newto': ('New', 7), 'sixteen': ('sixteen', 7),
  'lagos': ('Lagos', 8), 'london': ('London', 8), 'houston': ('Houston', 8), 'wherever': ('Wherever', 8), 'hear': ('hear', 8), 'brand': ('IFA.ng', 8), 'ase': ('Àṣẹ', 8),
}.items()}
cues.update({'s1': 15.25, 's2': 22.05, 's3': 33.15, 's4': 43.95, 'learn': 55.85, 'cta': 62.7, 'end': 72.5, 'reveal': 8.35})
variant = sys.argv[1] if len(sys.argv) > 1 else 'evergreen'
E = {'total': 78.0, 'src_dur': 78.0, 'outro': 0, 'vo': {k: v[0] for k, v in VO.items()}, 'lines': caps, 'cues': cues, 'variant': variant}
json.dump(E, open('build/edit.json', 'w'), ensure_ascii=False, indent=1)
for c in caps: print(f"{c[0]:6.2f}-{c[1]:6.2f} {c[2]}")
print(cues)
