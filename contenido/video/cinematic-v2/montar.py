#!/usr/bin/env python3
"""Montaje final: etalonaje por ambiente, bloom y grano, bandas de cine, textos animados,
tarjeta final y banda sonora (música, sonido real de la barra y efectos sintetizados).

Uso: python3 montar.py <carpeta_planos> <musica.mp3> <original.mp4> <carpeta_salida>
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

HERE = Path(__file__).resolve().parent
PLANOS, MUSIC, SRC, OUT = (Path(p).resolve() for p in sys.argv[1:5])
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((HERE / "planos.json").read_text())
edl = json.loads((HERE / "edl.json").read_text())
FPS, W, H, SR = edl["fps"], edl["ancho"], edl["alto"], 48000
BAR = (1920 - H) // 2
BEAT = edl["beat"]
BODY, END = edl["cuerpo_s"], edl["fin_s"]
TOTAL = BODY + END
E = {e["plano"]: e for e in edl["planos"]}
P = {p["id"]: p for p in cfg["planos"]}
HIT = E["rojo"]["entra"]                         # el golpe de la música cae en el primer corte a la barra

def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)

# 1. Etalonaje -----------------------------------------------------------------------------
LOOK = {
    "barra": ("curves=m='0/0 0.12/0.095 0.5/0.5 0.86/0.885 1/0.975',eq=contrast=1.07:saturation=1.06:gamma=0.985,"
              "colorbalance=rs=-0.02:gs=0:bs=0.035:rm=0.05:gm=0.012:bm=-0.055:rh=0.045:gh=0.012:bh=-0.075"),
    # El salón está iluminado con LED morado: se templa a ámbar y se apagan azules y magentas
    "salon": ("colortemperature=temperature=3300:mix=0.95,"
              "selectivecolor=blues=0.4 0.15 -0.45 0.1:magentas=0.3 -0.4 0.35 0.05,hue=s=0.62,"
              "curves=m='0/0 0.14/0.12 0.5/0.52 0.86/0.88 1/0.975',eq=contrast=1.1:gamma=1.04,"
              "colorbalance=rs=0.03:gs=0.01:bs=-0.04:rm=0.12:gm=0.04:bm=-0.14:rh=0.07:gh=0.03:bh=-0.09"),
}
BLOOM = ("split[b][hl];[hl]colorlevels=rimin=0.74:gimin=0.74:bimin=0.74,gblur=sigma=26,"
         "colorbalance=rm=0.1:bm=-0.1[glow];[b][glow]blend=all_mode=screen:all_opacity=0.26")
GRAIN = "noise=c0s=5:c0f=t+u:c1s=2:c1f=t+u:c2s=2:c2f=t+u,vignette=PI/4.9"

graded = []
for i, e in enumerate(edl["planos"]):
    src = PLANOS / f"{i:02d}_{e['plano']}.mp4"
    dst = OUT / f"g_{i:02d}_{e['plano']}.mp4"
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        ff("-i", src, "-vf", f"{BLOOM},{LOOK[P[e['plano']]['luz']]},{GRAIN},format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", "11", dst)
        print("etalonado", e["plano"], flush=True)
    graded.append(dst)
(OUT / "lista.txt").write_text("".join(f"file '{g}'\n" for g in graded))
ff("-f", "concat", "-safe", "0", "-i", OUT / "lista.txt", "-c", "copy", OUT / "cuerpo.mp4")

# 2. Textos ---------------------------------------------------------------------------------
if not (OUT / "fin.png").exists():
    (OUT / "textos.js").write_text("""
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 14000 } });
 await p.goto('file://%s', { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
 for (const id of ['base','t1','t2','t3','t4','fin']) await p.locator('#'+id).screenshot({ path: '%s/' + id + '.png', omitBackground: true });
 await b.close(); })();""" % (HERE / "textos.html", OUT))
    subprocess.run(["node", str(OUT / "textos.js")], check=True)
TEXTOS = {
    "t1": (1.0, E["humo"]["sale"] - 0.9),
    "t2": (E["agitado"]["entra"] + 0.08, E["brazo"]["sale"] - 0.12),
    "t3": (E["naranja"]["entra"] + 0.3, E["naranja"]["sale"] - 0.15),
    "t4": (E["reaccion"]["entra"] + 0.25, E["nube"]["sale"] - 0.4),
}

# 3. Banda sonora ------------------------------------------------------------------------------
N = int(TOTAL * SR)
mix = np.zeros((N, 2))
def tt(d): return np.arange(int(d * SR)) / SR
def band(x, lo=None, hi=None):
    if lo and hi: sos = butter(4, [lo, hi], btype="band", fs=SR, output="sos")
    elif lo: sos = butter(4, lo, btype="high", fs=SR, output="sos")
    else: sos = butter(4, hi, btype="low", fs=SR, output="sos")
    return sosfilt(sos, x)
def place(sig, at, g, pan=0.0):
    i = int(at * SR)
    if i < 0: sig = sig[-i:]; i = 0
    s = sig[: max(0, N - i)]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    if s.ndim == 1: mix[i:i + len(s), 0] += s * g * l; mix[i:i + len(s), 1] += s * g * r
    else: mix[i:i + len(s)] += s * g

# 3a. Música: golpe medido en la pista, alineado con HIT; intro filtrada que se abre en el golpe
y, sr0 = librosa.load(MUSIC, sr=22050, mono=True, offset=50, duration=5)
oenv = librosa.onset.onset_strength(y=y, sr=sr0, hop_length=128)
t = librosa.frames_to_time(np.arange(len(oenv)), sr=sr0, hop_length=128) + 50
m = (t > 52.2) & (t < 52.7)
hit_track = float(t[np.argmax(oenv * m)])
offset = hit_track - HIT
mus, _ = librosa.load(MUSIC, sr=SR, mono=False, offset=offset, duration=TOTAL + 0.5)
mus = mus.T[:N]
if len(mus) < N: mus = np.vstack([mus, np.zeros((N - len(mus), 2))])
ih = int(HIT * SR); xf = int(0.35 * SR)
intro = np.stack([band(mus[:ih + xf, c], hi=900) for c in range(2)], 1) * 1.25
w = np.ones(ih + xf); w[ih:] = np.linspace(1, 0, xf)
mus[:ih + xf] = intro * w[:, None] + mus[:ih + xf] * (1 - w)[:, None]
fade = np.ones(N); fi = int(0.5 * SR); fo = int((END + 0.6) * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo) ** 1.4
mix += mus * (fade * 0.8)[:, None]

# 3b. Sonido real de la barra: solo el brillo (>1.8 kHz) para no arrastrar la canción del local;
#     en los tramos lentos se estira con rubberband y baja de tono
wav = OUT / "original_audio.wav"
if not wav.exists(): ff("-i", SRC, "-vn", "-ac", "1", "-ar", SR, wav)
def segments(p, e):
    """Divide el plano según su curva de velocidad: [(t_out_ini, t_out_fin, t_src_ini, velocidad_media)]."""
    dur = e["sale"] - e["entra"]; v = p["vel"]; segs = []; s = p["src"]
    for (u0, s0), (u1, s1) in zip(v, v[1:]):
        if u1 <= u0: continue
        d = (u1 - u0) * dur; sp = (s0 + s1) / 2
        segs.append((e["entra"] + u0 * dur, e["entra"] + u1 * dur, s, sp)); s += d * sp
    return segs
amb = np.zeros(N)
for pid, e in E.items():
    for (a, z, s, sp) in segments(P[pid], e):
        d = z - a
        snippet = OUT / f"_amb_{pid}_{int(a*100)}.wav"
        if sp >= 0.97:
            ff("-ss", f"{s:.4f}", "-t", f"{d + 0.05:.4f}", "-i", wav, "-af", "highpass=f=1800,highpass=f=1800", snippet)
        else:
            ff("-ss", f"{s:.4f}", "-t", f"{d * sp + 0.05:.4f}", "-i", wav,
               "-af", f"highpass=f=1200,rubberband=tempo={sp:.4f}:pitch={max(0.5, sp ** 0.5):.3f},lowpass=f=6000", snippet)
        x, _ = sf.read(snippet); x = x[: int(d * SR)]
        r = int(0.03 * SR); x[:r] *= np.linspace(0, 1, r); x[-r:] *= np.linspace(1, 0, r)
        i = int(a * SR); amb[i:i + len(x)] += x
amb = amb / (np.sqrt(np.mean(amb[np.abs(amb) > 1e-4] ** 2)) + 1e-9) * 0.05      # ~ -26 dBFS
mix += amb[:, None]

# 3c. Efectos sintetizados
rng = np.random.default_rng(21)
x = tt(HIT); u = x / HIT                                              # dron grave bajo el humo
drone = (np.sin(2 * np.pi * 55 * x) * 0.5 + np.sin(2 * np.pi * 82.5 * x) * 0.25) * (0.3 + 0.7 * u) * np.minimum(1, x / 1.5)
place(drone * np.minimum(1, (HIT - x) / 0.2), 0, 0.12)
x = tt(4 * BEAT); u = x / x[-1]                                        # subida de un compás
place(band(rng.standard_normal(len(x)), 900, 10000) * u ** 2.8 * np.minimum(1, (1 - u) * 50), HIT - 4 * BEAT, 0.2)
x = tt(2.2); f = 42 + 40 * np.exp(-x / 0.09)                            # golpe grave en el corte
place(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.5), HIT, 0.55)
place(band(rng.standard_normal(len(x)), None, 180) * np.exp(-x / 0.06), HIT, 0.5)
for pid, u0 in (("chorro", 0.22), ("arriba", 0.2), ("nube", 0.0)):     # aire al entrar en cámara lenta
    e = E[pid]; at = e["entra"] + u0 * (e["sale"] - e["entra"]) - 0.5
    d = 0.7; x = tt(d); u = x / d
    place(band(rng.standard_normal(len(x)), 400, 7000) * np.sin(np.pi * u) ** 2 * (0.4 + 0.6 * u), at, 0.1, pan=0.25)
    x = tt(1.6); f = 48 + 30 * np.exp(-x / 0.12)                        # y un golpe sordo al entrar
    place(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.4), at + 0.5, 0.22)
x = tt(1.4); u = x / 1.4                                                # swell inverso hacia la tarjeta final
place(band(rng.standard_normal(len(x)), 300, 5000) * u ** 3 * np.minimum(1, (1 - u) * 30), BODY - 1.35, 0.14)
x = tt(2.6); sh = np.zeros(len(x))                                      # destello dorado en la tarjeta
for fq in (2093, 2637, 3136, 3951, 5274):
    on = rng.uniform(0, 0.25); sh += np.sin(2 * np.pi * fq * x) * np.where(x > on, np.exp(-(x - on) / 1.1), 0)
place(sh / 5, BODY + 0.05, 0.06)
x = tt(2.0); f = 40 + 34 * np.exp(-x / 0.1)
place(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.45), BODY, 0.3)

mix = np.tanh(mix * 1.08) / np.tanh(1.08)
sf.write(OUT / "audio.wav", mix, SR)

# 4. Exportación -----------------------------------------------------------------------------------
def export(with_text, name):
    inputs = ["-i", OUT / "cuerpo.mp4", "-loop", "1", "-t", END, "-i", OUT / "fin.png", "-i", OUT / "audio.wav"]
    fc = f"[0:v]pad=1080:1920:0:{BAR}:black[v0]"; last = "v0"
    if with_text:
        inputs += ["-loop", "1", "-t", BODY, "-i", OUT / "base.png"]
        fc += f";[3:v]format=rgba,fade=t=in:st=0.6:d=1.2:alpha=1[bs];[{last}][bs]overlay[w0]"; last = "w0"
        for k, nm in enumerate(["t1", "t2", "t3", "t4"]):
            inputs += ["-loop", "1", "-t", BODY, "-i", OUT / f"{nm}.png"]
            a, z = TEXTOS[nm]; fin_, fout = 0.7, 0.5
            fc += (f";[{4 + k}:v]format=rgba,fade=t=in:st={a}:d={fin_}:alpha=1,fade=t=out:st={z - fout}:d={fout}:alpha=1[x{k}]"
                   f";[{last}][x{k}]overlay=y='18*pow(1-min(1,max(0,(t-{a})/{fin_ + 0.3})),2)':enable='between(t,{a},{z})'[w{k + 1}]")
            last = f"w{k + 1}"
    fc += (f";[{last}]trim=duration={BODY},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.8,fade=t=out:st={BODY - 0.45}:d=0.45,setsar=1[body]"
           f";[1:v]fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.5,setsar=1[endv]"
           f";[body][endv]concat=n=2:v=1:a=0,format=yuv420p[v]"
           f";[2:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample={SR}[a]")
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", TOTAL, "-r", FPS,
       "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-maxrate", "14M", "-bufsize", "28M", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", OUT / name)

export(True, "exotico-the-art-v2.mp4")
export(False, "exotico-the-art-v2-sin-textos.mp4")
(HERE / "mezcla.json").write_text(json.dumps({"musica": MUSIC.name, "golpe_en_pista_s": round(hit_track, 3),
    "musica_desde_s": round(offset, 3), "golpe_en_reel_s": HIT, "total_s": round(TOTAL, 3),
    "textos": {k: [round(a, 2), round(z, 2)] for k, (a, z) in TEXTOS.items()}}, ensure_ascii=False, indent=2))
print("LISTO", round(TOTAL, 2), "s · música desde", round(offset, 2), "s · golpe", HIT, "s")
