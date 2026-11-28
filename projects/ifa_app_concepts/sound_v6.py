"""Soundtracks for Concept A ("The Cast") and Concept B ("Voice Note"), both built on the real ifa.ng chant audio.
usage: python3 sound_v6.py A|B edit.json vo_dir chant.wav out.wav
"""
import sys, json, wave, subprocess
import numpy as np
which, ein, vo_dir, chant_p, out = sys.argv[1:6]
E = json.load(open(ein)); T = E['total']; SR = 44100; N = int(T * SR); t = np.arange(N) / SR
rng = np.random.default_rng(21)
def dec(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768
def place(buf, sig, at, g=1.0):
    i = int(at * SR)
    if i < 0: sig = sig[-i:]; i = 0
    if i >= len(buf): return
    j = min(len(buf), i + len(sig)); buf[i:j] += g * sig[:j - i]
def lp(x, a):
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s += a * (x[i] - s); y[i] = s
    return y
def noise(d): return rng.standard_normal(int(d * SR)).astype(np.float32)
def reverb(x, dur=2.6, mix=.45):
    ir = noise(dur) * np.exp(-np.arange(int(dur * SR)) / SR * 2.4); ir = lp(ir, .2); ir /= np.abs(ir).sum() ** .5 * 6
    n = 1 << int(np.ceil(np.log2(len(x) + len(ir))))
    wet = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[:len(x)].astype(np.float32)
    wet *= np.abs(x).max() / (np.abs(wet).max() + 1e-9)
    return x * (1 - mix) + wet * mix
def whoosh(d=.5, bright=.35):
    x = noise(d); y = np.zeros_like(x); s = 0
    for i in range(len(x)): s += (0.02 + bright * i / len(x)) * (x[i] - s); y[i] = s
    tt = np.arange(len(x)) / SR; return (y * np.sin(np.pi * tt / d) ** 2 / (np.abs(y).max() + 1e-9)).astype(np.float32)
def boom(d=1.6, f0=48):
    tt = np.arange(int(d * SR)) / SR; f = f0 + 60 * np.exp(-tt * 8)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.6)).astype(np.float32)
def bell(f=880, d=2.4):   # àgogò-like metallic bell (inharmonic partials)
    tt = np.arange(int(d * SR)) / SR
    return (sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * dk) for r, a, dk in [(1, 1, 2.2), (2.76, .5, 3.5), (5.4, .25, 6), (8.9, .12, 9)]) / 1.9).astype(np.float32)
def shimmer(d=1.8):
    s = np.zeros(int(d * SR), np.float32)
    for k, f in enumerate([1318.5, 1567.98, 1975.5, 2637.0]):
        o = int(k * .07 * SR); tt = np.arange(len(s) - o) / SR; s[o:] += (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2.6) * .26).astype(np.float32)
    return s
def ding(f, d=.8, b=2):
    tt = np.arange(int(d * SR)) / SR; return ((np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * 2.01 * f * tt)) * np.exp(-tt * (4 + b)) / 1.4).astype(np.float32)
def pop():
    tt = np.arange(int(.14 * SR)) / SR; f = 900 * np.exp(-tt * 18) + 260
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 26)).astype(np.float32)
def tick():
    x = noise(.025); return ((x - lp(x, .4)) * np.exp(-np.arange(len(x)) / SR * 260) * .6).astype(np.float32)
def beep(f=1200, d=.09):
    tt = np.arange(int(d * SR)) / SR; return (np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / d)).astype(np.float32)

chant = dec(chant_p)
vo = np.zeros(N, np.float32)
for k, g in E['vo'].items():
    v = dec(f'{vo_dir}/{k}.mp3'); act = v[np.abs(v) > .02]; v *= .12 / (np.sqrt((act ** 2).mean()) + 1e-9)   # equal loudness per clip
    place(vo, v, g)
w = int(.15 * SR); venv = np.convolve(np.abs(vo), np.ones(w) / w, 'same')
talk = np.clip(venv / (np.percentile(venv[venv > 1e-4], 60) + 1e-9), 0, 1)
talk = np.convolve(talk, np.ones(int(.3 * SR)) / int(.3 * SR), 'same')
fx = np.zeros(N, np.float32); bed = np.zeros(N, np.float32)
Q = E['cues']

if which == 'A':
    # hushed, reverberant chant bed for the whole piece; it comes forward for the finale
    seg = chant[:N].copy() if len(chant) >= N else np.pad(chant, (0, N - len(chant)))
    seg = reverb(lp(seg, .12) * 1.6, 3.0, .6)
    place(bed, seg, 0)
    lvl = .35 + .65 * np.clip((t - Q['complete'] + .5) / 1.5, 0, 1)
    bed *= lvl * np.clip(t / 2.0, 0, 1) * np.clip((T - t) / 2.5, 0, 1)
    place(fx, boom(2.4, 40), .2, .6)                       # the board rises from darkness
    place(fx, whoosh(1.2, .15), Q['window'] - .3, .35); place(fx, shimmer(2.2), Q['window'] + .1, .25)
    for i, k in enumerate(['m1', 'm2', 'm3', 'm4']):
        place(fx, boom(1.6, 44), Q[k] + .05, .75); place(fx, bell([784, 880, 988, 1046.5][i], 2.6), Q[k] + .1, .3); place(fx, shimmer(1.4), Q[k] + .2, .18)
    place(fx, bell(523.25, 3.5), Q['complete'], .35); place(fx, bell(659.25, 3.5), Q['complete'] + .12, .28); place(fx, boom(3.0, 36), Q['complete'], .9)
    place(fx, shimmer(2.4), Q['hear'], .25); place(fx, bell(1046.5, 2.5), Q['brand'], .2); place(fx, bell(783.99, 3.0), Q['end'] + .1, .25)
    mix = vo * 1.05 + bed * .55 * (1 - .4 * talk) + fx * .5
else:
    # chant as a light background vibe, swelling on the end card
    seg = chant[int(2 * SR):int(2 * SR) + N]; seg = np.pad(seg, (0, max(0, N - len(seg))))
    place(bed, lp(seg, .25), 0)
    bed *= (.6 + .4 * np.clip((t - Q['end'] + .3) / 1.2, 0, 1)) * np.clip(t / 1.5, 0, 1) * np.clip((T - t) / 2.0, 0, 1)
    # message sounds
    sends = [.5, E['vo']['B1'] - .25, 36.6, E['vo']['B3'] - .25, 45.2, 46.3]
    recv = [9.9, E['vo']['B2'] - .25, 22.7, 26.0, 29.4, 32.9, E['vo']['B4'] - .25]
    for s in sends: place(fx, whoosh(.22, .6), s - .12, .25); place(fx, pop(), s, .35)
    for r in recv: place(fx, ding(1318.5, .5, 4), r, .3); place(fx, ding(1760, .5, 4), r + .08, .22)
    for i in range(7): place(fx, tick(), 9.0 + i * .13, .3)
    for k in ['B1', 'B3']: place(fx, beep(1400), E['vo'][k] - 1.35, .3); place(fx, beep(900), E['vo'][k] - .3, .3)
    for at in [22.7, 26.0, 29.4, 32.9]: place(fx, whoosh(.35, .4), at + .62, .3); place(fx, tick(), at + .7, .5)
    place(fx, pop(), 36.2, .35); place(fx, pop(), 50.0, .35)
    place(fx, ding(783.99, 2.0, 1), Q['end'] + .1, .25); place(fx, ding(1174.66, 2.0, 1), Q['end'] + .55, .2)
    mix = vo * 1.0 + bed * .6 * (1 - .6 * talk) + fx * .5
mix /= max(1.0, np.abs(mix).max() / .98)
wv = wave.open(out, 'wb'); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((mix * 32767).astype(np.int16).tobytes()); wv.close()
print('ok', which, T)
