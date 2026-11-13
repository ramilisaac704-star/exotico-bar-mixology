#!/usr/bin/env python3
"""Proyecto editable del reel cinematográfico de EXÓTICO (v1).

Uso:  python3 build.py <carpeta_con_v1_v2_v3.mp4> <musica.mp3> <carpeta_trabajo>

Toda la edición está en la lista PLANOS: cambia tiempos, encuadres o el orden
y vuelve a ejecutar. Requiere ffmpeg y Node con Playwright (para los textos).
"""
import subprocess, sys, os, json
from pathlib import Path

SRC, MUSIC, WORK = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
HERE = Path(__file__).resolve().parent
WORK.mkdir(parents=True, exist_ok=True)
FPS = 30
BEAT = 60 / 136.0          # la pista va a 136 pulsos por minuto
MUSIC_OFFSET = 2.95        # la entrada fuerte de la música cae al final de la intro

# Encuadres sacados del original 4K (2160x3840). Ninguno amplía por encima de la resolución nativa.
def med(x=302, y=600): return f"crop=1296:2304:{x}:{y}"       # plano medio
WIDE = "crop=1890:3360:0:240"                                  # plano general: playa, barra y cielo
HANDS = "crop=1080:1920:650:1090"                              # detalle de manos y barra
DRINK = "crop=1080:1920:540:1400"                              # detalle del cóctel terminado

GRADE = ("curves=m='0/0 0.18/0.30 0.5/0.63 1/1',eq=contrast=1.06:saturation=1.15,"
         "colorbalance=rs=0.06:bs=-0.07:rm=0.03:bm=-0.03:rh=0.02:bh=-0.05,"
         "unsharp=3:3:0.35,vignette=PI/5.5")

# (archivo, inicio en el original, pulsos de duración, encuadre, velocidad, nota)
PLANOS = [
    ("v3", 4.30, 5.2, med(),        1.0, "GANCHO: lanzamiento de la coctelera al aire"),
    ("v3", 44.0, 4.0, WIDE,         1.0, "General: brazo extendido, playa y barra"),
    ("v1", 8.00, 4.0, med(),        1.0, "Revisa la coctelera"),
    ("v1", 13.2, 4.0, HANDS,        1.0, "Detalle: manos y vertido"),
    ("v2", 8.00, 4.0, med(180),     1.0, "Vertido en chorro desde la botella"),
    ("v2", 17.8, 4.0, med(180),     1.0, "Botella verde en la mano"),
    ("v1", 40.5, 4.0, HANDS,        1.0, "Detalle: manos trabajando"),
    ("v2", 54.0, 2.0, med(150),     1.0, "IMPACTO: coctelera sobre la cabeza"),
    ("v3", 13.0, 2.0, med(),        1.0, "Giro de coctelera"),
    ("v2", 48.6, 2.0, med(150),     1.0, "Agitado enérgico"),
    ("v3", 31.6, 2.0, med(),        1.0, "Coctelera en primer término"),
    ("v2", 56.4, 2.0, med(150),     1.0, "Coctelera en alto"),
    ("v3", 5.00, 2.0, WIDE,         1.0, "General del lanzamiento"),
    ("v2", 0.40, 2.0, med(180),     1.0, "Botella sobre el antebrazo"),
    ("v3", 14.0, 2.0, med(),        1.0, "Coctelera en movimiento"),
    ("v1", 20.0, 4.0, med(),        0.5, "CÁMARA LENTA: vertido desde lo alto"),
    ("v3", 55.6, 4.0, med(),        0.5, "CÁMARA LENTA: vertido naranja"),
    ("v3", 62.0, 6.0, DRINK,        1.0, "CIERRE: cóctel terminado"),
    ("v2", 77.5, 6.0, WIDE,         1.0, "General: mirando el atardecer"),
]
END_CARD = 3.0

def run(cmd):
    subprocess.run(cmd, check=True)

def ff(*args):
    run(["ffmpeg", "-v", "error", "-y", *map(str, args)])

# 1. Textos (PNG transparentes) ------------------------------------------------
if not (WORK / "fin.png").exists():
    js = WORK / "textos.js"
    js.write_text("""
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 10000 } });
 await p.goto('file://%s', { waitUntil: 'networkidle' }); await p.evaluate(() => document.fonts.ready);
 for (const id of ['base','t1','t2','t3','fin']) await p.locator('#'+id).screenshot({ path: '%s/' + id + '.png', omitBackground: true });
 await b.close(); })();""" % (HERE / "textos.html", WORK))
    run(["node", str(js)])

# 2. Planos --------------------------------------------------------------------
times, t, frame = [], 0.0, 0
concat = []
for i, (src, start, beats, crop, speed, note) in enumerate(PLANOS):
    end_frame = round((t + beats * BEAT) * FPS)
    n = end_frame - frame
    out = WORK / f"plano{i:02d}.mp4"
    dur_out = n / FPS
    if out.exists():
        pass  # ya renderizado: borra el archivo para rehacer este plano
    elif speed == 1.0:
        vf = f"{crop},scale=1080:1920:flags=lanczos,{GRADE},fps={FPS},format=yuv420p"
        ff("-ss", start, "-t", dur_out + 0.2, "-i", SRC / f"{src}.mp4",
           "-vf", vf, "-af", "aresample=44100,volume=1", "-ac", "2", "-frames:v", n,
           "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-c:a", "aac", "-b:a", "160k", "-shortest", out)
    else:  # cámara lenta con interpolación de movimiento; sin audio original
        vf = (f"{crop},scale=1080:1920:flags=lanczos,setpts=PTS/{speed},"
              f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,{GRADE},format=yuv420p")
        ff("-ss", start, "-t", dur_out * speed + 0.2, "-i", SRC / f"{src}.mp4",
           "-f", "lavfi", "-t", dur_out, "-i", "anullsrc=r=44100:cl=stereo",
           "-vf", vf, "-frames:v", n, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-c:a", "aac", "-b:a", "160k", out)
    times.append({"plano": i, "origen": src, "inicio_original": start, "entra": round(frame / FPS, 3),
                  "sale": round(end_frame / FPS, 3), "velocidad": speed, "nota": note})
    concat.append(f"file '{out}'")
    t += beats * BEAT
    frame = end_frame
    print(f"plano {i:02d} listo: {note}", flush=True)

body = frame / FPS
(WORK / "lista.txt").write_text("\n".join(concat) + "\n")
ff("-f", "concat", "-safe", "0", "-i", WORK / "lista.txt", "-c", "copy", WORK / "cuerpo.mp4")
(HERE / "edl.json").write_text(json.dumps({"fps": FPS, "bpm": 136, "musica_desde": MUSIC_OFFSET,
                                           "duracion_total": round(body + END_CARD, 2), "planos": times},
                                          ensure_ascii=False, indent=2))

total = body + END_CARD
t3_in = times[-1]["entra"]
audio = (f"[0:a]volume=0.3[amb];[amus]atrim=start={MUSIC_OFFSET}:duration={total},asetpts=PTS-STARTPTS,"
         f"afade=t=in:st=0:d=0.4,afade=t=out:st={total-1.6}:d=1.6,volume=0.5[mus];"
         f"[amb]apad=whole_dur={total}[ambp];[ambp][mus]amix=inputs=2:normalize=0:duration=longest,"
         f"alimiter=limit=0.95,atrim=duration={total}[a]")

def export(with_text, out):
    inputs = ["-i", WORK / "cuerpo.mp4", "-i", MUSIC]
    names = ["base", "t1", "t2", "t3", "fin"] if with_text else ["fin"]
    for nme in names:
        inputs += ["-loop", "1", "-t", total, "-i", WORK / f"{nme}.png"]
    fc = audio.replace("[amus]", "[1:a]")
    if with_text:
        fc += (f";[3:v]format=rgba,fade=t=in:st=0.15:d=0.3:alpha=1,fade=t=out:st=1.95:d=0.3:alpha=1[t1]"
               f";[4:v]format=rgba,fade=t=in:st=2.35:d=0.3:alpha=1,fade=t=out:st=3.7:d=0.3:alpha=1[t2]"
               f";[5:v]format=rgba,fade=t=in:st={t3_in+0.15}:d=0.35:alpha=1[t3]"
               f";[0:v][2:v]overlay[v0];[v0][t1]overlay=enable='between(t,0.15,2.27)'[v1]"
               f";[v1][t2]overlay=enable='between(t,2.35,4.02)'[v2]"
               f";[v2][t3]overlay=enable='gte(t,{t3_in+0.15})'[v3]"
               f";[v3]trim=duration={body},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.2,fade=t=out:st={body-0.3}:d=0.3,setsar=1[bodyv]"
               f";[6:v]fps={FPS},format=yuv420p,trim=duration={END_CARD},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.35,setsar=1[endv]"
               f";[bodyv][endv]concat=n=2:v=1:a=0,format=yuv420p[v]")
    else:
        fc += (f";[0:v]fade=t=in:st=0:d=0.2,fade=t=out:st={body-0.3}:d=0.3,setsar=1[bodyv]"
               f";[2:v]fps={FPS},format=yuv420p,trim=duration={END_CARD},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.35,setsar=1[endv]"
               f";[bodyv][endv]concat=n=2:v=1:a=0,format=yuv420p[v]")
    ff(*inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", total,
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-maxrate", "12M", "-bufsize", "24M",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)

export(True, WORK / "exotico-cinematic-v1.mp4")
export(False, WORK / "exotico-cinematic-v1-sin-textos.mp4")
print("LISTO", round(total, 2), "s")
