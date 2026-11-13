#!/usr/bin/env python3
"""Banda sonora del comercial: narración, música con atenuación automática y efectos sintetizados.

Uso: python3 audio.py <carpeta_voz> <musica.mp3> <carpeta_salida>

- <carpeta_voz> contiene linea_1.wav … linea_5.wav (ver voz.py).
- Los efectos de sonido se sintetizan aquí con numpy: no hay grabaciones de terceros.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

HERE = Path(__file__).resolve().parent
VOZ, MUSIC, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((HERE / "montaje.json").read_text())
SR = 48000
BEAT = 60.0 / cfg["musica"]["bpm"]
rng = np.random.default_rng(7)

# --- Línea de tiempo --------------------------------------------------------
starts, shots, t = [], {}, 0.0
for esc in cfg["escenas"]:
    starts.append(t)
    for shot_id, beats, *_ in esc["planos"]:
        shots[shot_id] = t
        t += beats * BEAT
BODY = t
TOTAL = BODY + cfg["marca_s"]
N = int(TOTAL * SR)

def band(x, lo, hi):
    if lo and hi:
        sos = butter(4, [lo, hi], btype="band", fs=SR, output="sos")
    elif lo:
        sos = butter(4, lo, btype="high", fs=SR, output="sos")
    else:
        sos = butter(4, hi, btype="low", fs=SR, output="sos")
    return sosfilt(sos, x)

def place(bus, sig, at, gain=1.0, pan=0.0):
    """Suma una señal mono al bus estéreo en el segundo `at` (pan -1 izquierda … 1 derecha)."""
    i = int(at * SR)
    if i < 0:
        sig = sig[-i:]; i = 0
    sig = sig[: max(0, N - i)]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    bus[i:i + len(sig), 0] += sig * gain * l
    bus[i:i + len(sig), 1] += sig * gain * r

def tt(d):
    return np.arange(int(d * SR)) / SR

# --- Efectos sintetizados -----------------------------------------------------
def whoosh(d=0.7):
    x = tt(d); n = rng.standard_normal(len(x))
    lo, mid, hi = band(n, 200, 900), band(n, 900, 3500), band(n, 3500, 9000)
    u = x / d
    env = np.sin(np.pi * u) ** 2
    return (lo * (1 - u) + mid * np.sin(np.pi * u) + hi * u) * env / 3

def riser(d=2.0):
    x = tt(d); u = x / d; n = rng.standard_normal(len(x))
    air = band(n, 1500, 10000) * u ** 2.5
    tone = np.sin(2 * np.pi * np.cumsum(180 + 900 * u ** 2) / SR) * u ** 3 * 0.25
    return (air * 0.5 + tone) * np.minimum(1, (1 - u) * 60)

def impact(d=2.6):
    x = tt(d)
    f = 38 + 34 * np.exp(-x / 0.12)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.55)
    thump = band(rng.standard_normal(len(x)), None, 220) * np.exp(-x / 0.07) * 0.8
    tail = band(rng.standard_normal(len(x)), 150, 1800) * np.exp(-x / 0.8) * 0.06
    return sub + thump + tail

def shimmer(d=3.4):
    x = tt(d); out = np.zeros(len(x))
    for f in (2093, 2637, 3136, 3951, 4186, 5274, 6272):
        on = rng.uniform(0, 0.35); tau = rng.uniform(0.9, 1.8)
        e = np.where(x > on, np.exp(-(x - on) / tau), 0) * np.minimum(1, np.maximum(0, (x - on) * 40))
        out += np.sin(2 * np.pi * f * rng.uniform(0.995, 1.005) * x) * e * (1 + 0.3 * np.sin(2 * np.pi * rng.uniform(3, 7) * x))
    return out / 7

def clink(base=2350, d=0.9):
    x = tt(d); out = np.zeros(len(x))
    for mult, tau, a in ((1, 0.30, 1.0), (1.69, 0.22, 0.6), (2.48, 0.15, 0.45), (3.36, 0.10, 0.3)):
        out += a * np.sin(2 * np.pi * base * mult * x) * np.exp(-x / tau)
    click = band(rng.standard_normal(len(x)), 3000, 12000) * np.exp(-x / 0.004) * 0.6
    return (out + click) / 2.4

def ice(d=1.0):
    out = np.zeros(int(d * SR)); at = 0.0
    for _ in range(5):
        c = clink(rng.uniform(1700, 3300), 0.35) * rng.uniform(0.4, 1.0)
        i = int(at * SR); out[i:i + len(c)] += c[: len(out) - i]
        at += rng.uniform(0.08, 0.2)
    return out

def pour(d=1.5):
    x = tt(d); n = band(rng.standard_normal(len(x)), 500, 5000)
    gurgle = 0.6 + 0.4 * np.clip(band(rng.standard_normal(len(x)), None, 16) * 6, -1, 1)
    env = np.minimum(1, x / 0.15) * np.minimum(1, (d - x) / 0.3)
    return n * gurgle * env

def hiss(d=1.6):
    x = tt(d); n = band(rng.standard_normal(len(x)), 3000, 9000)
    return n * np.sin(np.pi * x / d) ** 2

fx = np.zeros((N, 2))
T = starts + [BODY]
for k in (1, 2, 3, 4):
    place(fx, whoosh(), T[k] - 0.38, 0.11, pan=(-0.4 if k % 2 else 0.4))
place(fx, pour(1.5), shots["3a"] + 0.1, 0.05)
place(fx, ice(), shots["3b"] + 0.05, 0.10, pan=0.2)
place(fx, hiss(1.6), shots["3d"] + 0.1, 0.035, pan=-0.2)
place(fx, hiss(1.1), shots["3e"] + 0.05, 0.03, pan=0.2)
place(fx, clink(2480), shots["4b"] + 0.45, 0.11, pan=0.15)
place(fx, clink(2790), shots["4b"] + 0.52, 0.08, pan=-0.15)
place(fx, clink(2600), shots["5a"] + 0.35, 0.08)
place(fx, riser(2.0), BODY - 2.0, 0.22)
place(fx, impact(), BODY, 0.55)
place(fx, shimmer(), BODY + 0.55, 0.14, pan=-0.2)
place(fx, shimmer(3.0), BODY + 1.4, 0.09, pan=0.3)
place(fx, impact(2.0), BODY + 4.5, 0.22)
place(fx, shimmer(3.0), BODY + 5.4, 0.10)

# --- Narración ----------------------------------------------------------------
tono = cfg["voz"]["tono"]
voice = np.zeros(N); marks = []
for k, esc in enumerate(cfg["escenas"]):
    src = VOZ / f"linea_{k + 1}.wav"
    out = OUT / f"voz_{k + 1}.wav"
    chain = (f"asetrate=24000*{tono},aresample={SR},atempo={1 / tono:.5f},highpass=f=70,"
             "equalizer=f=115:t=q:w=0.9:g=2.5,equalizer=f=3200:t=q:w=1.2:g=2,"
             "acompressor=threshold=-21dB:ratio=3:attack=8:release=120:makeup=3,"
             "aecho=0.8:0.22:38:0.10")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", chain, "-ac", "1", "-ar", str(SR), str(out)], check=True)
    a, _ = sf.read(out)
    a = a / (np.sqrt(np.mean(a[np.abs(a) > 0.01] ** 2)) + 1e-9) * 0.11      # ~ -19 dBFS RMS
    at = starts[k] + esc["voz_en_pulso"] * BEAT
    i = int(at * SR); voice[i:i + len(a)] += a[: N - i]
    marks.append({"linea": k + 1, "texto": esc["narracion"], "entra": round(at, 2), "sale": round(at + len(a) / SR, 2)})
    assert at + len(a) / SR < T[k + 1] + 0.3, f"la línea {k + 1} no cabe en su escena"

# --- Música: se alinea su entrada fuerte con el inicio de la escena 4 -----------
y, _ = librosa.load(MUSIC, sr=22050, mono=True)
ons = librosa.onset.onset_strength(y=y, sr=22050, hop_length=256)
a0 = cfg["musica"]["acento_s"]
lo, hi = librosa.time_to_frames([a0 - 0.5, a0 + 0.5], sr=22050, hop_length=256)
accent = float(librosa.frames_to_time(lo + int(np.argmax(ons[lo:hi])), sr=22050, hop_length=256))
m_start = accent - cfg["musica"]["pulsos_hasta_acento"] * BEAT
m, _ = librosa.load(MUSIC, sr=SR, mono=False, offset=m_start, duration=TOTAL + 0.5)
m = m.T[:N]
if len(m) < N:
    m = np.vstack([m, np.zeros((N - len(m), 2))])
m = m / (np.sqrt(np.mean(m[int(25 * SR):int(35 * SR)] ** 2)) + 1e-9) * 0.13   # tramo fuerte ~ -18 dBFS
fade = np.ones(N); fi, fo = int(0.6 * SR), int(2.6 * SR)
fade[:fi] = np.linspace(0, 1, fi) ** 2; fade[-fo:] = np.linspace(1, 0, fo) ** 1.5
env = np.abs(voice)
win = int(0.25 * SR); env = np.convolve(env, np.ones(win) / win, mode="same")
env = np.clip(env / 0.05, 0, 1)
env = np.convolve(env, np.ones(win) / win, mode="same")
duck = 1 - 0.5 * env                                  # la música baja a la mitad bajo la voz
music = m * (fade * duck)[:, None]

mix = music + fx + voice[:, None] * 1.0
mix = np.tanh(mix * 1.15) / np.tanh(1.15) * 0.92      # limitador suave
mix = mix / np.max(np.abs(mix)) * 0.89
sf.write(OUT / "mezcla.wav", mix, SR)
sf.write(OUT / "solo_voz.wav", voice, SR)
(OUT / "audio.json").write_text(json.dumps({"total_s": round(TOTAL, 3), "cuerpo_s": round(BODY, 3),
    "musica_desde_s": round(m_start, 3), "acento_s": round(accent, 3), "escenas_s": [round(x, 3) for x in T],
    "narracion": marks}, ensure_ascii=False, indent=2))
print(json.dumps({"total": round(TOTAL, 2), "musica_desde": round(m_start, 2), "acento": round(accent, 2),
                  "narracion": [(m_["entra"], m_["sale"]) for m_ in marks]}))
