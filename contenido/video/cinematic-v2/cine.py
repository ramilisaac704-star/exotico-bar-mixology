#!/usr/bin/env python3
"""Motor de planos cinematográficos: reencuadre con movimiento de cámara subpíxel sobre el 4K,
rampas de velocidad y cámara lenta con fotogramas reales de 60 fps más interpolación RIFE.

Uso:
  python cine.py planos.json <original.mp4> <carpeta_trabajo>            # renderiza los planos
  python cine.py planos.json <original.mp4> <carpeta_trabajo> --preview  # solo encuadres inicial/final
Ejecutar con el Python de ComfyUI (torch + opencv).
"""
import json, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2

CFG, SRC, WORK = Path(sys.argv[1]), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
PREVIEW = "--preview" in sys.argv
cfg = json.loads(CFG.read_text())
FPS, W, H = cfg["fps"], cfg["ancho"], cfg["alto"]
BEAT = 60.0 / cfg["bpm"]
SW, SH, SFPS = 2160, 3840, 60.0
RATIO = W / H
WORK.mkdir(parents=True, exist_ok=True)


def ff(*args, **kw):
    return subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True, **kw)


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def speed_at(curve, u):
    for (u0, s0), (u1, s1) in zip(curve, curve[1:]):
        if u <= u1:
            return s0 if u1 == u0 else s0 + (s1 - s0) * (u - u0) / (u1 - u0)
    return curve[-1][1]


def cam_at(p, u):
    (cx0, cy0, h0), (cx1, cy1, h1) = p["cam"]
    e = smooth(u)
    h = h0 + (h1 - h0) * e
    w = h * RATIO
    cx = min(max(cx0 + (cx1 - cx0) * e, w / 2), SW - w / 2)
    cy = min(max(cy0 + (cy1 - cy0) * e, h / 2), SH - h / 2)
    return cx, cy, w, h


def region_for(p):
    xs, ys, xe, ye = [], [], [], []
    for u in np.linspace(0, 1, 25):
        cx, cy, w, h = cam_at(p, u)
        xs.append(cx - w / 2); ys.append(cy - h / 2); xe.append(cx + w / 2); ye.append(cy + h / 2)
    m = 24
    x0, y0 = int(max(0, min(xs) - m)), int(max(0, min(ys) - m))
    x1, y1 = int(min(SW, max(xe) + m)), int(min(SH, max(ye) + m))
    x0 -= x0 % 2; y0 -= y0 % 2; x1 += x1 % 2; y1 += y1 % 2
    return x0, y0, min(x1, SW) - x0, min(y1, SH) - y0


def frame_plan(p, n):
    """Para cada fotograma de salida: tiempo de origen y velocidad."""
    times, speeds, s = [], [], p["src"]
    for k in range(n):
        v = speed_at(p["vel"], k / max(n - 1, 1))
        times.append(s); speeds.append(v)
        s += v / FPS
    return times, speeds


def warp(src, X, Y, cx, cy, w, h):
    sc = h / H
    img = src
    if sc > 1.25:                                   # prefiltro suave al reducir
        img = cv2.GaussianBlur(src, (0, 0), 0.33 * sc)
    M = np.array([[w / W, 0, cx - w / 2 - X], [0, h / H, cy - h / 2 - Y]], dtype=np.float64)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)


def stabilized_source(p, X, Y, RW, RH, start, dur):
    """Para tomas en mano: recorta la región, estabiliza (vid.stab) y devuelve el archivo intermedio."""
    out = WORK / f"_estab_{p['id']}.mp4"
    meta = WORK / f"_estab_{p['id']}.json"
    sig = {"X": X, "Y": Y, "RW": RW, "RH": RH, "start": start, "dur": dur}
    if out.exists() and meta.exists() and json.loads(meta.read_text()) == sig:
        return out
    trf = WORK / f"_estab_{p['id']}.trf"
    ff("-ss", start, "-t", dur, "-i", SRC, "-vf", f"crop={RW}:{RH}:{X}:{Y},vidstabdetect=shakiness=8:accuracy=15:result={trf}", "-f", "null", "-")
    ff("-ss", start, "-t", dur, "-i", SRC, "-vf",
       f"crop={RW}:{RH}:{X}:{Y},vidstabtransform=input={trf}:smoothing=24:zoom=4:optzoom=0:interpol=bicubic:crop=keep,fps={SFPS}",
       "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "6", "-pix_fmt", "yuv420p", out)
    meta.write_text(json.dumps(sig))
    return out


class Stream:
    """Lee fotogramas secuenciales (60 fps) de una región del origen y sirve pares por índice."""
    def __init__(self, path, start, dur, X, Y, RW, RH, pre_cropped=False):
        vf = f"fps={SFPS}" if pre_cropped else f"crop={RW}:{RH}:{X}:{Y},fps={SFPS}"
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.4f}", "-t", f"{dur:.4f}", "-i", str(path),
               "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.RW, self.RH = RW, RH
        self.buf, self.next_idx = {}, 0

    def _read(self):
        raw = self.proc.stdout.read(self.RW * self.RH * 3)
        if len(raw) < self.RW * self.RH * 3:
            return None
        return np.frombuffer(raw, np.uint8).reshape(self.RH, self.RW, 3)

    def get(self, idx):
        while self.next_idx <= idx:
            f = self._read()
            if f is None:
                break
            self.buf[self.next_idx] = f; self.next_idx += 1
        for k in [k for k in self.buf if k < idx - 1]:
            del self.buf[k]
        if idx in self.buf:
            return self.buf[idx]
        return self.buf[max(self.buf)]            # fin del archivo: repite el último

    def close(self):
        self.proc.stdout.close(); self.proc.wait()


rife = None
def interp(f0, f1, t):
    global rife
    if rife is None:
        sys.path.insert(0, str(CFG.resolve().parent))
        from rife_cpu import Rife
        rife = Rife()
    return rife.between(f0, f1, t)


# ---------------------------------------------------------------------------------------
planos = cfg["planos"]
cuts = np.cumsum([0] + [p["pulsos"] for p in planos]) * BEAT
fr = np.round(cuts * FPS).astype(int)
edl, previews = [], []
t_all = time.time()
for i, p in enumerate(planos):
    n = int(fr[i + 1] - fr[i])
    times, speeds = frame_plan(p, n)
    X, Y, RW, RH = region_for(p)
    start = p["src"] - 1 / SFPS
    dur = (times[-1] - p["src"]) + 4 / SFPS
    edl.append({"plano": p["id"], "nota": p["nota"], "origen": [round(p["src"], 3), round(times[-1], 3)],
                "entra": round(fr[i] / FPS, 3), "sale": round(fr[i + 1] / FPS, 3), "fotogramas": n,
                "velocidad": [round(min(speeds), 2), round(max(speeds), 2)], "region": [X, Y, RW, RH]})
    if PREVIEW:
        for u, s in ((0.0, times[0]), (1.0, times[-1])):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s:.4f}", "-i", str(SRC), "-frames:v", "1",
                                  "-vf", f"crop={RW}:{RH}:{X}:{Y}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                                 check=True, capture_output=True).stdout
            img = np.frombuffer(raw, np.uint8).reshape(RH, RW, 3)
            out = warp(img, X, Y, *cam_at(p, u))
            out = cv2.resize(out, (216, 344))
            cv2.putText(out, f"{p['id']} {s:.2f}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
            previews.append(out)
        continue

    out = WORK / f"{i:02d}_{p['id']}.mp4"
    stamp = WORK / f"{i:02d}_{p['id']}.json"
    sig = {k: p[k] for k in ("src", "pulsos", "vel", "cam", "estab")} | {"n": n}
    if out.exists() and stamp.exists() and json.loads(stamp.read_text()) == sig:
        print(f"plano {i:02d} {p['id']:9s} ya renderizado", flush=True); continue
    t0 = time.time()
    if p["estab"]:
        path = stabilized_source(p, X, Y, RW, RH, start, dur)
        stream = Stream(path, 0.0, dur, X, Y, RW, RH, pre_cropped=True)
    else:
        stream = Stream(SRC, start, dur, X, Y, RW, RH)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "11",
                            "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    n_rife = 0
    for k in range(n):
        j = (times[k] - start) * SFPS
        j0 = int(np.floor(j)); frac = j - j0
        cam = cam_at(p, k / max(n - 1, 1))
        if speeds[k] >= 0.9 or frac < 0.1 or frac > 0.9:
            frame = warp(stream.get(j0 if frac < 0.5 else j0 + 1), X, Y, *cam)
        else:
            f0 = warp(stream.get(j0), X, Y, *cam)
            f1 = warp(stream.get(j0 + 1), X, Y, *cam)
            frame = interp(f0, f1, frac); n_rife += 1
        enc.stdin.write(frame.tobytes())
    enc.stdin.close(); enc.wait(); stream.close()
    stamp.write_text(json.dumps(sig))
    print(f"plano {i:02d} {p['id']:9s} {n:4d} fot. | RIFE {n_rife:3d} | origen {p['src']:.2f}-{times[-1]:.2f} s | {time.time()-t0:5.0f} s", flush=True)

if PREVIEW:
    rows = [np.hstack(previews[k:k + 8]) for k in range(0, len(previews), 8)]
    rows = [np.hstack([r, np.zeros((344, 216 * 8 - r.shape[1], 3), np.uint8)]) if r.shape[1] < 216 * 8 else r for r in rows]
    cv2.imwrite(str(WORK / "preview.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    for e in edl:
        print(f"{e['plano']:9s} {e['entra']:6.2f}-{e['sale']:6.2f}  origen {e['origen'][0]:.2f}-{e['origen'][1]:.2f}  vel {e['velocidad']}  región {e['region']}")
    print("preview:", WORK / "preview.jpg")
else:
    (CFG.parent / "edl.json").write_text(json.dumps({"fps": FPS, "bpm": cfg["bpm"], "beat": BEAT, "ancho": W, "alto": H,
        "cuerpo_s": round(fr[-1] / FPS, 3), "fin_s": round(round(cfg["fin_pulsos"] * BEAT * FPS) / FPS, 3),
        "planos": edl}, ensure_ascii=False, indent=2))
    print("LISTO cuerpo", round(fr[-1] / FPS, 2), "s en", round(time.time() - t_all), "s")
