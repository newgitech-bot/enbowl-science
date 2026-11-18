"""효과음 합성 + 나레이션 배치 → 오디오 트랙 wav"""
import json, subprocess, sys, wave
import numpy as np
SR = 44100
rng = np.random.default_rng(7)

def env(n, a=0.005, d=0.1):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
    return e

def lp(x, k):  # 간단 저역통과(이동평균)
    return np.convolve(x, np.ones(k) / k, mode="same")

def bp(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))

def whoosh(dur=0.4):
    n = int(SR * dur); x = rng.normal(size=n)
    t = np.linspace(0, 1, n)
    out = np.zeros(n)
    for i, (lo, hi) in enumerate([(300, 900), (700, 2000), (1500, 4000)]):
        seg = bp(x, lo, hi) * np.sin(np.pi * np.clip(t * 3 - i * 0.6, 0, 1)) ** 2
        out += seg
    return out / np.abs(out).max() * 0.35

def pop(f0=900):
    n = int(SR * 0.09); t = np.arange(n) / SR
    f = f0 * np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.03) * 0.35

def tick():
    n = int(SR * 0.025); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) + 0.5 * rng.normal(size=n)) * env(n, 0.0005, 0.006) * 0.25

def thud(f0=90, amp=0.6):
    n = int(SR * 0.25); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f0 * t * (1 - 0.3 * t)) + 0.3 * lp(rng.normal(size=n), 20)) * env(n, 0.002, 0.06) * amp

def slide(dur=1.1):
    n = int(SR * dur); x = bp(rng.normal(size=n), 1500, 6000)
    t = np.linspace(0, 1, n)
    return x / np.abs(x).max() * np.sin(np.pi * t) ** 1.5 * 0.12

def roll(dur, amp=0.35):
    n = int(SR * dur); t = np.arange(n) / SR
    x = lp(rng.normal(size=n), 60)
    x = x / np.abs(x).max()
    rumble = np.sin(2 * np.pi * 55 * t) * 0.4 + np.sin(2 * np.pi * 7 * t) * 0.2
    e = np.minimum(1, t / 0.15) * np.minimum(1, (dur - t) / 0.2)
    return (x * 0.8 + rumble * 0.3) * e * amp

def pin_crash():
    n = int(SR * 1.4); out = np.zeros(n); t = np.arange(n) / SR
    # 첫 충격
    out[:int(SR * 0.3)] += thud(70, 1.0)[:int(SR * 0.3)] if len(thud()) >= int(SR * 0.3) else 0
    imp = bp(rng.normal(size=int(SR * 0.12)), 200, 5000) * env(int(SR * 0.12), 0.0005, 0.03)
    out[:len(imp)] += imp / np.abs(imp).max() * 0.9
    # 핀끼리 부딪히는 나무 소리 여러 개
    for k in range(26):
        st = int(SR * (0.02 + rng.exponential(0.18)))
        if st >= n - 4000: continue
        f = rng.uniform(900, 2600); m = int(SR * 0.08); tt = np.arange(m) / SR
        clack = (np.sin(2 * np.pi * f * tt) + 0.6 * np.sin(2 * np.pi * f * 2.3 * tt)) * env(m, 0.0005, 0.018)
        clack += bp(rng.normal(size=m), 800, 4000) * env(m, 0.0003, 0.008) * 0.6
        out[st:st + m] += clack * rng.uniform(0.25, 0.7) * np.exp(-st / SR * 1.5)
    # 핀이 바닥에 떨어지는 둔탁한 소리
    for k in range(6):
        st = int(SR * rng.uniform(0.25, 0.9)); b = thud(rng.uniform(110, 170), 0.35)
        out[st:st + len(b)] += b[:max(0, n - st)]
    return out / np.abs(out).max() * 0.9

def drip():
    n = int(SR * 0.12); t = np.arange(n) / SR
    f = 600 + 1400 * t / 0.12
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.003, 0.04) * 0.18

def heartbeat():
    a = thud(55, 0.5); b = thud(50, 0.35)
    out = np.zeros(int(SR * 0.45)); out[:len(a)] += a; out[int(SR * 0.2):int(SR * 0.2) + len(b)] += b[:len(out) - int(SR * 0.2)]
    return out

def rise(dur=0.6):
    n = int(SR * dur); t = np.arange(n) / SR
    f = 300 + 900 * (t / dur) ** 1.5
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / dur) * 0.12

def chime():
    out = np.zeros(int(SR * 1.2))
    for i, f in enumerate((880, 1318.5)):
        n = int(SR * 0.9); t = np.arange(n) / SR
        s = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t)) * env(n, 0.003, 0.35) * 0.25
        st = int(SR * 0.12 * i); out[st:st + n] += s
    return out

def load_voice(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)

def build(spec, out_path):
    total = spec["duration"]; mix = np.zeros(int(SR * (total + 1)))
    def put(sig, t, gain=1.0):
        st = int(SR * t)
        if st >= len(mix): return
        e = min(len(mix), st + len(sig)); mix[st:e] += sig[:e - st] * gain
    for ev in spec["events"]:
        kind, t = ev[0], ev[1]
        g = ev[2] if len(ev) > 2 and not isinstance(ev[2], str) else 1.0
        if kind == "voice": put(load_voice(ev[2]), t, 1.0)
        elif kind == "roll": put(roll(ev[2]), t, ev[3] if len(ev) > 3 else 1.0)
        elif kind == "slide": put(slide(ev[2]), t)
        else: put(globals()[kind](), t, g)
    mix = mix[:int(SR * total)]
    peak = np.abs(mix).max(); mix = mix / peak * 0.95 if peak > 0.95 else mix
    pcm = (mix * 32767).astype(np.int16)
    with wave.open(out_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if __name__ == "__main__":
    build(json.load(open(sys.argv[1])), sys.argv[2])
