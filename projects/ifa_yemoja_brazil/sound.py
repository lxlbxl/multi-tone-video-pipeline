"""Sound design for the Yemọja reel: VO placement, ducked carnival bed, synthesized SFX.
usage: python3 sound.py edit.json in.mp4-audio.wav vo_dir out.wav
"""
import sys, json, wave, subprocess
import numpy as np
ein, src_wav, vo_dir, out = sys.argv[1:5]
E = json.load(open(ein)); Q = E['cues']; T = E['total']; SR = 44100; N = int(T * SR)
t = np.arange(N) / SR
def readwav(p):
    w = wave.open(p); ch = w.getnchannels(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return x.reshape(-1, ch).mean(1) if ch > 1 else x
def dec(path):  # any audio -> mono float @SR
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768
rng = np.random.default_rng(7)
def place(buf, sig, at, g=1.0):
    i = int(at * SR);
    if i >= len(buf): return
    j = min(len(buf), i + len(sig)); buf[i:j] += g * sig[:j - i]
def lp(x, a):  # one-pole lowpass, a in (0,1]
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s += a * (x[i] - s); y[i] = s
    return y
def env(n, att, rel):
    e = np.ones(n); a = int(att * SR); r = int(rel * SR)
    if a: e[:a] = np.linspace(0, 1, a)
    if r: e[-r:] *= np.linspace(1, 0, r)
    return e

# ---------- VO ----------
vo = np.zeros(N)
for k, g0 in E['vo'].items():
    v = dec(f'{vo_dir}/vo{k}.mp3'); place(vo, v, g0)
vo_env = np.convolve(np.abs(vo), np.ones(int(.12 * SR)) / int(.12 * SR), 'same')
talk = np.clip(vo_env / (np.percentile(vo_env[vo_env > 1e-4], 60) + 1e-9), 0, 1)
talk = np.convolve(talk, np.ones(int(.35 * SR)) / int(.35 * SR), 'same')  # smooth ducking curve

# ---------- carnival bed ----------
src = dec(src_wav)
bed = np.zeros(N)
A_end = E['replay_start']
place(bed, src[:int(A_end * SR)], 0)
tail = src[int(18 * SR):int((18 + (T - A_end) + .5) * SR)]           # normal-speed crowd/music under the outro
place(bed, tail * env(len(tail), .8, 2.5), A_end - .3, 0.9)
gain = 1.0 - 0.72 * talk                                               # duck ~-11 dB under voice
# emotional section: muffled + quiet
emo = np.clip(np.minimum((t - 29.3) / .6, (38.55 - t) / .15), 0, 1)
bed_lp = lp(bed, 0.04)
bed = bed * (1 - emo) + bed_lp * emo * 0.55
gain *= (1 - 0.25 * emo)
# outro: sit lower under the call, fade at end card
outro = np.clip((t - 47.6) / 1.0, 0, 1)
gain *= (1 - 0.25 * outro)
gain *= np.clip((T - t) / 3.0, 0, 1)
bed *= gain

# ---------- SFX ----------
fx = np.zeros(N)
def noise(d): return rng.standard_normal(int(d * SR))
def whoosh(d=.6, bright=.3):
    x = noise(d); y = np.zeros_like(x); s = 0
    for i in range(len(x)): s += (0.02 + bright * i / len(x)) * (x[i] - s); y[i] = s
    tt = np.arange(len(x)) / SR; return y * np.sin(np.pi * tt / d) ** 2 / (np.abs(y).max() + 1e-9)
def riser(d=1.0):
    tt = np.arange(int(d * SR)) / SR; f = 120 * (8 ** (tt / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    nz = whoosh(d, .5) * 0.8
    return (tone + nz) * (tt / d) ** 2
def boom(d=1.6, f0=55):
    tt = np.arange(int(d * SR)) / SR; f = f0 + 70 * np.exp(-tt * 9)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.6)
    click = noise(.03) * np.exp(-np.arange(int(.03 * SR)) / SR * 120) * .5
    s[:len(click)] += click; return s
def ding(f, d=1.4, b=0.0):
    tt = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * f * 2.01 * tt) + .2 * np.sin(2 * np.pi * f * 3 * tt)) * np.exp(-tt * (4 + b)) / 1.6
def pop():
    tt = np.arange(int(.16 * SR)) / SR; f = 900 * np.exp(-tt * 18) + 260
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 24)
def thump(d=.35):
    tt = np.arange(int(d * SR)) / SR; return np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 20)) * tt) * np.exp(-tt * 14)
def shimmer(d=2.0):
    s = np.zeros(int(d * SR))
    for k, f in enumerate([1318.5, 1567.98, 1975.5, 2637.0, 3136.0]):
        tt = np.arange(len(s) - int(k * .07 * SR)) / SR
        s[int(k * .07 * SR):] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3) * .3
    return s
def splash(d=1.2):
    x = noise(d); y = x - lp(x, .15); tt = np.arange(len(x)) / SR
    return y * np.exp(-tt * 3.5) * (1 - np.exp(-tt * 60)) * .6

# hook
place(fx, whoosh(.5), 0.05, .35)
place(fx, pop(), 2.0, .35)                                  # strike-through tick
place(fx, riser(1.0), Q['brazil'] - 1.0, .32)
place(fx, boom(1.8), Q['brazil'] - .02, .95)
# Yemọja reveal
place(fx, riser(1.1), Q['yemoja1'] - 1.1, .28)
place(fx, boom(1.4, 60), Q['yemoja1'] - .02, .6)
place(fx, splash(1.4), Q['yemoja1'], .55)
place(fx, shimmer(2.2), Q['yemoja1'] + .05, .35)
place(fx, ding(1046.5, 1.0, 1), Q['our'], .18)
place(fx, ding(784, 1.4), 12.0, .12)
# map
place(fx, whoosh(.7), 15.0, .35)
ocean = lp(noise(14.0), .02); ocean *= (0.6 + .4 * np.sin(2 * np.pi * .18 * np.arange(len(ocean)) / SR)) * env(len(ocean), 1.0, 1.5)
place(fx, ocean / (np.abs(ocean).max() + 1e-9), 15.1, .22)
place(fx, ding(880, 1.2), Q['ogun'] - .2, .16)
place(fx, ding(659.3, 1.4), 23.5, .16)
place(fx, shimmer(1.8), Q['carried2'], .2)
place(fx, pop(), 26.0, .25); place(fx, pop(), 27.35, .25)
# emotional heartbeat
hb = 29.7
while hb < 37.9:
    place(fx, thump(), hb, .55); place(fx, thump(), hb + .26, .38); hb += 1.0
drone_t = np.arange(int(9.0 * SR)) / SR
drone = (np.sin(2 * np.pi * 55 * drone_t) + .5 * np.sin(2 * np.pi * 82.4 * drone_t) + .3 * np.sin(2 * np.pi * 110 * drone_t)) * env(len(drone_t), 1.5, 1.0)
place(fx, drone / 1.8, 29.4, .18)
place(fx, ding(523.25, 2.4) + ding(659.25, 2.4) * .8 + ding(783.99, 2.4) * .6, Q['never'] - .45, .14)
# AND TODAY
place(fx, riser(.9), Q['today'] - 1.05, .3)
place(fx, boom(1.4), Q['today'] - .25, .7)
place(fx, whoosh(.5), 41.35, .3); place(fx, pop(), 41.5, .35); place(fx, pop(), 42.4, .35); place(fx, ding(1046.5, 1.0, 1), 43.1, .2)
# the call
for c in ['lagos', 'london', 'houston', 'bahia']: place(fx, pop(), Q[c] - .05, .4); place(fx, ding(1318.5, .6, 3), Q[c] - .03, .08)
for c in ['speak', 'wear', 'teach']: place(fx, boom(.8, 70), Q[c] - .08, .5); place(fx, whoosh(.35), Q[c] - .3, .2)
place(fx, riser(1.2), Q['proud'] - 1.2, .3); place(fx, boom(2.0), Q['proud'] - .05, .85)
place(fx, shimmer(2.0), Q['eje'], .25)
place(fx, riser(.8), Q['ase'] - .8, .35); place(fx, boom(2.6, 45), Q['ase'] - .03, 1.0); place(fx, shimmer(2.6), Q['ase'], .4)
place(fx, ding(783.99, 2.5) + .7 * ding(1174.66, 2.5), 69.45, .2)
# warm pad under the call, swelling to the end
pt = np.arange(int((T - 47.5) * SR)) / SR
pad = sum(a * np.sin(2 * np.pi * f * pt + .3 * np.sin(2 * np.pi * .1 * pt)) for f, a in [(98, .5), (146.8, .35), (196, .3), (246.9, .18), (293.7, .12)])
pad *= np.clip(pt / 4, 0, 1) * (0.7 + 0.3 * np.clip((pt - 10) / 10, 0, 1)) * np.clip((T - 47.5 - pt) / 2.5, 0, 1)
place(fx, pad / np.abs(pad).max(), 47.5, .16)

mix = vo * 1.0 + bed * 0.55 + fx * 0.5
mix /= max(1.0, np.abs(mix).max() / 0.98)
w = wave.open(out, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes()); w.close()
print('ok', T)
