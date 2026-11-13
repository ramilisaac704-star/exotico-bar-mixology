#!/usr/bin/env python3
"""Montaje final del comercial: planos + etalonaje + subtítulos + marca + banda sonora.

Uso: python3 montar.py <carpeta_planos> <carpeta_marca> <carpeta_audio> <carpeta_salida>
Requiere ffmpeg y Node con Playwright (subtítulos).
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLANOS, MARCA, AUDIO, OUT = (Path(p) for p in sys.argv[1:5])
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((HERE / "montaje.json").read_text())
edl = json.loads((HERE / "edl.json").read_text())
au = json.loads((AUDIO / "audio.json").read_text())
FPS = cfg["fps"]; BODY = edl["cuerpo_s"]; BRAND = cfg["marca_s"]; TOTAL = BODY + BRAND

def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)

# 1. Subtítulos: una frase larga se parte en dos pantallas --------------------
subs = []
for n in au["narracion"]:
    text, a, b = n["texto"].replace("...", "…"), n["entra"], n["sale"]
    parts = [text]
    if len(text) > 70 and ", y " in text:
        i = text.index(", y ")
        parts = [text[: i + 1], text[i + 2:]]
    total = sum(len(p) for p in parts); t = a
    for p in parts:
        d = (b - a) * len(p) / total
        subs.append({"texto": p.strip().rstrip(","), "entra": round(t, 2), "sale": round(t + d, 2)})
        t += d
subs[-1]["sale"] += 0.3
html = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@1,500;1,600&display=swap" rel="stylesheet">
<style>*{margin:0;padding:0}body{background:transparent}
.f{width:1080px;height:1920px;position:relative}
.s{position:absolute;left:90px;right:90px;bottom:350px;text-align:center;font-family:'Cormorant Garamond',serif;font-style:italic;
font-weight:600;font-size:60px;line-height:1.18;color:#f6ecd8;text-shadow:0 2px 6px rgba(0,0,0,.85),0 0 34px rgba(0,0,0,.75),0 0 80px rgba(0,0,0,.5);text-wrap:balance}
</style></head><body>%s</body></html>""" % "".join(
    f'<div class="f" id="s{i}"><div class="s">{s["texto"]}</div></div>' for i, s in enumerate(subs))
(OUT / "subs.html").write_text(html)
(OUT / "subs.js").write_text("""
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 4000 } });
 await p.goto('file://%s', { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
 for (let i = 0; i < %d; i++) await p.locator('#s' + i).screenshot({ path: '%s/s' + i + '.png', omitBackground: true });
 await b.close(); })();""" % (OUT / "subs.html", len(subs), OUT))
subprocess.run(["node", str(OUT / "subs.js")], check=True)

# 2. Cuerpo: planos en orden, corte directo al pulso -----------------------------
(OUT / "lista.txt").write_text("".join(f"file '{PLANOS / (p['plano'] + '.mp4')}'\n" for p in edl["planos"]))
ff("-f", "concat", "-safe", "0", "-i", OUT / "lista.txt", "-c", "copy", OUT / "cuerpo.mp4")

# 3. Marca: secuencia de fotogramas ----------------------------------------------
ff("-framerate", FPS, "-i", MARCA / "m%04d.jpg", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", OUT / "marca.mp4")

GRADE = ("eq=contrast=1.05:saturation=1.07:gamma=0.98,"
         "colorbalance=rs=0.035:bs=-0.04:rm=0.02:bm=-0.02:rh=0.015:bh=-0.03,"
         "vignette=PI/6,noise=alls=5:allf=t+u")

def export(with_subs, name):
    inputs = ["-i", OUT / "cuerpo.mp4", "-i", OUT / "marca.mp4", "-i", AUDIO / "mezcla.wav"]
    fc = f"[0:v]{GRADE}[g]"; last = "g"
    if with_subs:
        for i, s in enumerate(subs):
            inputs += ["-loop", "1", "-t", BODY, "-i", OUT / f"s{i}.png"]
            a, b = s["entra"], s["sale"]
            fc += (f";[{3 + i}:v]format=rgba,fade=t=in:st={a}:d=0.25:alpha=1,fade=t=out:st={b - 0.25}:d=0.25:alpha=1[c{i}]"
                   f";[{last}][c{i}]overlay=enable='between(t,{a},{b})'[o{i}]")
            last = f"o{i}"
    fc += (f";[{last}]trim=duration={BODY},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.5,fade=t=out:st={BODY - 0.3}:d=0.3,setsar=1[body]"
           f";[1:v]fps={FPS},fade=t=in:st=0:d=0.25,fade=t=out:st={BRAND - 0.5}:d=0.5,setsar=1[brand]"
           f";[body][brand]concat=n=2:v=1:a=0,format=yuv420p[v]"
           f";[2:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", TOTAL,
       "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "9M", "-bufsize", "18M", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT / name)

export(True, "exotico-the-art-of-the-experience.mp4")
export(False, "exotico-the-art-of-the-experience-sin-subtitulos.mp4")
(HERE / "subtitulos.json").write_text(json.dumps(subs, ensure_ascii=False, indent=2))
print("LISTO", round(TOTAL, 2), "s")
