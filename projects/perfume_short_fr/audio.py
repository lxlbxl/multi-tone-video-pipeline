"""Builds the final audio: cleaned voice + synthesized music bed (ducked) + SFX.
python3 audio.py SRC.mp4 OUT.wav"""
import sys, subprocess, numpy as np, wave
from edit_spec import *

SR = 48000
DUR = int((T_END - T0) * 24) / 24.0
N = int(DUR * SR)
rng = np.random.default_rng(7)


def to_out(t): return t - T0


def read_wav(p):
    w = wave.open(p); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a.reshape(-1, w.getnchannels()).mean(1)


# ------------------------------------------------ voice
src = sys.argv[1]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(T0), "-t", str(DUR), "-i", src, "-vn",
                "-af", "highpass=f=85,lowpass=f=14000,afftdn=nf=-28:tn=1,"
                       "equalizer=f=220:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.0:g=3,equalizer=f=9000:t=h:w=1:g=2,"
                       "acompressor=threshold=-20dB:ratio=3.5:attack=8:release=120:makeup=4,"
                       "alimiter=limit=0.89",
                "-ar", str(SR), "-ac", "1", "voice.wav"], check=True)
voice = read_wav("voice.wav")[:N]
voice = np.pad(voice, (0, N - len(voice)))
voice /= np.sqrt(np.mean(voice[np.abs(voice) > 0.01] ** 2)) / 0.16   # normalise speech RMS

# voice envelope for ducking
win = int(0.05 * SR)
e = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same"))
duck_target = np.where(e > 0.03, 1.0, 0.0)
# smooth: fast attack, slow release
duck = np.zeros(N); d = 0.0
a_att, a_rel = 1 - np.exp(-1 / (0.04 * SR)), 1 - np.exp(-1 / (0.35 * SR))
step = 48
for i in range(0, N, step):
    tgt = duck_target[i]
    k = a_att if tgt > d else a_rel
    d += (tgt - d) * (1 - (1 - k) ** step)
    duck[i:i + step] = d


# ------------------------------------------------ music bed (synth)
def env_adsr(n, a=0.01, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)


BPM = 96; beat = 60 / BPM
music = np.zeros(N)
# chord progression (Am - F - C - G), two bars each
prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
bar = 4 * beat
t_all = np.arange(N) / SR
for ci in range(int(DUR / (2 * bar)) + 2):
    chord = prog[ci % 4]
    s0 = int(ci * 2 * bar * SR); n = int(2 * bar * SR) + int(0.5 * SR)
    if s0 >= N: break
    n = min(n, N - s0)
    tt = np.arange(n) / SR
    pad = np.zeros(n)
    for m in chord + [chord[0] + 12]:
        f = mtof(m)
        for det in (-0.12, 0.0, 0.12):
            pad += np.sin(2 * np.pi * f * (1 + det / 100) * tt + rng.random() * 6)
            pad += 0.25 * np.sin(2 * np.pi * 2 * f * (1 + det / 100) * tt)
    pad *= np.minimum(1, tt / 0.6) * np.minimum(1, (n / SR - tt) / 0.5)
    music[s0:s0 + n] += pad * 0.018
    # bass
    fb = mtof(chord[0] - 24)
    for b in range(8):
        bs = s0 + int(b * beat * SR)
        if bs >= N: break
        bn = min(int(beat * SR), N - bs); bt = np.arange(bn) / SR
        music[bs:bs + bn] += 0.10 * np.sin(2 * np.pi * fb * bt) * env_adsr(bn, 0.005, 0.35)
    # arp pluck (eighths)
    arp = chord + [chord[1] + 12]
    for k in range(16):
        ps = s0 + int(k * beat / 2 * SR)
        if ps >= N: break
        pn = min(int(0.4 * SR), N - ps); pt = np.arange(pn) / SR
        f = mtof(arp[k % 4] + 12)
        music[ps:ps + pn] += 0.035 * (np.sin(2 * np.pi * f * pt) + 0.3 * np.sin(4 * np.pi * f * pt)) * env_adsr(pn, 0.002, 0.09)
# drums
nb = int(DUR / beat) + 1
for b in range(nb):
    s = int(b * beat * SR)
    if s >= N: break
    if b % 2 == 0:  # kick
        n = min(int(0.3 * SR), N - s); tt = np.arange(n) / SR
        f = 50 + 90 * np.exp(-tt * 30)
        music[s:s + n] += 0.32 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9)
    else:  # snap/clap
        n = min(int(0.18 * SR), N - s)
        music[s:s + n] += 0.07 * rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 28)
    for h in (0.5,):  # off-beat hats
        hs = s + int(h * beat * SR)
        if hs < N:
            n = min(int(0.05 * SR), N - hs)
            hn = rng.standard_normal(n); hn = np.diff(np.concatenate([[0], hn]))
            music[hs:hs + n] += 0.03 * hn * np.exp(-np.arange(n) / SR * 80)
# fade in/out and ducking
music *= np.minimum(1, t_all / 1.0) * np.minimum(1, (DUR - t_all) / 1.5)
music *= (1 - 0.72 * duck)
music *= 0.75

# ------------------------------------------------ SFX
sfx = np.zeros(N)
def place(sig, t, gain=1.0):
    s = int(to_out(t) * SR)
    if s < 0: sig = sig[-s:]; s = 0
    n = min(len(sig), N - s)
    if n > 0: sfx[s:s + n] += sig[:n] * gain

def whoosh(d=0.5):
    n = int(d * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    # sweep band-pass via moving filter: crude one-pole with varying coeff
    y = np.zeros(n); lp = 0; lp2 = 0
    for i in range(n):
        fc = 300 + 5000 * np.sin(np.pi * i / n) ** 2
        a = 1 - np.exp(-2 * np.pi * fc / SR)
        lp += a * (x[i] - lp); lp2 += a * 0.3 * (lp - lp2)
        y[i] = lp - lp2
    return y / (np.abs(y).max() + 1e-9) * np.sin(np.pi * tt / d) ** 1.5

def pop():
    n = int(0.09 * SR); tt = np.arange(n) / SR
    f = 900 * np.exp(-tt * 18) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 45)

def boom():
    n = int(1.0 * SR); tt = np.arange(n) / SR
    f = 38 + 120 * np.exp(-tt * 14)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.5)
    s += 0.25 * rng.standard_normal(n) * np.exp(-tt * 25)
    return s

def shimmer(d=1.4):
    n = int(d * SR); tt = np.arange(n) / SR; s = np.zeros(n)
    for k, m in enumerate([81, 84, 88, 91, 93, 96]):
        st = int(k * 0.07 * SR); f = mtof(m)
        seg = np.sin(2 * np.pi * f * tt[:n - st]) * np.exp(-tt[:n - st] * 3.2)
        s[st:] += seg * 0.4
    return s * np.minimum(1, tt / 0.01)

def ding():
    n = int(1.2 * SR); tt = np.arange(n) / SR
    return sum(a * np.sin(2 * np.pi * f * tt) for f, a in ((1320, 1), (2640, .4), (3960, .2))) * np.exp(-tt * 4)

def riser(d=1.0):
    n = int(d * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n); y = np.zeros(n); lp = 0
    for i in range(n):
        a = 1 - np.exp(-2 * np.pi * (200 + 6000 * (i / n) ** 2) / SR); lp += a * (x[i] - lp); y[i] = lp
    return y / (np.abs(y).max() + 1e-9) * (tt / d) ** 2

W_ = whoosh(); P_ = pop(); B_ = boom(); SH_ = shimmer(); D_ = ding()
# hook
place(B_, T0 + 0.05, 0.55); place(P_, T0 + 0.27, 0.3); place(P_, T0 + 0.49, 0.3)
place(W_, HOOK[1] - 0.05, 0.35)
# headlines behind him
for h in HEADLINES:
    place(W_, h[0] - 0.25, 0.28); place(B_, h[0], 0.30)
# product transitions
for p in PRODUCTS:
    place(riser(0.6), p[0] - 0.6, 0.12); place(W_, p[0] - 0.15, 0.4); place(B_, p[0], 0.35)
# bottle highlight shimmer
for col, pts in BOTTLE_TRACKS:
    place(SH_, pts[0][0] - 0.3, 0.16)
# chips
for p in PRODUCTS:
    for ct, _ in p[6]: place(P_, ct, 0.28); place(whoosh(0.3), ct - 0.1, 0.12)
# emphasised caption words: soft pop
for txt, ts in CAPTIONS:
    for w, tt in zip(txt.split(), ts):
        if w.startswith("*"): place(P_, tt, 0.14)
# end card
place(D_, END_CARD_START + 0.6, 0.18); place(P_, END_CARD_START + 0.75, 0.25); place(P_, END_CARD_START + 0.9, 0.25)
place(D_, END_CARD_START + 1.6, 0.14)

mix = voice * 1.0 + music + sfx * 0.9
mix = np.tanh(mix * 0.9) / 0.9
pcm = (np.clip(mix / max(1.0, np.abs(mix).max() / 0.95), -1, 1) * 32767).astype(np.int16)
st = np.stack([pcm, pcm], 1)
with wave.open("premix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "premix.wav", "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", str(SR), sys.argv[2]], check=True)
print("audio done", DUR)
