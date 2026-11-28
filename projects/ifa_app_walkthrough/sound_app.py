"""Soundtrack for the IFA.ng app video: synthesized afro-pop groove, UI sounds, VO, and the real ifa.ng hero chant.
usage: python3 sound_app.py edit.json vo_dir chant.wav out.wav
"""
import sys, json, wave, subprocess
import numpy as np
ein, vo_dir, chant_p, out = sys.argv[1:5]
E = json.load(open(ein)); Q = E['cues']; T = E['total']; SR = 44100; N = int(T * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)
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
def ar(n, a, r): e = np.ones(n, np.float32); A = max(1, int(a * SR)); R = max(1, int(r * SR)); e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R); return e

# ---------------- instruments ----------------
def kick():
    tt = np.arange(int(.35 * SR)) / SR; f = 48 + 90 * np.exp(-tt * 30)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)).astype(np.float32)
def clap():
    x = noise(.18); x = x - lp(x, .25); tt = np.arange(len(x)) / SR
    env = np.exp(-tt * 28) + .6 * np.exp(-np.maximum(tt - .012, 0) * 30) * (tt > .012)
    return (x * env * .5).astype(np.float32)
def shaker():
    x = noise(.06); x = x - lp(x, .5); tt = np.arange(len(x)) / SR
    return (x * np.exp(-tt * 70) * .25).astype(np.float32)
def talk(f0=220, d=.22, bend=1.35):   # talking-drum style pitch bend
    tt = np.arange(int(d * SR)) / SR; f = f0 * (1 + (bend - 1) * np.exp(-tt * 18))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 14) * (1 - np.exp(-tt * 400))).astype(np.float32)
def bassnote(f, d):
    tt = np.arange(int(d * SR)) / SR
    s = np.sin(2 * np.pi * f * tt) + .35 * np.sin(2 * np.pi * 2 * f * tt) + .15 * np.sin(2 * np.pi * 3 * f * tt)
    return (s * ar(len(tt), .005, .08) * .55).astype(np.float32)
def pluck(f, d=.35):
    tt = np.arange(int(d * SR)) / SR
    return ((np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 9) * .25).astype(np.float32)

# ---------------- groove (108 bpm) ----------------
BPM = 108; beat = 60 / BPM; bar = 4 * beat
g0, g1 = Q['reveal'] + .35, Q['cta'] + 1.5
groove = np.zeros(N, np.float32)
chords = [(110.0, [440, 523.25, 659.25]), (87.31, [349.23, 440, 523.25]), (130.81, [523.25, 659.25, 783.99]), (98.0, [392, 493.88, 587.33])]  # Am F C G
nb = int((g1 - g0) / bar) + 1
for b in range(nb):
    t0 = g0 + b * bar
    root, tri = chords[b % 4]
    for k in [0, 1.5, 2, 3.5] if b % 2 else [0, 1.5, 2.5]:
        place(groove, kick(), t0 + k * beat, .9)
    for k in [1, 3]: place(groove, clap(), t0 + k * beat, .55)
    for k in range(16): place(groove, shaker(), t0 + k * beat / 4, .6 if k % 2 else .35)
    for k, m in [(0, 1), (1.5, 1), (2, 1.5), (3, 1)]: place(groove, bassnote(root * m, beat * .9), t0 + k * beat, .55)
    for k, i in [(.5, 0), (1, 1), (2.5, 2), (3, 1)]: place(groove, pluck(tri[i]), t0 + k * beat, .35)
    if b % 2 == 1:   # talking-drum answer phrase every two bars
        for k, f in [(2.75, 260), (3.0, 200), (3.25, 300), (3.5, 220), (3.75, 180)]: place(groove, talk(f), t0 + k * beat, .45)
# learn scene: groove muffled; CTA: groove fades as the chant rises
lw = np.clip(np.minimum((t - Q['learn']) / .3, (Q['cta'] - t) / .3), 0, 1)
groove = groove * (1 - lw) + lp(groove, .06) * lw * 1.3
groove *= np.clip((t - g0) / .2, 0, 1) * np.clip((Q['cta'] + 1.4 - t) / 1.4, 0, 1)

# ---------------- hook bed ----------------
hook = np.zeros(N, np.float32)
dt = np.arange(int(Q['reveal'] * SR)) / SR
drone = (np.sin(2 * np.pi * 55 * dt) + .5 * np.sin(2 * np.pi * 82.4 * dt)) * np.clip(dt / 1.5, 0, 1) * .25
place(hook, drone.astype(np.float32), 0)
tick = (np.sin(2 * np.pi * 2200 * np.arange(int(.03 * SR)) / SR) * np.exp(-np.arange(int(.03 * SR)) / SR * 200)).astype(np.float32)
tt = 0.4
while tt < Q['reveal'] - .1: place(hook, tick, tt, .25); tt += .5
for i in range(10): place(hook, (noise(.05) * np.exp(-np.arange(int(.05 * SR)) / SR * 80)).astype(np.float32), Q['days'] + i / 6, .18)   # calendar flicks

# ---------------- SFX ----------------
fx = np.zeros(N, np.float32)
def whoosh(d=.5, bright=.35):
    x = noise(d); y = np.zeros_like(x); s = 0
    for i in range(len(x)): s += (0.02 + bright * i / len(x)) * (x[i] - s); y[i] = s
    tt = np.arange(len(x)) / SR; return (y * np.sin(np.pi * tt / d) ** 2 / (np.abs(y).max() + 1e-9)).astype(np.float32)
def riser(d=1.0):
    tt = np.arange(int(d * SR)) / SR; f = 150 * (6 ** (tt / d))
    return ((np.sin(2 * np.pi * np.cumsum(f) / SR) * .35 + whoosh(d, .5) * .7) * (tt / d) ** 2).astype(np.float32)
def boom(d=1.4, f0=52):
    tt = np.arange(int(d * SR)) / SR; f = f0 + 70 * np.exp(-tt * 9)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3)).astype(np.float32)
def ding(f, d=1.0, b=1.0):
    tt = np.arange(int(d * SR)) / SR
    return ((np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * f * 2.01 * tt)) * np.exp(-tt * (4 + b)) / 1.4).astype(np.float32)
def pop():
    tt = np.arange(int(.15 * SR)) / SR; f = 900 * np.exp(-tt * 18) + 260
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 24)).astype(np.float32)
def click():
    x = noise(.02); return ((x - lp(x, .4)) * np.exp(-np.arange(len(x)) / SR * 300) * .8).astype(np.float32)
def key():
    x = noise(.03); return ((x - lp(x, .3)) * np.exp(-np.arange(len(x)) / SR * 220) * .5).astype(np.float32)
def shimmer(d=1.6):
    s = np.zeros(int(d * SR), np.float32)
    for k, f in enumerate([1318.5, 1567.98, 1975.5, 2637.0]):
        o = int(k * .06 * SR); tt = np.arange(len(s) - o) / SR; s[o:] += (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3) * .28).astype(np.float32)
    return s
def thud():
    tt = np.arange(int(.4 * SR)) / SR; return (np.sin(2 * np.pi * (70 + 60 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 10) + noise(.4)[:len(tt)] * np.exp(-tt * 40) * .3).astype(np.float32)

place(fx, whoosh(.5), .1, .3)
place(fx, whoosh(.9, .2), Q['miles'] - .3, .35)
place(fx, riser(1.0), Q['reveal'] - 1.0, .35); place(fx, boom(), Q['reveal'] + .05, .8); place(fx, shimmer(), Q['reveal'] + .1, .3)
place(fx, pop(), Q['notanymore'] + 2.4, .3); place(fx, pop(), Q['pocket'], .35)
for s in ['s1', 's2', 's3', 's4']:
    place(fx, whoosh(.45), Q[s] - .3, .4); place(fx, boom(.9, 60), Q[s], .65); place(fx, ding(880 if s != 's4' else 1046.5, .8), Q[s] + .05, .15)
for c in ['concern', 'language', 'budget', 'verified', 'fees', 'upfront', 'picktime', 'pay', 'saved']: place(fx, pop(), Q[c], .35)
place(fx, pop(), Q['compare'] + .2, .3); place(fx, pop(), Q['compare'] + .7, .3); place(fx, pop(), Q['signin'] + .2, .3)
place(fx, click(), Q['pick2'] - .2, .6); place(fx, click(), Q['compare'] - .4, .6); place(fx, click(), Q['signin'] + 1.9, .6)
for i in range(13): place(fx, key(), Q['pick2'] + .1 + i * (1.9 / 13), .45)
for i in range(10): place(fx, key(), Q['signin'] + .3 + i * .14, .45)
place(fx, ding(1318.5, .5, 3), Q['meet'] + .25, .25); place(fx, ding(1760, .7, 3), Q['meet'] + .38, .2)
place(fx, thud(), Q['install'], .6); place(fx, thud(), Q['approved'], .55); place(fx, shimmer(1.2), Q['approved'] + .05, .2)
for c in ['odu', 'ebo', 'gather']: place(fx, ding(1046.5, .5, 3), Q[c], .15)
for i in range(4): place(fx, whoosh(.3, .5), Q['newto'] + .3 + i * .35 - .1, .3)
place(fx, boom(1.2), Q['learn'], .4)
for c in ['lagos', 'london', 'houston']: place(fx, pop(), Q[c], .3)
place(fx, shimmer(2.0), Q['hear'], .25); place(fx, riser(.7), Q['ase'] - .7, .3); place(fx, boom(2.0, 45), Q['ase'], .9)
place(fx, ding(783.99, 2.2), Q['end'] + .1, .2)

# ---------------- real chant from the ifa.ng hero video ----------------
chant = dec(chant_p)
ch = np.zeros(N, np.float32)
seg = chant[int(16.4 * SR):int((16.4 + (T - Q['cta'] + .5)) * SR)]   # pause, then the clean verse+chorus (17.8-31.5 s): no speech
place(ch, seg, Q['cta'] - .1)
seg2 = chant[int(1.0 * SR):int((1.0 + (Q['s1'] - Q['reveal'] + .5)) * SR)]   # faint under the in-phone hero
place(ch, seg2 * .35, Q['reveal'])
ch_env = np.clip(np.minimum((t - Q['cta']) / 1.2, 1), 0, 1) + np.clip((t > Q['reveal']) & (t < Q['s1'] + .4), 0, 1) * 1.0
ch *= np.clip(ch_env, 0, 1) * np.clip((T - t) / 2.0, 0, 1)

# ---------------- VO + ducking ----------------
vo = np.zeros(N, np.float32)
for k, g in E['vo'].items(): place(vo, dec(f'{vo_dir}/vo{k}.mp3'), g)
w = int(.15 * SR); venv = np.convolve(np.abs(vo), np.ones(w) / w, 'same')
talkc = np.clip(venv / (np.percentile(venv[venv > 1e-4], 60) + 1e-9), 0, 1)
talkc = np.convolve(talkc, np.ones(int(.3 * SR)) / int(.3 * SR), 'same')
duck = 1 - .6 * talkc
mix = vo * 1.0 + groove * .32 * duck + hook * .5 + fx * .45 + ch * .75 * (1 - .45 * talkc)
mix /= max(1.0, np.abs(mix).max() / .98)
wv = wave.open(out, 'wb'); wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((mix * 32767).astype(np.int16).tobytes()); wv.close()
print('ok', T)
