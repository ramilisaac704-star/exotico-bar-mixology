#!/usr/bin/env python3
"""Reel «Experiencia» de EXÓTICO, editado desde el original 4K a 60 fps.

Uso:  python3 build.py <original.mp4> <musica.mp3> <carpeta_trabajo>

- Montaje: planos.json (encuadre sobre el 4K, velocidad, pulsos, luz).
- Cámara lenta real: los planos a 0.5 usan los fotogramas de 60 fps (sin inventar fotogramas).
- La música entra en silencio y el primer corte a la barra cae en su entrada fuerte.
- El audio real de la barra se conserva por debajo, sin la canción del local.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf, librosa

SRC, MUSIC, WORK = (Path(p).resolve() for p in sys.argv[1:4])
HERE = Path(__file__).resolve().parent
WORK.mkdir(parents=True, exist_ok=True)
cfg = json.loads((HERE / "planos.json").read_text())
FPS, SR = 30, 48000
BEAT = 60.0 / cfg["bpm"]

GRADE = {
    "barra": ("curves=m='0/0 0.18/0.155 0.5/0.5 0.82/0.86 1/0.97',eq=contrast=1.08:saturation=1.10:gamma=0.97,"
              "colorbalance=rs=0.02:bs=-0.03:rm=0.045:gm=0.01:bm=-0.055:rh=0.03:gh=0.005:bh=-0.07,vignette=PI/5"),
    "salon": ("colortemperature=temperature=4300:mix=0.55,curves=m='0/0 0.2/0.19 0.5/0.52 0.85/0.87 1/0.98',"
              "eq=contrast=1.07:saturation=0.86:gamma=1.04,"
              "colorbalance=rs=0.04:bs=-0.06:rm=0.07:gm=0.01:bm=-0.09:rh=0.03:bh=-0.06,vignette=PI/4.6"),
}
GRAIN = "noise=alls=4:allf=t,unsharp=5:5:0.35"

def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)

# 1. Rejilla de pulsos: el plano 1 dura la introducción y el 2 cae en el drop ---------
planos = cfg["planos"]
drop = cfg["drop_musica_s"]
m_start = drop - planos[0]["pulsos"] * BEAT
cuts = np.cumsum([0] + [p["pulsos"] for p in planos]) * BEAT
fr = np.round(cuts * FPS).astype(int)
BODY = fr[-1] / FPS
END = round(cfg["fin_pulsos"] * BEAT * FPS) / FPS
TOTAL = BODY + END

# 2. Planos desde el 4K -----------------------------------------------------------------
concat, edl = [], []
for i, p in enumerate(planos):
    n = int(fr[i + 1] - fr[i])
    x, y, w, h = p["crop"]
    v = p["vel"]
    src_dur = n / FPS * v
    out = WORK / f"{i:02d}_{p['id']}.mp4"
    stamp = WORK / f"{i:02d}_{p['id']}.json"
    meta = {k: p[k] for k in ("src", "pulsos", "vel", "crop", "luz", "estab")} | {"n": n}
    if not (out.exists() and stamp.exists() and json.loads(stamp.read_text()) == meta):
        # a) recorte del tramo exacto, a 60 fps, ya reencuadrado (archivo intermedio casi sin pérdida)
        cut = WORK / f"_{i:02d}.mp4"
        ff("-ss", round(p["src"] - 0.25, 3), "-t", round(src_dur + 0.6, 3), "-i", SRC,
           "-vf", f"crop={w}:{h}:{x}:{y},scale=1080:1920:flags=lanczos", "-an",
           "-c:v", "libx264", "-preset", "fast", "-crf", "8", cut)
        chain = []
        if p["estab"]:
            trf = WORK / f"_{i:02d}.trf"
            ff("-i", cut, "-vf", f"vidstabdetect=shakiness=7:accuracy=15:result={trf}", "-f", "null", "-")
            chain.append(f"vidstabtransform=input={trf}:smoothing=14:zoom=4:optzoom=0:interpol=bicubic")
        chain += [f"trim=start=0.25:duration={src_dur:.4f}", "setpts=PTS-STARTPTS"]
        if v != 1.0:
            chain.append(f"setpts=PTS/{v}")          # 60 fps reales repartidos en el doble de tiempo
        chain += [f"fps={FPS}", GRADE[p["luz"]], GRAIN, "format=yuv420p"]
        ff("-i", cut, "-vf", ",".join(chain), "-frames:v", n, "-an",
           "-c:v", "libx264", "-preset", "medium", "-crf", "13", out)
        cut.unlink()
        stamp.write_text(json.dumps(meta))
    concat.append(f"file '{out}'")
    edl.append({"plano": p["id"], "nota": p["nota"], "origen_s": p["src"], "velocidad": v,
                "entra": round(fr[i] / FPS, 3), "sale": round(fr[i + 1] / FPS, 3)})
    print(f"plano {i:02d} {p['id']:9s} {fr[i]/FPS:6.2f}-{fr[i+1]/FPS:6.2f}", flush=True)
(WORK / "lista.txt").write_text("\n".join(concat) + "\n")
ff("-f", "concat", "-safe", "0", "-i", WORK / "lista.txt", "-c", "copy", WORK / "cuerpo.mp4")

# 3. Textos -------------------------------------------------------------------------------
if not (WORK / "fin.png").exists():
    js = WORK / "textos.js"
    js.write_text("""
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 14000 } });
 await p.goto('file://%s', { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
 for (const id of ['base','t1','t2','t3','t4','fin']) await p.locator('#'+id).screenshot({ path: '%s/' + id + '.png', omitBackground: true });
 await b.close(); })();""" % (HERE / "textos.html", WORK))
    subprocess.run(["node", str(js)], check=True)
E = {e["plano"]: e for e in edl}
TEXTOS = {
    "t1": (0.35, E["humo"]["sale"] - 0.18),
    "t2": (E["agitado"]["entra"] + 0.1, E["brazo"]["sale"] - 0.18),
    "t3": (E["naranja"]["entra"] + 0.15, E["naranja"]["sale"] - 0.15),
    "t4": (E["reaccion"]["entra"] + 0.15, E["nube"]["sale"] - 0.25),
}

# 4. Sonido: música + ambiente real de la barra + efectos sintetizados -----------------------
N = int(TOTAL * SR)
mus, _ = librosa.load(MUSIC, sr=SR, mono=False, offset=m_start, duration=TOTAL + 0.3)
mus = mus.T[:N]
if len(mus) < N:
    mus = np.vstack([mus, np.zeros((N - len(mus), 2))])
fade = np.ones(N); fo = int(1.2 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 1.3
mix = mus * fade[:, None] * 0.82

SRC_WAV = WORK / "original_audio.wav"
if not SRC_WAV.exists():
    ff("-i", SRC, "-vn", "-ac", "1", "-ar", SR, SRC_WAV)

def clip_audio(p, n_out):
    """Audio original del plano: a 1x se usa tal cual; en cámara lenta se omite (sonaría deformado)."""
    if p["vel"] != 1.0:
        return np.zeros(n_out)
    a, _ = librosa.load(SRC_WAV, sr=SR, mono=True, offset=p["src"], duration=n_out / SR + 0.05)
    a = a[:n_out]
    if len(a) < n_out:
        a = np.pad(a, (0, n_out - len(a)))
    from scipy.signal import butter, sosfilt   # solo el «brillo» del hielo y el metal, sin la canción del local
    a = sosfilt(butter(4, 2500, btype="high", fs=SR, output="sos"), a)
    r = int(0.03 * SR); a[:r] *= np.linspace(0, 1, r); a[-r:] *= np.linspace(1, 0, r)
    return a
amb = np.zeros(N)
for i, p in enumerate(planos):
    s0, s1 = int(fr[i] / FPS * SR), int(fr[i + 1] / FPS * SR)
    amb[s0:s1] += clip_audio(p, s1 - s0)
mix += (amb * 0.55)[:, None]

rng = np.random.default_rng(11)
def tt(d): return np.arange(int(d * SR)) / SR
def band(x, lo, hi):
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(4, [lo, hi], btype="band", fs=SR, output="sos"), x)
def place(sig, at, g, pan=0.0):
    i = int(at * SR); s = sig[: max(0, N - i)]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    mix[i:i + len(s), 0] += s * g * l; mix[i:i + len(s), 1] += s * g * r
# Silbido de humo en el gancho (el plano está en cámara lenta y sin audio propio)
x = tt(E["humo"]["sale"]); u = x / x[-1]
place(band(rng.standard_normal(len(x)), 2500, 9000) * (0.35 + 0.65 * np.sin(np.pi * u) ** 1.5), 0.0, 0.06)
# Riser de 1 compás antes del drop
d = 4 * BEAT; x = tt(d); u = x / d
place(band(rng.standard_normal(len(x)), 1200, 9000) * u ** 2.6 * np.minimum(1, (1 - u) * 40), E["rojo"]["entra"] - d, 0.16)
# Golpe grave en el drop
x = tt(1.6); f = 40 + 36 * np.exp(-x / 0.1)
place(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.45) * 0.9, E["rojo"]["entra"], 0.5)
# Aire en las cámaras lentas del show y del humo en la mesa
for k in ("chorro", "arriba", "nube"):
    d = 0.55; x = tt(d); u = x / d
    place(band(rng.standard_normal(len(x)), 500, 6000) * np.sin(np.pi * u) ** 2 * u, E[k]["entra"] - 0.42, 0.09, pan=0.3)
# Destello en la tarjeta final
x = tt(2.4); sh = np.zeros(len(x))
for fq in (2093, 2637, 3136, 3951, 5274):
    on = rng.uniform(0, 0.25); sh += np.sin(2 * np.pi * fq * x) * np.where(x > on, np.exp(-(x - on) / 1.1), 0)
place(sh / 5, BODY + 0.05, 0.07)
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
sf.write(WORK / "audio.wav", mix, SR)

# 5. Exportación ---------------------------------------------------------------------------------
def export(with_text, name):
    inputs = ["-i", WORK / "cuerpo.mp4", "-loop", "1", "-t", END, "-i", WORK / "fin.png", "-i", WORK / "audio.wav"]
    fc, last = "[0:v]null[v0]", "v0"
    if with_text:
        inputs += ["-loop", "1", "-t", BODY, "-i", WORK / "base.png"]
        fc += f";[3:v]format=rgba[bs];[{last}][bs]overlay[w0]"; last = "w0"
        for k, nm in enumerate(["t1", "t2", "t3", "t4"]):
            inputs += ["-loop", "1", "-t", BODY, "-i", WORK / f"{nm}.png"]
            a, z = TEXTOS[nm]
            fc += (f";[{4 + k}:v]format=rgba,fade=t=in:st={a}:d=0.28:alpha=1,fade=t=out:st={z - 0.22}:d=0.22:alpha=1[x{k}]"
                   f";[{last}][x{k}]overlay=enable='between(t,{a},{z})'[w{k + 1}]")
            last = f"w{k + 1}"
    fc += (f";[{last}]trim=duration={BODY},setpts=PTS-STARTPTS,setsar=1[body]"
           f";[1:v]fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.22,setsar=1[endv]"
           f";[body][endv]concat=n=2:v=1:a=0,format=yuv420p[v]"
           f";[2:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample={SR}[a]")
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", TOTAL, "-r", FPS,
       "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-maxrate", "12M", "-bufsize", "24M", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", WORK / name)

export(True, "exotico-experiencia.mp4")
export(False, "exotico-experiencia-sin-textos.mp4")
# Portada: fotograma de la risa a cámara + título de marca (portada.html)
ff("-ss", round(E["risa"]["entra"] + 0.75, 2), "-i", WORK / "exotico-experiencia-sin-textos.mp4",
   "-frames:v", "1", "-q:v", "1", WORK / "portada-fondo.jpg")
(WORK / "portada.js").write_text("""
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
 await p.goto('file://%s?bg=' + encodeURIComponent('file://%s'), { waitUntil: 'networkidle' });
 await p.evaluate(() => document.fonts.ready); await p.waitForFunction(() => document.getElementById('bg').complete);
 await p.screenshot({ path: '%s', type: 'jpeg', quality: 94 }); await b.close(); })();""" % (HERE / "portada.html", WORK / "portada-fondo.jpg", WORK / "portada.jpg"))
subprocess.run(["node", str(WORK / "portada.js")], check=True)
(HERE / "edl.json").write_text(json.dumps({
    "fps": FPS, "bpm": cfg["bpm"], "musica": MUSIC.name, "musica_desde_s": round(m_start, 3),
    "cuerpo_s": round(BODY, 3), "total_s": round(TOTAL, 3),
    "textos": {k: [round(a, 2), round(z, 2)] for k, (a, z) in TEXTOS.items()}, "planos": edl}, ensure_ascii=False, indent=2))
print("LISTO", round(TOTAL, 2), "s · música desde", round(m_start, 2), "s")
