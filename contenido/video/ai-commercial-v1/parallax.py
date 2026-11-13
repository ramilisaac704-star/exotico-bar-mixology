#!/usr/bin/env python3
"""Convierte cada imagen fija en un plano con movimiento de cámara 3D (paralaje por profundidad).

Uso: python parallax.py <carpeta_tomas> <carpeta_salida>
Ejecutar con el Python de ComfyUI (necesita torch, transformers y opencv).
La profundidad se estima con Depth Anything V2 Small (Apache-2.0), en CPU.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np, cv2, torch
from PIL import Image
from transformers import pipeline

HERE = Path(__file__).resolve().parent
SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((HERE / "montaje.json").read_text())
FPS = cfg["fps"]; BEAT = 60.0 / cfg["musica"]["bpm"]
W, H = 1080, 1920
SW, SH = 1296, 2268            # la imagen se amplía una sola vez; el paralaje muestrea de aquí

# zoom inicial/final, desplazamiento del plano cercano en px (x0,x1,y0,y1)
MOV = {
    "dron":      dict(z=(1.06, 1.20), sx=(0, 0),     sy=(-14, 14)),
    "avance":    dict(z=(1.05, 1.15), sx=(-5, 5),    sy=(-3, 3)),
    "retroceso": dict(z=(1.16, 1.06), sx=(5, -5),    sy=(3, -3)),
    "lateral_d": dict(z=(1.09, 1.11), sx=(-18, 18),  sy=(0, 0)),
    "lateral_i": dict(z=(1.11, 1.09), sx=(18, -18),  sy=(0, 0)),
    "orbita":    dict(z=(1.08, 1.12), sx=(-16, 16),  sy=(-5, 5)),
}

depth_pipe = pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf", device="cpu")

def pick(shot_id):
    sel = cfg.get("seleccion", {}).get(shot_id)
    if sel:
        return SRC / sel
    files = sorted(SRC.glob(f"{shot_id}_s*.png"))
    if not files:
        sys.exit(f"Falta la toma {shot_id}")
    return files[-1]

xs, ys = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
t = 0.0; frame = 0; edl = []
for esc in cfg["escenas"]:
    for shot_id, beats, mov, *extra in esc["planos"]:
        opt = extra[0] if extra else {}                 # {"cy": centro vertical 0-1, "z": [zoom inicial, final]}
        end = round((t + beats * BEAT) * FPS); n = end - frame
        path = pick(shot_id)
        out = OUT / f"{shot_id}.mp4"
        edl.append({"plano": shot_id, "imagen": path.name, "movimiento": mov,
                    "entra": round(frame / FPS, 3), "sale": round(end / FPS, 3), "escena": esc["nombre"]})
        t += beats * BEAT; frame = end
        stamp = OUT / f"{shot_id}.json"
        meta = {"imagen": path.name, "n": n, "mov": mov, "opt": opt}
        if out.exists() and stamp.exists() and json.loads(stamp.read_text()) == meta:
            continue
        img = Image.open(path).convert("RGB")
        d = np.array(depth_pipe(img)["depth"], dtype=np.float32)
        d = (d - d.min()) / (d.max() - d.min() + 1e-6)             # 1 = cerca
        src = cv2.resize(np.array(img)[:, :, ::-1], (SW, SH), interpolation=cv2.INTER_LANCZOS4)
        dep = cv2.GaussianBlur(cv2.resize(d, (SW, SH), interpolation=cv2.INTER_CUBIC), (0, 0), 9)
        focus = float(np.median(dep))
        m = dict(MOV[mov]); m["z"] = tuple(opt.get("z", m["z"])); cy = opt.get("cy", 0.5)
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "13",
                               "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
        k = SH / H                                                  # escala salida -> fuente
        for i in range(n):
            u = i / max(n - 1, 1)
            z = m["z"][0] + (m["z"][1] - m["z"][0]) * u
            sx = m["sx"][0] + (m["sx"][1] - m["sx"][0]) * u
            sy = m["sy"][0] + (m["sy"][1] - m["sy"][0]) * u
            bx = (xs - W / 2) / z * k + SW / 2
            by = (ys - H / 2) / z * k + SH * cy
            dd = cv2.remap(dep, bx, by, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT) - focus
            fr = cv2.remap(src, bx + sx * dd * 2.2, by + sy * dd * 2.2, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            ff.stdin.write(fr.tobytes())
        ff.stdin.close(); ff.wait()
        stamp.write_text(json.dumps(meta))
        print("plano", shot_id, n, "fotogramas", mov, flush=True)

(HERE / "edl.json").write_text(json.dumps({"fps": FPS, "cuerpo_s": round(frame / FPS, 3), "planos": edl}, ensure_ascii=False, indent=2))
print("cuerpo", round(frame / FPS, 2), "s")
