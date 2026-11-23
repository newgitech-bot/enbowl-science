"""코드로 만드는 저작권 걱정 없는 배경음 (칠합/로파이 느낌, 96 BPM)."""
import numpy as np, sys, wave
SR = 44100
rng = np.random.default_rng(7)

def t_(n): return np.arange(n) / SR
def env_ad(n, a, d):
    t = t_(n); e = np.minimum(1, t / max(a, 1e-4)); return e * np.exp(-t / d)
def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y
def lp_fast(x, fc, k=2):  # 일차 저역통과를 벡터로(필터 계수 근사 대신 FFT)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / fc) ** (2 * k)) ** 0.5, len(x))
def mtof(m): return 440 * 2 ** ((m - 69) / 12)

def kick():
    n = int(0.35 * SR); t = t_(n); f = 50 + 90 * np.exp(-t / 0.04)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
def snare():
    n = int(0.25 * SR); t = t_(n)
    nz = lp_fast(rng.standard_normal(n), 6000) * np.exp(-t / 0.07)
    return 0.6 * nz + 0.3 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05)
def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR); t = t_(n)
    x = rng.standard_normal(n); x = x - lp_fast(x, 7000)
    return x * np.exp(-t / (0.06 if open_ else 0.015))
def epiano(m, dur):  # 부드러운 전자 피아노
    n = int(dur * SR); t = t_(n); f = mtof(m)
    mod = np.sin(2 * np.pi * f * t) * 1.2 * np.exp(-t / 0.4)
    x = np.sin(2 * np.pi * f * t + mod) + 0.2 * np.sin(2 * np.pi * 2 * f * t)
    return x * env_ad(n, 0.01, 0.9) * (1 - np.clip((t - dur + 0.08) / 0.08, 0, 1))
def bass(m, dur):
    n = int(dur * SR); t = t_(n); f = mtof(m)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return np.tanh(1.5 * x) * env_ad(n, 0.005, 0.5) * (1 - np.clip((t - dur + 0.05) / 0.05, 0, 1))
def pluck(m, dur):
    n = int(dur * SR); t = t_(n); f = mtof(m)
    x = np.sign(np.sin(2 * np.pi * f * t)) * 0.3 + np.sin(2 * np.pi * f * t)
    return lp_fast(x, 2500) * env_ad(n, 0.003, 0.18)

def reverb(x, sec=1.6, mix=0.22):
    n = int(sec * SR); ir = rng.standard_normal(n) * np.exp(-t_(n) / (sec / 5))
    ir = lp_fast(ir, 4000); ir /= np.abs(ir).sum() ** 0.5 * 8
    N = 1 << int(np.ceil(np.log2(len(x) + n)))
    w = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
    return x + mix * w / (np.abs(w).max() + 1e-9) * np.abs(x).max()

def make(total, bpm=96):
    beat = 60 / bpm; bar = 4 * beat
    L = int((total + 2) * SR)
    drums = np.zeros(L); keys = np.zeros(L); bs = np.zeros(L); lead = np.zeros(L)
    def put(buf, sig, t, g=1.0):
        s = int(t * SR); e = min(L, s + len(sig))
        if s < L: buf[s:e] += sig[:e - s] * g
    # 코드: Fmaj9 - Em7 - Dm9 - G13sus (밝고 편한 진행)
    chords = [[53, 57, 60, 64, 67], [52, 55, 59, 62, 66], [50, 53, 57, 60, 64], [55, 57, 60, 62, 65]]
    roots = [41, 40, 38, 43]
    melody = [[72, None, 69, 67], [71, None, 67, None], [69, 72, None, 74], [72, None, None, None]]
    nbars = int(np.ceil(total / bar)) + 1
    K, S, H, HO = kick(), snare(), hat(), hat(True)
    for b in range(nbars):
        t0 = b * bar; ci = b % 4
        intro = t0 < 1 * bar
        for k, m in enumerate(chords[ci]):  # 코드는 반박자 늦게 스윙
            put(keys, epiano(m, bar * 0.95), t0 + 0.012 * k, 0.16)
        put(keys, epiano(chords[ci][2] + 12, beat), t0 + 2.5 * beat, 0.08)
        if not intro:
            put(bs, bass(roots[ci], beat * 1.4), t0, 0.5)
            put(bs, bass(roots[ci], beat * 0.45), t0 + 1.75 * beat, 0.35)
            put(bs, bass(roots[ci] + 7, beat * 0.9), t0 + 2.5 * beat, 0.4)
            for st in range(8):  # 8분음표 하이햇, 스윙
                tt = t0 + st * beat / 2 + (0.06 * beat if st % 2 else 0)
                put(drums, HO if st == 7 else H, tt, 0.13 if st % 2 else 0.2)
            put(drums, K, t0, 0.9); put(drums, K, t0 + 2.5 * beat, 0.7)
            if b % 2: put(drums, K, t0 + 3.25 * beat, 0.45)
            put(drums, S, t0 + beat, 0.45); put(drums, S, t0 + 3 * beat, 0.45)
        else:
            put(drums, H, t0 + beat, 0.08); put(drums, H, t0 + 3 * beat, 0.08)
        if b >= 4 and b % 8 >= 4:  # 중간중간 짧은 멜로디
            for q, m in enumerate(melody[ci]):
                if m: put(lead, pluck(m, beat * 0.9), t0 + q * beat, 0.22)
    keys = lp_fast(keys, 3200)
    mix = drums * 0.9 + reverb(keys, 1.8, 0.35) + bs * 0.8 + reverb(lead, 1.4, 0.4)
    # 로파이 질감: 약한 테이프 흔들림 대신 잡음 한 겹
    mix += lp_fast(rng.standard_normal(L), 3000) * 0.004
    mix = np.tanh(mix * 1.2)
    mix = mix[:int(total * SR)]
    fi, fo = int(0.8 * SR), int(2.0 * SR)
    mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
    return mix / np.abs(mix).max() * 0.9

if __name__ == "__main__":
    total = float(sys.argv[1]); out = sys.argv[2]
    x = make(total)
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
