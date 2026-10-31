import numpy as np, sys, subprocess
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, lfilter

SR = 44100
DUR = 30.0
N = int(SR * DUR)
rng = np.random.default_rng(7)

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def tarr(d): return np.arange(int(SR * d)) / SR

def env(n, a=0.01, r=0.2, sus=1.0):
    e = np.ones(n) * sus
    ai = max(1, int(a * SR)); ri = max(1, int(r * SR))
    e[:ai] = np.linspace(0, sus, ai)
    ri = min(ri, n)
    e[-ri:] *= np.linspace(1, 0, ri)
    return e

def osc(f, d, kind="saw", detune=0.0):
    t = tarr(d)
    out = 0
    for dt in ([-detune, detune] if detune else [0]):
        ff = f * (1 + dt)
        ph = (t * ff) % 1.0
        if kind == "saw": out = out + (2 * ph - 1)
        elif kind == "sq": out = out + np.sign(ph - 0.5)
        elif kind == "tri": out = out + (4 * np.abs(ph - 0.5) - 1)
        else: out = out + np.sin(2 * np.pi * ph)
    return out / (2 if detune else 1)

def lp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "low")
    return lfilter(b, a, x)

def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "high")
    return lfilter(b, a, x)

def add(buf, x, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= buf.shape[0]: return
    x = x[: buf.shape[0] - i]
    l = gain * np.cos((pan + 1) * np.pi / 4)
    r = gain * np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * l
    buf[i:i + len(x), 1] += x * r

def reverb(buf, decay=1.8, wet=0.25):
    n = int(SR * decay)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 4.0 / decay * 1.5)[:, None]
    ir = lp(ir.T, 5000).T
    out = np.zeros_like(buf)
    for c in range(2):
        out[:, c] = fftconvolve(buf[:, c], ir[:, c])[: buf.shape[0]]
    out /= (np.abs(out).max() + 1e-9)
    return buf * (1 - wet) + out * wet * np.abs(buf).max()

def kick(d=0.4, f0=140, f1=45):
    n = int(SR * d); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * 1.0

def clap(d=0.25):
    n = int(SR * d); t = np.arange(n) / SR
    x = hp(rng.standard_normal(n), 1200)
    bursts = np.zeros(n)
    for o in (0, 0.012, 0.024):
        i = int(o * SR); bursts[i:] += np.exp(-(t[: n - i]) * 90)
    tail = np.exp(-t * 18) * 0.5
    return x * (bursts * 0.5 + tail) * 0.6

def hat(d=0.08, open_=False):
    n = int(SR * (0.3 if open_ else d)); t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t * (14 if open_ else 60)) * 0.35

def snare(d=0.25):
    n = int(SR * d); t = np.arange(n) / SR
    return (hp(rng.standard_normal(n), 1500) * np.exp(-t * 22) * 0.6 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.4)

def riser(start, d, buf, gain=0.35, f0=300, f1=9000):
    n = int(SR * d); t = np.arange(n) / SR
    x = rng.standard_normal(n)
    out = np.zeros(n)
    # sweep via block filtering
    blocks = 40
    bl = n // blocks
    for i in range(blocks):
        fc = f0 * (f1 / f0) ** (i / blocks)
        seg = x[i * bl:(i + 1) * bl]
        out[i * bl:(i + 1) * bl] = hp(seg, min(fc, 18000), 1)
    out *= np.linspace(0, 1, n) ** 2
    add(buf, out, start, gain=gain)

def impact(start, buf, gain=0.8):
    k = kick(1.2, 90, 32) * gain
    n = int(SR * 2.0); t = np.arange(n) / SR
    shim = lp(rng.standard_normal(n), 6000) * np.exp(-t * 3) * 0.25
    add(buf, k, start)
    add(buf, shim, start)

def finish(buf, name, fade_out=0.6):
    buf = reverb(buf, 1.6, 0.18)
    peak = np.abs(buf).max()
    buf = buf / peak * 0.89
    f = int(fade_out * SR)
    buf[-f:] *= np.linspace(1, 0, f)[:, None]
    buf[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))[:, None]
    wav = f"{OUT}/{name}.wav"
    wavfile.write(wav, SR, (buf * 32767).astype(np.int16))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k", f"{OUT}/{name}.mp3"], check=True)

OUT = sys.argv[1]

def chord_pad(buf, notes, start, d, gain=0.12, kind="saw", fc=1800, a=0.6, r=0.8):
    for m in notes:
        x = osc(mtof(m), d, kind, detune=0.004)
        x = lp(x, fc) * env(len(x), a, r)
        add(buf, x, start, pan=rng.uniform(-0.5, 0.5), gain=gain)

def pluck(buf, m, start, d=0.35, gain=0.15, kind="saw", fc=3500, pan=0.0):
    x = osc(mtof(m), d, kind, detune=0.003)
    x = lp(x, fc) * np.exp(-tarr(d) * 9)
    add(buf, x, start, pan=pan, gain=gain)

def bass(buf, m, start, d, gain=0.35, kind="sin"):
    x = osc(mtof(m), d, kind)
    x = lp(x, 400) * env(len(x), 0.01, 0.08)
    add(buf, x, start, gain=gain)

# ---------- 1. Cinematic Rise (90 BPM) ----------
def cinematic():
    buf = np.zeros((N, 2)); bpm = 90; beat = 60 / bpm
    prog = [([57, 60, 64], 33), ([53, 57, 60], 29), ([55, 59, 62], 31), ([52, 56, 59], 28)]
    # 4 bars per chord pair; 15s ~ 9 beats*... use 2-beat spacing chords
    t0 = 0
    seq = [0, 1, 2, 3, 0, 1]
    for i, k in enumerate(seq):
        notes, b = prog[k % 4]
        s = i * 2.67
        if s >= DUR: break
        chord_pad(buf, [n + 12 for n in notes] + [n for n in notes], s, 3.4, 0.07 + 0.012 * i, "saw", 1200 + 400 * i, 0.9, 1.0)
        bass(buf, b, s, 2.7, 0.3, "sin")
    # strings-like high sustained line rising
    for i, m in enumerate([81, 84, 88, 91]):
        x = lp(osc(mtof(m), 3.0, "tri", 0.005), 5000) * env(int(3.0 * SR), 1.2, 1.0)
        add(buf, x, 3 + i * 2.7, pan=0.3, gain=0.06)
    # soft pulse
    for i in range(int(DUR / beat)):
        s = i * beat
        add(buf, kick(0.3, 90, 50) * (0.35 + 0.35 * min(1, s / 10)), s)
        if s > 5: add(buf, hat(), s + beat / 2, gain=0.5)
    riser(7.0, 3.0, buf, 0.45)
    impact(10.0, buf, 0.9)
    # bright arpeggio after hit
    arp = [69, 76, 81, 84, 88, 84, 81, 76]
    for i in range(int((DUR - 10) / (beat / 2))):
        pluck(buf, arp[i % 8] + (0 if i < 16 else 0), 10.0 + i * beat / 2, 0.4, 0.13, "sq", 4500, pan=(-1) ** i * 0.4)
    chord_pad(buf, [57, 64, 69, 72, 76], 10.0, 5.0, 0.1, "saw", 3500, 0.05, 1.5)
    bass(buf, 33, 10.0, 5.0, 0.4)
    finish(buf, "1_cinematic_rise", 1.2)

# ---------- 2. Clean Tech Pulse (110 BPM) ----------
def tech():
    buf = np.zeros((N, 2)); bpm = 110; beat = 60 / bpm; s16 = beat / 4
    roots = [45, 41, 48, 43]
    chords = [[57, 60, 64, 67], [53, 57, 60, 64], [60, 64, 67, 71], [55, 59, 62, 67]]
    bars = int(DUR / (beat * 4)) + 1
    for b in range(bars):
        bs = b * beat * 4
        k = b % 4
        chord_pad(buf, chords[k], bs, beat * 4 + 0.3, 0.05, "saw", 1500 + 300 * b, 0.1, 0.6)
        for st in range(16):
            s = bs + st * s16
            if s >= DUR: break
            # arp
            m = chords[k][[0, 1, 2, 3, 2, 1, 2, 3][st % 8]] + 12
            gain = 0.09 + 0.05 * min(1, s / 8)
            pluck(buf, m, s, 0.22, gain, "sq", 2500 + 2500 * min(1, s / 10), pan=np.sin(st) * 0.5)
            # bass 8ths
            if st % 2 == 0:
                bass(buf, roots[k], s, s16 * 1.8, 0.3, "tri")
            if st % 4 == 0 and s > 1.0:
                add(buf, kick(0.3, 130, 48), s, gain=0.85)
            if st % 2 == 1 and s > 3:
                add(buf, hat(), s, gain=0.7)
            if st in (4, 12) and s > 4:
                add(buf, clap(), s, gain=0.5)
    riser(6.5, 1.7, buf, 0.3)
    impact(8.2, buf, 0.7)
    finish(buf, "2_clean_tech_pulse", 0.5)

# ---------- 3. Uplifting Pop (120 BPM) ----------
def pop():
    buf = np.zeros((N, 2)); bpm = 120; beat = 60 / bpm
    chords = [[60, 64, 67], [67, 71, 74], [69, 72, 76], [65, 69, 72]]
    roots = [36, 43, 45, 41]
    bars = int(DUR / (beat * 4)) + 1
    for b in range(bars):
        bs = b * beat * 4; k = b % 4
        chord_pad(buf, [n for n in chords[k]] + [chords[k][0] + 12], bs, beat * 4, 0.08, "saw", 3000, 0.02, 0.15)
        for i in range(4):
            s = bs + i * beat
            if s >= DUR: break
            add(buf, kick(0.3, 130, 50), s, gain=0.85)
            add(buf, hat(0.08, True), s + beat / 2, gain=0.6)
            if i in (1, 3): add(buf, clap(), s, gain=0.7)
            bass(buf, roots[k], s, beat * 0.9, 0.35, "sin")
            bass(buf, roots[k], s + beat / 2, beat * 0.4, 0.25, "sin")
        # hook: bell-ish melody
        mel = [[79, 76, 79, 81], [83, 79, 83, 86], [84, 81, 84, 88], [81, 77, 81, 84]][k]
        for i, m in enumerate(mel):
            s = bs + i * beat
            if s >= DUR: break
            x = osc(mtof(m), 0.6, "sin") + 0.4 * osc(mtof(m * 2 if m < 96 else m), 0.6, "sin") * 0.0
            x = (osc(mtof(m), 0.6, "sin") + 0.3 * osc(mtof(m + 12), 0.6, "sin")) * np.exp(-tarr(0.6) * 5)
            add(buf, x, s, pan=0.2, gain=0.18)
    riser(5.5, 2.0, buf, 0.25)
    finish(buf, "3_uplifting_pop", 0.5)

# ---------- 4. Ambient Glow (80 BPM) ----------
def ambient():
    buf = np.zeros((N, 2)); bpm = 80; beat = 60 / bpm
    chords = [[57, 64, 67, 72], [53, 60, 64, 69], [48, 55, 64, 67], [55, 62, 67, 71]]
    for i in range(5):
        s = i * 3.2
        if s >= DUR: break
        chord_pad(buf, chords[i % 4], s, 5.2, 0.09, "tri", 2200, 1.4, 2.0)
        chord_pad(buf, [chords[i % 4][0] - 12], s, 5.2, 0.12, "sin", 600, 1.4, 2.0)
    mel = [76, 79, 81, 79, 84, 81, 79, 76, 79, 81, 84, 88]
    for i, m in enumerate(mel):
        s = 1.0 + i * beat * 1.0 + (0.0 if i % 3 else 0.1)
        if s >= DUR - 0.5: break
        x = (osc(mtof(m), 1.8, "sin") + 0.25 * osc(mtof(m * 2), 1.8, "sin")) * np.exp(-tarr(1.8) * 2.6)
        x = x * (1 - np.exp(-tarr(1.8) * 300))
        add(buf, x, s, pan=(-1) ** i * 0.35, gain=0.17)
    # shimmer
    n = N; sh = hp(lp(rng.standard_normal(n), 9000), 5000) * np.linspace(0.0, 0.05, n) ** 1
    buf[:, 0] += sh * 0.5; buf[:, 1] += sh[::-1] * 0.5
    buf = reverb(buf, 2.6, 0.35)
    finish(buf, "4_ambient_glow", 1.5)

# ---------- 5. Fast Hype (128 BPM) ----------
def hype():
    buf = np.zeros((N, 2)); bpm = 128; beat = 60 / bpm; s16 = beat / 4
    roots = [38, 38, 41, 36]
    drop = 8 * beat  # ~3.75s? use drop at bar 3 start -> 8 beats
    drop = 7.5
    bars = int(DUR / (beat * 4)) + 1
    for b in range(bars):
        bs = b * beat * 4; k = b % 4
        for st in range(16):
            s = bs + st * s16
            if s >= DUR: break
            pre = s < drop
            if st % 4 == 0 and (not pre or s > 1.9):
                add(buf, kick(0.28, 150, 48), s, gain=0.95)
            if st % 4 == 2:
                add(buf, hat(0.08, True), s, gain=0.7 if not pre else 0.3)
            if st % 2 == 1 and not pre:
                add(buf, hat(), s, gain=0.5)
            if st in (4, 12) and not pre:
                add(buf, clap(), s, gain=0.75)
                add(buf, snare(), s, gain=0.3)
            if not pre:
                # offbeat bass
                if st % 4 == 2:
                    x = lp(osc(mtof(roots[k] + 12), s16 * 3, "saw", 0.003), 900) * env(int(s16 * 3 * SR), 0.005, 0.05)
                    add(buf, x, s, gain=0.28)
                if st % 4 in (0, 1, 3) and st < 16:
                    bass(buf, roots[k], s, s16 * 0.9, 0.25, "sin")
                # stabs
                if st in (0, 3, 6, 10, 14):
                    for n in [62 + (0 if k < 2 else 3 * (k - 1)), 65, 69]:
                        x = lp(osc(mtof(n + 12), 0.15, "saw", 0.005), 4000) * np.exp(-tarr(0.15) * 14)
                        add(buf, x, s, gain=0.07, pan=0.2)
            else:
                # build snare roll
                if s > 5.0 and st % 2 == 0:
                    add(buf, snare(0.15), s, gain=0.25 * (s - 5) / 2.5)
    # pre-drop pad
    chord_pad(buf, [50, 57, 62, 65], 0, drop, 0.07, "saw", 1500, 1.0, 0.1)
    riser(4.5, drop - 4.5 - 0.05, buf, 0.5)
    # silence gap before drop
    g0, g1 = int((drop - 0.12) * SR), int(drop * SR)
    buf[g0:g1] *= np.linspace(1, 0.05, g1 - g0)[:, None]
    impact(drop, buf, 1.0)
    chord_pad(buf, [50, 57, 62, 65, 69], drop, DUR - drop, 0.06, "saw", 3500, 0.02, 0.6)
    finish(buf, "5_fast_hype", 0.4)


def hype30():
    buf = np.zeros((N, 2)); bpm = 128; beat = 60 / bpm; s16 = beat / 4; bar = beat * 4
    D1, S4, S5, S6, D2, EG = 7.5, 11.25, 16.875, 19.6875, 22.5, 28.125
    roots = [38, 38, 41, 36]
    chordsA = [[62, 65, 69], [62, 65, 69], [65, 69, 72], [60, 64, 67]]
    nbars = int(DUR / bar) + 1
    for b in range(nbars):
        bs = b * bar; k = b % 4
        for st in range(16):
            s = bs + st * s16
            if s >= DUR: break
            groove = (D1 <= s < S5) or (D2 <= s < EG)
            brk = S5 <= s < S6
            build2 = S6 <= s < D2
            intro = s < D1
            outro = s >= EG
            second = s >= D2
            # kick
            if groove and st % 4 == 0: add(buf, kick(0.28, 150, 48), s, gain=0.95)
            if intro and st % 4 == 0 and s > 1.9: add(buf, kick(0.28, 150, 48), s, gain=0.95)
            if brk and st in (0, 8): add(buf, kick(0.4, 90, 40), s, gain=0.55)
            # hats / claps
            if groove:
                if st % 4 == 2: add(buf, hat(0.08, True), s, gain=0.7)
                if st % 2 == 1: add(buf, hat(), s, gain=0.5)
                if st in (4, 12): add(buf, clap(), s, gain=0.75); add(buf, snare(), s, gain=0.3)
            if brk and st % 2 == 0: add(buf, hat(), s, gain=0.35)
            if intro and st % 4 == 2: add(buf, hat(0.08, True), s, gain=0.3)
            # bass + stabs
            if groove:
                if st % 4 == 2:
                    x = lp(osc(mtof(roots[k] + 12), s16 * 3, "saw", 0.003), 900) * env(int(s16 * 3 * SR), 0.005, 0.05)
                    add(buf, x, s, gain=0.28)
                if st % 4 in (0, 1, 3): bass(buf, roots[k], s, s16 * 0.9, 0.25, "sin")
                if st in (0, 3, 6, 10, 14):
                    for n in chordsA[k]:
                        x = lp(osc(mtof(n + 12), 0.15, "saw", 0.005), 4000) * np.exp(-tarr(0.15) * 14)
                        add(buf, x, s, gain=0.07, pan=0.2)
            # lead arp: extra in first groove after S4 and in second drop
            if (S4 <= s < S5) or second and groove:
                m = chordsA[k][[0, 1, 2, 1][st % 4]] + 24
                pluck(buf, m, s, 0.2, 0.07 if s < D2 else 0.09, "sq", 4500, pan=np.sin(st) * 0.5)
            if brk:
                if st % 2 == 0:
                    m = chordsA[k][[0, 1, 2, 1][(st // 2) % 4]] + 12
                    pluck(buf, m, s, 0.35, 0.09, "tri", 2500, pan=np.sin(st) * 0.4)
            # snare rolls
            if intro and s > 5.0 and st % 2 == 0 and s < D1:
                add(buf, snare(0.15), s, gain=0.25 * (s - 5) / 2.5)
            if build2:
                prog = (s - S6) / (D2 - S6)
                step = 2 if prog < 0.5 else 1
                if st % step == 0: add(buf, snare(0.15), s, gain=0.12 + 0.3 * prog)
    # pads
    chord_pad(buf, [50, 57, 62, 65], 0, D1, 0.07, "saw", 1500, 1.0, 0.1)
    chord_pad(buf, [50, 57, 62, 65, 69], D1, S5 - D1, 0.06, "saw", 3500, 0.02, 0.6)
    chord_pad(buf, [48, 55, 60, 64], S5, S6 - S5, 0.09, "saw", 1800, 0.4, 0.3)
    chord_pad(buf, [48, 55, 60, 64], S6, D2 - S6, 0.07, "saw", 2200, 0.5, 0.1)
    chord_pad(buf, [50, 57, 62, 65, 69, 74], D2, EG - D2, 0.07, "saw", 4200, 0.02, 0.6)
    chord_pad(buf, [50, 57, 62, 69], EG, DUR - EG, 0.08, "saw", 2600, 0.05, 1.2)
    # risers and impacts
    riser(4.5, D1 - 4.5 - 0.05, buf, 0.5)
    riser(S6 + 0.2, D2 - S6 - 0.25, buf, 0.55, 300, 12000)
    for g in (D1, D2):
        g0, g1 = int((g - 0.12) * SR), int(g * SR)
        buf[g0:g1] *= np.linspace(1, 0.05, g1 - g0)[:, None]
        impact(g, buf, 1.0)
    impact(S4, buf, 0.45)          # scene change: +3.2 counter
    impact(S5, buf, 0.35)          # man clip
    add(buf, kick(1.0, 80, 30), EG, gain=0.9)  # outro hit
    finish(buf, "hype_30s", 1.2)

hype30()
print("ok")
