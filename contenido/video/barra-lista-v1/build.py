#!/usr/bin/env python3
"""Reel «Todo listo» de EXÓTICO: recorrido de la barra montada, editado al pulso de la música.

Uso:  python3 build.py <video_original.mp4> <musica.mp3> <carpeta_trabajo>

Toda la edición está en PLANOS. Requiere ffmpeg (con vid.stab), librosa, numpy,
soundfile y Node con Playwright (textos).
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf, librosa

SRC, MUSIC, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
HERE = Path(__file__).resolve().parent
WORK.mkdir(parents=True, exist_ok=True)
FPS, SR = 30, 48000
END_BEATS = 4                       # tarjeta final: 4 pulsos (~2 s)
LIFT_WINDOW = (60.0, 76.0)          # zona de la música donde buscar la subida de energía
REVEAL = 8                          # índice del plano que debe caer sobre esa subida

GRADE = ("curves=m='0/0 0.22/0.21 0.5/0.535 0.8/0.84 1/1',eq=contrast=1.07:saturation=1.12:gamma=1.02,"
         "colorbalance=rs=0.01:bs=0.015:rm=0.06:gm=0.012:bm=-0.065:rh=0.045:gh=0.01:bh=-0.06,vignette=PI/5.8")

# (inicio en el original, pulsos, velocidad, encuadre o None, ajuste extra o "", nota)
PLANOS = [
    (11.50, 3, 1.00, None, "", "GANCHO: barrido por las botellas"),
    (0.00, 4, 1.25, "crop=640:1138:40:142", "eq=gamma=1.18:brightness=0.02", "La barra completa (sin el letrero del local)"),
    (5.45, 2, 1.00, None, "", "Canela y plantas"),
    (6.95, 2, 1.00, None, "", "Siropes con vertedores"),
    (8.15, 2, 1.00, None, "", "Cocteleras tornasoladas"),
    (9.30, 2, 1.00, None, "", "Coladores y medidores"),
    (15.00, 2, 1.00, None, "", "Medidores y colador"),
    (16.05, 2, 1.00, None, "", "La mano sobre la barra"),
    (17.35, 4, 1.00, None, "", "REVELADO: la barra frente al lobby"),
]

def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)

# 1. Estabilización (vid.stab, dos pasadas) ----------------------------------------
estab = WORK / "estab.mp4"
if not estab.exists():
    trf = WORK / "transforms.trf"
    ff("-i", SRC, "-vf", f"vidstabdetect=shakiness=6:accuracy=15:result={trf}", "-f", "null", "-")
    ff("-i", SRC, "-vf", f"vidstabtransform=input={trf}:smoothing=18:optzoom=1:interpol=bicubic,unsharp=5:5:0.4",
       "-an", "-c:v", "libx264", "-crf", "10", "-preset", "medium", estab)

# 2. Pulsos de la música y punto de entrada -----------------------------------------
y, sr = librosa.load(MUSIC, sr=22050, mono=True, duration=110)  # el MP3 tiene un tramo dañado hacia el final
_, bf = librosa.beat.beat_track(y=y, sr=sr)
beats = librosa.frames_to_time(bf, sr=sr)
hop = sr // 2
rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2)) for i in range(0, len(y) - hop, hop)])
sm = np.convolve(rms, np.ones(4) / 4, mode="same")
lo, hi = int(LIFT_WINDOW[0] * 2), int(LIFT_WINDOW[1] * 2)
lift_t = (lo + int(np.argmax(np.diff(sm[lo:hi])))) / 2
reveal_beat = sum(p[1] for p in PLANOS[:REVEAL])
k_lift = int(np.argmin(np.abs(beats - lift_t)))
k0 = k_lift - reveal_beat
offset = float(beats[k0])
grid = beats[k0:] - offset                                    # pulsos relativos al inicio del video

# 3. Planos -------------------------------------------------------------------------
edl, concat, b = [], [], 0
for i, (start, nb, speed, crop, extra, note) in enumerate(PLANOS):
    f0, f1 = round(grid[b] * FPS), round(grid[b + nb] * FPS)
    n = f1 - f0
    chain = ",".join(x for x in (crop, "scale=1080:1920:flags=lanczos", extra, GRADE,
                                 f"setpts=PTS/{speed}" if speed != 1 else "", f"fps={FPS}", "format=yuv420p") if x)
    out = WORK / f"plano{i:02d}.mp4"
    ff("-ss", start, "-t", n / FPS * speed + 0.3, "-i", estab, "-vf", chain, "-frames:v", n, "-an",
       "-c:v", "libx264", "-preset", "medium", "-crf", "14", out)
    edl.append({"plano": i, "nota": note, "origen_s": start, "velocidad": speed,
                "entra": round(f0 / FPS, 3), "sale": round(f1 / FPS, 3)})
    concat.append(f"file '{out}'")
    b += nb
BODY = round(grid[b] * FPS) / FPS
END = round(grid[b + END_BEATS] * FPS) / FPS - BODY
TOTAL = BODY + END
(WORK / "lista.txt").write_text("\n".join(concat) + "\n")
ff("-f", "concat", "-safe", "0", "-i", WORK / "lista.txt", "-c", "copy", WORK / "cuerpo.mp4")

# 4. Textos ---------------------------------------------------------------------------
if not (WORK / "fin.png").exists():
    js = WORK / "textos.js"
    js.write_text("""
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 10000 } });
 await p.goto('file://%s', { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
 for (const id of ['base','t1','t2','t3','fin']) await p.locator('#'+id).screenshot({ path: '%s/' + id + '.png', omitBackground: true });
 await b.close(); })();""" % (HERE / "textos.html", WORK))
    subprocess.run(["node", str(js)], check=True)

e = {p["plano"]: p for p in edl}
T = {  # (entra, sale) de cada texto
    "t1": (0.25, e[1]["sale"] - 0.15),
    "t2": (e[3]["entra"] + 0.12, e[5]["sale"] - 0.15),
    "t3": (e[REVEAL]["entra"] + 0.55, BODY),
}

# 5. Sonido: música + dos efectos sintetizados ----------------------------------------
N = int(TOTAL * SR)
m, _ = librosa.load(MUSIC, sr=SR, mono=False, offset=offset, duration=TOTAL + 0.2)
m = m.T[:N]
fade = np.ones(N); fi, fo = int(0.08 * SR), int(0.9 * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo) ** 1.4
mix = m * fade[:, None] * 0.8
rng = np.random.default_rng(3)
def tt(d): return np.arange(int(d * SR)) / SR
def bandnoise(n, lo, hi):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(4, [lo, hi], btype="band", fs=SR, output="sos"), n)
def place(sig, at, g):
    i = int(at * SR); s = sig[: max(0, N - i)]
    mix[i:i + len(s)] += (s * g)[:, None]
d = 0.6; x = tt(d); u = x / d                                   # aire que entra al revelado
place(bandnoise(rng.standard_normal(len(x)), 600, 7000) * np.sin(np.pi * u) ** 2 * u, e[REVEAL]["entra"] - 0.45, 0.10)
x = tt(2.4); sh = np.zeros(len(x))                              # destello suave en la tarjeta final
for f in (2093, 2637, 3136, 3951, 5274):
    on = rng.uniform(0, 0.25); sh += np.sin(2 * np.pi * f * x) * np.where(x > on, np.exp(-(x - on) / 1.1), 0)
place(sh / 5, BODY + 0.05, 0.06)
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
sf.write(WORK / "audio.wav", mix, SR)

# 6. Exportación -------------------------------------------------------------------------
def export(with_text, name):
    inputs = ["-i", WORK / "cuerpo.mp4", "-loop", "1", "-t", END, "-i", WORK / "fin.png", "-i", WORK / "audio.wav"]
    fc = "[0:v]null[v0]"; last = "v0"
    if with_text:
        for k, nm in enumerate(["base", "t1", "t2", "t3"]):
            inputs += ["-loop", "1", "-t", BODY, "-i", WORK / f"{nm}.png"]
        a, z = 0.0, BODY
        fc += f";[3:v]format=rgba[b0];[{last}][b0]overlay[w0]"; last = "w0"
        for k, nm in enumerate(["t1", "t2", "t3"]):
            a, z = T[nm]
            out_fade = f",fade=t=out:st={z - 0.22}:d=0.22:alpha=1" if nm != "t3" else ""
            fc += (f";[{4 + k}:v]format=rgba,fade=t=in:st={a}:d=0.25:alpha=1{out_fade}[x{k}]"
                   f";[{last}][x{k}]overlay=enable='between(t,{a},{z})'[w{k + 1}]")
            last = f"w{k + 1}"
    fc += (f";[{last}]trim=duration={BODY},setpts=PTS-STARTPTS,setsar=1[body]"
           f";[1:v]fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.22,setsar=1[endv]"
           f";[body][endv]concat=n=2:v=1:a=0,format=yuv420p[v]"
           f";[2:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample={SR}[a]")
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", TOTAL, "-r", FPS,
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "10M", "-bufsize", "20M", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", WORK / name)

export(True, "exotico-todo-listo.mp4")
export(False, "exotico-todo-listo-sin-textos.mp4")
# Portada: fotograma del revelado con «Todo listo.» (el recorte 4:5 de la cuadrícula conserva el texto)
ff("-ss", round(e[REVEAL]["entra"] + 1.45, 2), "-i", WORK / "exotico-todo-listo.mp4", "-frames:v", "1", "-q:v", "2", WORK / "portada.jpg")
(HERE / "edl.json").write_text(json.dumps({
    "fps": FPS, "musica": MUSIC.name, "musica_desde_s": round(offset, 3), "subida_musica_s": round(lift_t, 2),
    "bpm": round(60 / float(np.median(np.diff(beats))), 2), "cuerpo_s": BODY, "total_s": round(TOTAL, 3),
    "textos": {k: [round(a, 2), round(z, 2)] for k, (a, z) in T.items()}, "planos": edl}, ensure_ascii=False, indent=2))
print("LISTO", round(TOTAL, 2), "s · música desde", round(offset, 2), "s")
