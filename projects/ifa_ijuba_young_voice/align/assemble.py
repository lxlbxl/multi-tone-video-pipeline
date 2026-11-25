"""Merge windowed alignments into one caption timeline, snapped to acoustic onsets.

usage: python3 assemble.py windows.json audio.wav edit_in.json edit_out.json
"""
import sys, json, wave
import numpy as np
win_p, wav_p, ein, eout = sys.argv[1:5]
W = json.load(open(win_p)); E = json.load(open(ein))
SRC = E['src_dur']

# ---- acoustic onset detector (voice band energy rising out of a dip) ----
w = wave.open(wav_p); sr = w.getframerate(); ch = w.getnchannels()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, ch).mean(1) / 32768
hop = int(sr * 0.01); win = int(sr * 0.03); nfft = 2048
F = np.fft.rfftfreq(nfft, 1 / sr); band = (F > 200) & (F < 3000); hw = np.hanning(win)
L = np.array([10 * np.log10((np.abs(np.fft.rfft(x[i:i + win] * hw, nfft)) ** 2)[band].sum() + 1e-10)
              for i in range(0, len(x) - win, hop)])
floor, top = np.percentile(L, 15), np.percentile(L, 97)
lo_thr = floor + 0.35 * (top - floor); hi_thr = floor + 0.6 * (top - floor)
onsets = []
for i in range(6, len(L) - 3):
    if L[i - 1] < hi_thr <= L[i] and L[i - 6:i].min() < lo_thr:
        # walk back to where the rise starts
        j = i
        while j > 0 and L[j - 1] < L[j] and L[j - 1] > lo_thr - 6: j -= 1
        onsets.append(j / 100)
onsets = np.array(sorted(set(onsets)))
def snap(t, tol=0.28):
    if not len(onsets): return t, False
    k = np.argmin(abs(onsets - t))
    return (float(onsets[k]), True) if abs(onsets[k] - t) <= tol else (t, False)

# ---- merge windows ----
lines = []
for wi, wd in enumerate(W):
    off = wd['off']
    for s, e, text, partial, words in wd['lines']:
        if text == 'INTRO': continue
        s += off; e += off
        is_last_window = wi == len(W) - 1
        if partial and not is_last_window: continue
        if lines and s < lines[-1]['end'] - 0.5: continue          # duplicate from overlap
        ws = [[t, ts + off] for t, ts in words]
        if lines and s < lines[-1]['end']:
            s = lines[-1]['end'] + 0.02; ws[0][1] = max(ws[0][1], s)
        lines.append({'start': s, 'end': min(e, SRC), 'text': text, 'words': ws})

# ---- snap line starts to acoustic onsets; shift words with the line ----
snapped = 0
for i, L_ in enumerate(lines):
    t, ok = snap(L_['start'])
    lo = (lines[i - 1]['words'][-1][1] + 0.12) if i else 0
    if ok and t > lo:
        d = t - L_['start']; snapped += 1
        L_['start'] = t
        for wv in L_['words']: wv[1] += d
        L_['words'][0][1] = t
        L_['end'] = max(L_['end'] + d, L_['words'][-1][1] + 0.15)
# keep strictly increasing + non-overlapping
for a, b in zip(lines, lines[1:]):
    a['end'] = min(a['end'], b['start'] - 0.02)

# ---- word end times ----
for L_ in lines:
    ws = L_['words']
    for k in range(len(ws)):
        end = ws[k + 1][1] if k + 1 < len(ws) else L_['end']
        ws[k].append(max(ws[k][1] + 0.08, end))

# ---- split long lines at commas for readability (max ~7 words) ----
out = []
for L_ in lines:
    ws = L_['words']
    while len(ws) > 9:
        cut = None
        for k in range(3, min(len(ws) - 2, 9) + 1):
            if ws[k - 1][0].endswith(','): cut = k
        if cut is None: cut = (len(ws) + 1) // 2
        out.append(ws[:cut]); ws = ws[cut:]
    out.append(ws)
# pacing: fold sub-0.75s fragments into a neighbour when it stays readable
def dur(ws): return ws[-1][2] - ws[0][1]
def is_ase(ws): return ws[0][0].startswith('Àṣẹ')
def opener(ws): return ws[0][0].startswith('Ìbà')
changed = True
while changed:
    changed = False
    for k in range(len(out)):
        a = out[k]
        if dur(a) >= 0.75 or is_ase(a): continue
        if k > 0 and not is_ase(out[k-1]) and not opener(a) and len(out[k-1]) + len(a) <= 9 and a[0][1] - out[k-1][-1][2] < 0.35:
            out[k-1] = out[k-1] + a; del out[k]; changed = True; break
        if k + 1 < len(out) and not is_ase(out[k+1]) and not opener(out[k+1]) and len(a) + len(out[k+1]) <= 9 and out[k+1][0][1] - a[-1][2] < 0.35:
            out[k] = a + out[k+1]; del out[k+1]; changed = True; break
# no caption may run into the next one
for a, b in zip(out, out[1:]):
    lim = b[0][1] - 0.02
    for wv in a:
        wv[2] = min(wv[2], lim); wv[1] = min(wv[1], lim - 0.05)
caps = [[round(ws[0][1], 3), round(ws[-1][2], 3), ' '.join(w[0] for w in ws).rstrip('.'),
         [[round(w[1], 3), round(w[2], 3)] for w in ws]] for ws in out]

# ---- sections + ÀṢẸ from line text ----
def first(pred):
    for c in caps:
        if pred(c[2]): return c[0]
    raise SystemExit('section not found')
low = lambda s: s.lower()
sec_def = [
 ("Olódùmarè", "The Supreme Being", "sun", None),
 ("Ilẹ̀", "Earth · Olódùmarè's footstool", "earth", lambda s: low(s).startswith('ìbà o, ilẹ̀')),
 ("Ayé", "The World · its days, nights & winds", "world", lambda s: low(s).startswith('ìbà ọ̀run òkè')),
 ("Ẹ̀là", "Ẹ̀là wòrò · Agbẹ́gilérè", "tree", lambda s: low(s).startswith('ìbà ẹ̀là')),
 ("Ọ̀rúnmìlà", "Ẹlẹ́rìí ìpín · witness of destiny", "opon", lambda s: low(s).startswith('ìbà ọ̀rúnmìlà')),
 ("Agbọnnìrègún", "Ọ̀rúnmìlà · Ifá", "ikin", lambda s: low(s).startswith('ìbà o, agbọnnìrègún')),
 ("Ìyá mi", "Òṣòròngà · the Mothers", "bird", lambda s: low(s).startswith('ìbà o, àwọn ìyá mi')),
 ("Odù", "Ológbòòjè", "gourd", lambda s: low(s).startswith('ìbà o, odù')),
 ("Ọbàtálá", "Òrìṣàálá · Òṣèèrègbo", "snail", lambda s: low(s).startswith('ìbà o, òrìṣàálá')),
 ("Ọ̀ṣun", "Àwúra-olú", "fan", lambda s: low(s).startswith('ìbà o, ọ̀ṣun')),
 ("Ṣàngó", "Olúkòso · ọkọ Ọya", "axe", lambda s: low(s).startswith('ìbà o, olúkòso')),
]
sections = []
for name, sub, ic, pred in sec_def:
    st = 3.5 if pred is None else first(pred)
    sections.append({'start': round(st, 3), 'name': name, 'sub': sub, 'icon': ic})
ase = [c[0] for c in caps if c[2].startswith('Àṣẹ')]
E2 = dict(E); E2['lines'] = caps; E2['sections'] = sections; E2['ase'] = ase
json.dump(E2, open(eout, 'w'), ensure_ascii=False, indent=1)
print(f'{len(caps)} caption lines, {snapped}/{len(lines)} line starts snapped to onsets, {len(onsets)} onsets')
print('ÀṢẸ:', ase)
print('sections:', [(s['name'], s['start']) for s in sections])
gaps = [b[0] - a[1] for a, b in zip(caps, caps[1:])]
dur = [c[1] - c[0] for c in caps]
print(f'line durations: min {min(dur):.2f} median {np.median(dur):.2f} max {max(dur):.2f}; overlaps: {sum(g < 0 for g in gaps)}')
