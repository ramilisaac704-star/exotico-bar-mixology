#!/usr/bin/env python3
"""Montaje del reel promocional: etalonaje por fuente, transiciones (flash y barrido),
textos, tarjeta final animada y banda sonora (música, efectos sintetizados, sonido real).

Uso: python3 montar.py <carpeta_planos> <musica.mp3> <carpeta_fuentes> <carpeta_salida>
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfilt

HERE = Path(__file__).resolve().parent
PLANOS, MUSIC, SRCDIR, OUT = (Path(p).resolve() for p in sys.argv[1:5])
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((HERE / "planos.json").read_text())
edl = json.loads((HERE / "edl.json").read_text())
FPS, SR, BEAT = edl["fps"], 48000, edl["beat"]
BODY, END = edl["cuerpo_s"], edl["fin_s"]
TOTAL = BODY + END
E = {e["plano"]: e for e in edl["planos"]}
P = {p["id"]: p for p in cfg["planos"]}
HIT = E["cabeza"]["entra"]                       # entrada de la música

def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)

# 1. Etalonaje (el bloom se mezcla en RGB: en YUV desplaza el color hacia magenta) --------
BLOOM = ("format=gbrp,split[b][hl];[hl]colorlevels=rimin=0.72:gimin=0.72:bimin=0.72,gblur=sigma=22,"
         "colorbalance=rm=0.1:bm=-0.12[glow];[b][glow]blend=all_mode=screen:all_opacity=0.28")
FIN = "vibrance=intensity=0.18,noise=c0s=5:c0f=t+u:c1s=2:c1f=t+u:c2s=2:c2f=t+u,vignette=PI/4.8"
LOOK = {
    "dia": ("curves=m='0/0 0.1/0.065 0.5/0.48 0.9/0.92 1/0.97',eq=contrast=1.1:saturation=1.08:gamma=0.95,"
            "colorbalance=rs=-0.02:gs=0:bs=0.03:rm=0.05:gm=0.01:bm=-0.06:rh=0.05:gh=0.02:bh=-0.08"),
    "noche": ("curves=m='0/0 0.1/0.07 0.5/0.5 0.9/0.93 1/0.98',eq=contrast=1.1:saturation=1.0:gamma=1.0,"
              "colorbalance=rs=0.03:gs=0:bs=-0.05:rm=0.03:gm=0:bm=-0.06:rh=0.04:gh=0.02:bh=-0.07"),
    "calido": ("curves=m='0/0 0.1/0.075 0.5/0.52 0.9/0.92 1/0.97',eq=contrast=1.07:saturation=1.1:gamma=1.04,"
               "colorbalance=rs=-0.02:bs=0.02:rm=0.04:gm=0.01:bm=-0.05:rh=0.04:gh=0.02:bh=-0.06"),
    "barra_j": ("curves=m='0/0 0.1/0.075 0.5/0.51 0.88/0.9 1/0.975',eq=contrast=1.08:saturation=1.02,"
                "colorbalance=rs=-0.02:gs=0.01:bs=0.02:rm=0.04:gm=0.02:bm=-0.06:rh=0.045:gh=0.025:bh=-0.08"),
    "salon": ("colortemperature=temperature=3300:mix=0.95,selectivecolor=blues=0.4 0.15 -0.45 0.1:magentas=0.3 -0.4 0.35 0.05,"
              "hue=s=0.62,curves=m='0/0 0.12/0.1 0.5/0.52 0.86/0.88 1/0.975',eq=contrast=1.1:gamma=1.04,"
              "colorbalance=rs=0.03:gs=0.01:bs=-0.04:rm=0.12:gm=0.04:bm=-0.14:rh=0.07:gh=0.03:bh=-0.09"),
}
graded = []
for i, e in enumerate(edl["planos"]):
    src = PLANOS / f"{i:02d}_{e['plano']}.mp4"
    dst = OUT / f"g_{i:02d}_{e['plano']}.mp4"
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        ff("-i", src, "-vf", f"{BLOOM},{LOOK[P[e['plano']]['luz']]},{FIN},format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", "11", dst)
        print("etalonado", e["plano"], flush=True)
    graded.append(dst)
(OUT / "lista.txt").write_text("".join(f"file '{g}'\n" for g in graded))
ff("-f", "concat", "-safe", "0", "-i", OUT / "lista.txt", "-c", "copy", OUT / "cuerpo.mp4")

# 2. Textos y tarjeta final ----------------------------------------------------------------
if not (OUT / "t4.png").exists():
    (OUT / "textos.js").write_text("""
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 12000 } });
 await p.goto('file://%s', { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
 for (const id of ['base','t1','t2','t3','t4']) await p.locator('#'+id).screenshot({ path: '%s/' + id + '.png', omitBackground: true });
 await b.close(); })();""" % (HERE / "textos.html", OUT))
    subprocess.run(["node", str(OUT / "textos.js")], check=True)
fin_dir = OUT / "fin"; fin_dir.mkdir(exist_ok=True)
n_fin = round(END * FPS)
if len(list(fin_dir.glob("*.jpg"))) != n_fin:
    (OUT / "fin.js").write_text("""
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
 await p.goto('file://%s', { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
 for (let i = 0; i < %d; i++) { await p.evaluate(t => render(t), i / %d);
   await p.screenshot({ path: '%s/f' + String(i).padStart(4, '0') + '.jpg', type: 'jpeg', quality: 95 }); }
 await b.close(); })();""" % (HERE / "marca_fin.html", n_fin, FPS, fin_dir))
    subprocess.run(["node", str(OUT / "fin.js")], check=True)
ff("-framerate", FPS, "-i", fin_dir / "f%04d.jpg", "-vf", "noise=c0s=3:c0f=t+u,format=yuv420p", "-c:v", "libx264", "-crf", "12", OUT / "fin.mp4")

TEXTOS = {   # (entra, sale, desplazamiento vertical en px: negativo = más arriba)
    "t1": (E["botellas"]["entra"] + 0.1, E["doble"]["sale"] - 0.12, 0),
    "t2": (E["arriba"]["entra"] + 0.1, E["arriba"]["sale"] - 0.12, 0),
    "t3": (E["entrega"]["entra"] + 0.15, E["entrega"]["sale"] - 0.1, -1000),   # arriba: el vaso ocupa la mitad inferior
    "t4": (E["nube"]["entra"] + 0.1, BODY - 0.12, 0),
}
FLASH = [HIT, BODY]                                      # destellos de corte
WHIP = [E["lanza"]["entra"], E["arriba"]["entra"]]       # barridos con desenfoque direccional

# 3. Banda sonora ---------------------------------------------------------------------------------
N = int(TOTAL * SR)
mix = np.zeros((N, 2))
rng = np.random.default_rng(5)
def tt(d): return np.arange(int(d * SR)) / SR
def band(x, lo=None, hi=None):
    sos = (butter(4, [lo, hi], btype="band", fs=SR, output="sos") if lo and hi else
           butter(4, lo, btype="high", fs=SR, output="sos") if lo else butter(4, hi, btype="low", fs=SR, output="sos"))
    return sosfilt(sos, x, axis=0)
def place(sig, at, g, pan=0.0):
    i = int(at * SR)
    if i < 0: sig = sig[-i:]; i = 0
    s = sig[: max(0, N - i)]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    mix[i:i + len(s), 0] += s * g * l; mix[i:i + len(s), 1] += s * g * r

y, sr0 = librosa.load(MUSIC, sr=22050, mono=True, offset=6.0, duration=2.0)
oenv = librosa.onset.onset_strength(y=y, sr=sr0, hop_length=128)
tt0 = librosa.frames_to_time(np.arange(len(oenv)), sr=sr0, hop_length=128) + 6.0
m = (tt0 > 6.8) & (tt0 < 7.4)
drop = float(tt0[np.argmax(oenv * m)])
offset = drop - HIT
mus, _ = librosa.load(MUSIC, sr=SR, mono=False, offset=offset, duration=TOTAL + 0.5)
mus = mus.T[:N]
if len(mus) < N: mus = np.vstack([mus, np.zeros((N - len(mus), 2))])
# Final: barrido de filtro hacia graves y desvanecido sobre la tarjeta
low = band(mus, hi=500)
k = np.clip((np.arange(N) / SR - BODY) / 1.6, 0, 1)[:, None]
mus = mus * (1 - k) + low * 1.4 * k
fo = np.clip(1 - (np.arange(N) / SR - BODY - 0.6) / (END - 0.6), 0, 1) ** 1.3
mix += mus * (0.85 * fo)[:, None]

# Sonido real de la barra (solo brillo > 2,5 kHz: el hielo y el metal, sin la música del local)
srcs = {k: SRCDIR / v for k, v in cfg["fuentes"].items()}
for pid in ("cabeza", "jugo", "doble", "prepara", "pecho", "presenta", "entrega"):
    e, p = E[pid], P[pid]
    d = e["sale"] - e["entra"]
    wav = OUT / f"_amb_{pid}.wav"
    ff("-ss", p["src"], "-t", d, "-i", srcs[p["fuente"]], "-vn", "-ac", "1", "-ar", SR,
       "-af", "highpass=f=2500,highpass=f=2500,lowpass=f=11000", wav)
    a, _ = sf.read(wav); a = a[: int(d * SR)]
    r = int(0.02 * SR); a[:r] *= np.linspace(0, 1, r); a[-r:] *= np.linspace(1, 0, r)
    rms = np.sqrt(np.mean(a ** 2)) + 1e-9
    place(a / rms * 0.03, e["entra"], 1.0)

# Efectos sintetizados
x = tt(HIT); u = x / HIT                                             # subida bajo el humo
place(band(rng.standard_normal(len(x)), 900, 10000) * u ** 2.6 * np.minimum(1, (1 - u) * 60), 0, 0.22)
drone = np.sin(2 * np.pi * 55 * x) * 0.6 + np.sin(2 * np.pi * 82.4 * x) * 0.3
place(drone * np.minimum(1, x / 0.4) * np.minimum(1, (HIT - x) / 0.1), 0, 0.09)
for at, g in ((HIT, 0.6), (BODY, 0.42)):                             # golpes graves
    x = tt(2.2); f = 42 + 42 * np.exp(-x / 0.08)
    place(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.5), at, g)
    place(band(rng.standard_normal(len(x)), None, 200) * np.exp(-x / 0.05), at, g * 0.8)
for c in WHIP:                                                       # barridos
    d = 0.42; x = tt(d); u = x / d
    place(band(rng.standard_normal(len(x)), 600, 8000) * np.sin(np.pi * u) ** 2, c - d * 0.6, 0.14, pan=-0.3)
for pid in ("lanza", "arriba", "alto"):                               # aire al entrar en cámara lenta
    e, v = E[pid], P[pid]["vel"]
    u0 = next(uu for uu, s in v if s < 0.9)
    at = e["entra"] + u0 * (e["sale"] - e["entra"])
    d = 0.6; x = tt(d); w = x / d
    place(band(rng.standard_normal(len(x)), 400, 7000) * np.sin(np.pi * w) ** 2 * (0.4 + 0.6 * w), at - 0.45, 0.1, pan=0.25)
    x = tt(1.4); f = 50 + 30 * np.exp(-x / 0.1)
    place(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.35), at, 0.2)
x = tt(2.6); sh = np.zeros(len(x))                                    # destello en la tarjeta
for fq in (2093, 2637, 3136, 3951, 5274):
    on = rng.uniform(0, 0.25); sh += np.sin(2 * np.pi * fq * x) * np.where(x > on, np.exp(-(x - on) / 1.0), 0)
place(sh / 5, BODY + 0.1, 0.07)

mix = np.tanh(mix * 1.08) / np.tanh(1.08)
sf.write(OUT / "audio.wav", mix, SR)

# 4. Exportación -------------------------------------------------------------------------------------
def body_fx():
    fx = []
    for t in FLASH[:-1]:
        fx += [f"eq=brightness=0.24:saturation=0.85:enable='between(t,{t:.3f},{t + 0.034:.3f})'",
               f"eq=brightness=0.10:enable='between(t,{t + 0.034:.3f},{t + 0.07:.3f})'"]
    for c in WHIP:
        fx.append(f"gblur=sigma=34:sigmaV=0.6:steps=2:enable='between(t,{c - 0.05:.3f},{c + 0.05:.3f})'")
    fx.append(f"eq=brightness=0.18:enable='between(t,{BODY - 0.067:.3f},{BODY:.3f})'")
    return ",".join(fx)

def export(with_text, name):
    inputs = ["-i", OUT / "cuerpo.mp4", "-i", OUT / "fin.mp4", "-i", OUT / "audio.wav"]
    fc = f"[0:v]{body_fx()}[v0]"; last = "v0"
    if with_text:
        inputs += ["-loop", "1", "-t", BODY, "-i", OUT / "base.png"]
        fc += f";[3:v]format=rgba,fade=t=in:st={HIT + 0.1}:d=0.5:alpha=1[bs];[{last}][bs]overlay=enable='gte(t,{HIT})'[w0]"; last = "w0"
        for k, nm in enumerate(["t1", "t2", "t3", "t4"]):
            inputs += ["-loop", "1", "-t", BODY, "-i", OUT / f"{nm}.png"]
            a, z, dy = TEXTOS[nm]
            fc += (f";[{4 + k}:v]format=rgba,fade=t=in:st={a}:d=0.35:alpha=1,fade=t=out:st={z - 0.25}:d=0.25:alpha=1[x{k}]"
                   f";[{last}][x{k}]overlay=y='{dy}+14*pow(1-min(1,max(0,(t-{a})/0.6)),2)':enable='between(t,{a},{z})'[w{k + 1}]")
            last = f"w{k + 1}"
    fc += (f";[{last}]trim=duration={BODY},setpts=PTS-STARTPTS,setsar=1[body]"
           f";[1:v]fps={FPS},format=yuv420p,setsar=1[endv]"
           f";[body][endv]concat=n=2:v=1:a=0,format=yuv420p[v]"
           f";[2:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample={SR}[a]")
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", TOTAL, "-r", FPS,
       "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "14M", "-bufsize", "28M", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", OUT / name)

export(True, "exotico-promo.mp4")
export(False, "exotico-promo-sin-textos.mp4")
(HERE / "mezcla.json").write_text(json.dumps({"musica": MUSIC.name, "golpe_en_pista_s": round(drop, 3),
    "musica_desde_s": round(offset, 3), "golpe_en_reel_s": HIT, "total_s": round(TOTAL, 3),
    "textos": {k: [round(a, 2), round(z, 2)] for k, (a, z, _) in TEXTOS.items()}}, ensure_ascii=False, indent=2))
print("LISTO", round(TOTAL, 2), "s · música desde", round(offset, 2), "s · golpe", HIT, "s")
