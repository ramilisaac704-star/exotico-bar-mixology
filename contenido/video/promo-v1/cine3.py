#!/usr/bin/env python3
"""Motor de planos para varias fuentes (4K y 720p, frecuencias distintas).

Cada plano: reencuadre con movimiento de cámara subpíxel, curva de velocidad
(cámara lenta con fotogramas reales + RIFE), estabilización opcional y
prefiltro opcional (ruido, exposición) aplicado antes de ampliar.

Uso:
  python cine3.py planos.json <carpeta_fuentes> <carpeta_trabajo> [--preview]
Ejecutar con el Python de ComfyUI (torch + opencv).
"""
import json, subprocess, sys, time
from pathlib import Path
import numpy as np, cv2

CFG, SRCDIR, WORK = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
PREVIEW = "--preview" in sys.argv
cfg = json.loads(CFG.read_text())
FPS, W, H = cfg["fps"], cfg["ancho"], cfg["alto"]
BEAT = 60.0 / cfg["bpm"]
RATIO = W / H
WORK.mkdir(parents=True, exist_ok=True)


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,avg_frame_rate:stream_side_data=rotation", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    w, h = s["width"], s["height"]
    rot = 0
    for sd in s.get("side_data_list", []):
        rot = int(sd.get("rotation", 0))
    if abs(rot) == 90:
        w, h = h, w
    n, d = s["avg_frame_rate"].split("/")
    return w, h, float(n) / float(d)


SOURCES = {}
for key, name in cfg["fuentes"].items():
    p = SRCDIR / name
    SOURCES[key] = {"path": p, **dict(zip(("w", "h", "fps"), probe(p)))}


def ease(u, kind):
    u = min(1.0, max(0.0, u))
    if kind == "golpe":                    # arranque rápido y asentamiento (punch)
        return 1 - (1 - u) ** 4
    return u * u * (3 - 2 * u)


def speed_at(curve, u):
    for (u0, s0), (u1, s1) in zip(curve, curve[1:]):
        if u <= u1:
            return s0 if u1 == u0 else s0 + (s1 - s0) * (u - u0) / (u1 - u0)
    return curve[-1][1]


def cam_at(p, u, SW, SH):
    (cx0, cy0, h0), (cx1, cy1, h1) = p["cam"]
    e = ease(u, p.get("curva", "suave"))
    h = min(h0 + (h1 - h0) * e, SH, SW / RATIO)
    w = h * RATIO
    cx = min(max(cx0 + (cx1 - cx0) * e, w / 2), SW - w / 2)
    cy = min(max(cy0 + (cy1 - cy0) * e, h / 2), SH - h / 2)
    return cx, cy, w, h


def region_for(p, SW, SH):
    xs, ys, xe, ye = [], [], [], []
    for u in np.linspace(0, 1, 25):
        cx, cy, w, h = cam_at(p, u, SW, SH)
        xs.append(cx - w / 2); ys.append(cy - h / 2); xe.append(cx + w / 2); ye.append(cy + h / 2)
    m = 16
    x0, y0 = int(max(0, min(xs) - m)), int(max(0, min(ys) - m))
    x1, y1 = int(min(SW, max(xe) + m)), int(min(SH, max(ye) + m))
    x0 -= x0 % 2; y0 -= y0 % 2
    w_, h_ = x1 - x0, y1 - y0
    w_ -= w_ % 2; h_ -= h_ % 2
    return x0, y0, w_, h_


def frame_plan(p, n):
    times, speeds, s = [], [], p["src"]
    for k in range(n):
        v = speed_at(p["vel"], k / max(n - 1, 1))
        times.append(s); speeds.append(v)
        s += v / FPS
    return times, speeds


def warp(src, X, Y, cx, cy, w, h):
    sc = h / H
    img = cv2.GaussianBlur(src, (0, 0), 0.33 * sc) if sc > 1.25 else src
    M = np.array([[w / W, 0, cx - w / 2 - X], [0, h / H, cy - h / 2 - Y]], dtype=np.float64)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)


def prepared_source(p, src, X, Y, RW, RH, start, dur):
    """Recorte de la región a la frecuencia nativa, con prefiltro y estabilización si se piden."""
    pre = p.get("pre", "")
    if not p.get("estab") and not pre:
        return None
    out = WORK / f"_prep_{p['id']}.mp4"
    meta = WORK / f"_prep_{p['id']}.json"
    sig = {"X": X, "Y": Y, "RW": RW, "RH": RH, "start": round(start, 4), "dur": round(dur, 4),
           "pre": pre, "estab": p.get("estab", False), "file": str(src["path"])}
    if out.exists() and meta.exists() and json.loads(meta.read_text()) == sig:
        return out
    base = f"crop={RW}:{RH}:{X}:{Y}" + (f",{pre}" if pre else "")
    chain = base
    if p.get("estab"):
        trf = WORK / f"_prep_{p['id']}.trf"
        ff("-ss", start, "-t", dur, "-i", src["path"], "-vf", f"{base},vidstabdetect=shakiness=8:accuracy=15:result={trf}", "-f", "null", "-")
        chain = f"{base},vidstabtransform=input={trf}:smoothing=20:zoom=3:optzoom=0:interpol=bicubic:crop=keep"
    ff("-ss", start, "-t", dur, "-i", src["path"], "-vf", f"{chain},fps={src['fps']:.4f}",
       "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "6", "-pix_fmt", "yuv420p", out)
    meta.write_text(json.dumps(sig))
    return out


class Stream:
    def __init__(self, path, start, dur, X, Y, RW, RH, fps, pre_cropped=False):
        vf = f"fps={fps:.4f}" if pre_cropped else f"crop={RW}:{RH}:{X}:{Y},fps={fps:.4f}"
        cmd = ["ffmpeg", "-v", "error", "-ss", f"{start:.4f}", "-t", f"{dur:.4f}", "-i", str(path),
               "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 8)
        self.RW, self.RH, self.buf, self.next_idx = RW, RH, {}, 0

    def get(self, idx):
        while self.next_idx <= idx:
            raw = self.proc.stdout.read(self.RW * self.RH * 3)
            if len(raw) < self.RW * self.RH * 3:
                break
            self.buf[self.next_idx] = np.frombuffer(raw, np.uint8).reshape(self.RH, self.RW, 3); self.next_idx += 1
        for k in [k for k in self.buf if k < idx - 1]:
            del self.buf[k]
        return self.buf[idx] if idx in self.buf else self.buf[max(self.buf)]

    def close(self):
        self.proc.stdout.close(); self.proc.wait()


rife = None
def interp(f0, f1, t):
    global rife
    if rife is None:
        sys.path.insert(0, str(CFG.parent))
        from rife_cpu import Rife
        rife = Rife()
    return rife.between(f0, f1, t)


planos = cfg["planos"]
cuts = np.cumsum([0] + [p["pulsos"] for p in planos]) * BEAT
fr = np.round(cuts * FPS).astype(int)
edl, previews, t_all = [], [], time.time()
for i, p in enumerate(planos):
    src = SOURCES[p["fuente"]]
    SW, SH, SFPS = src["w"], src["h"], src["fps"]
    n = int(fr[i + 1] - fr[i])
    times, speeds = frame_plan(p, n)
    X, Y, RW, RH = region_for(p, SW, SH)
    start = max(0.0, p["src"] - 1 / SFPS)
    dur = (times[-1] - p["src"]) + 4 / SFPS
    edl.append({"plano": p["id"], "fuente": p["fuente"], "nota": p["nota"],
                "origen": [round(p["src"], 3), round(times[-1], 3)], "entra": round(fr[i] / FPS, 3),
                "sale": round(fr[i + 1] / FPS, 3), "velocidad": [round(min(speeds), 2), round(max(speeds), 2)]})
    if PREVIEW:
        for u, s in ((0.0, times[0]), (1.0, times[-1])):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s:.4f}", "-i", str(src["path"]), "-frames:v", "1",
                                  "-vf", f"crop={RW}:{RH}:{X}:{Y}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                                 check=True, capture_output=True).stdout
            img = np.frombuffer(raw, np.uint8).reshape(RH, RW, 3)
            out = cv2.resize(warp(img, X, Y, *cam_at(p, u, SW, SH)), (180, 320))
            cv2.putText(out, f"{p['id']} {s:.2f}", (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
            previews.append(out)
        continue
    out = WORK / f"{i:02d}_{p['id']}.mp4"
    stamp = WORK / f"{i:02d}_{p['id']}.json"
    sig = {k: p.get(k) for k in ("fuente", "src", "pulsos", "vel", "cam", "curva", "estab", "pre")} | {"n": n}
    if out.exists() and stamp.exists() and json.loads(stamp.read_text()) == sig:
        print(f"plano {i:02d} {p['id']:12s} ya renderizado", flush=True); continue
    t0 = time.time()
    prep = prepared_source(p, src, X, Y, RW, RH, start, dur)
    stream = Stream(prep, 0.0, dur, X, Y, RW, RH, SFPS, True) if prep else Stream(src["path"], start, dur, X, Y, RW, RH, SFPS)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "11",
                            "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    n_rife = 0
    for k in range(n):
        j = (times[k] - start) * SFPS
        j0 = int(np.floor(j)); frac = j - j0
        cam = cam_at(p, k / max(n - 1, 1), SW, SH)
        if speeds[k] >= 0.9 or frac < 0.1 or frac > 0.9:
            frame = warp(stream.get(j0 if frac < 0.5 else j0 + 1), X, Y, *cam)
        else:
            frame = interp(warp(stream.get(j0), X, Y, *cam), warp(stream.get(j0 + 1), X, Y, *cam), frac); n_rife += 1
        enc.stdin.write(frame.tobytes())
    enc.stdin.close(); enc.wait(); stream.close()
    stamp.write_text(json.dumps(sig))
    print(f"plano {i:02d} {p['id']:12s} {n:4d} fot. | RIFE {n_rife:3d} | {p['fuente']} {p['src']:.2f}-{times[-1]:.2f} s | {time.time()-t0:4.0f} s", flush=True)

if PREVIEW:
    cols = 10
    rows = [np.hstack(previews[k:k + cols]) for k in range(0, len(previews), cols)]
    rows = [np.hstack([r, np.zeros((320, 180 * cols - r.shape[1], 3), np.uint8)]) if r.shape[1] < 180 * cols else r for r in rows]
    cv2.imwrite(str(WORK / "preview.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])
    for e in edl:
        print(f"{e['plano']:12s} {e['entra']:6.2f}-{e['sale']:6.2f}  {e['fuente']} {e['origen'][0]:.2f}-{e['origen'][1]:.2f}  vel {e['velocidad']}")
else:
    (CFG.parent / "edl.json").write_text(json.dumps({"fps": FPS, "bpm": cfg["bpm"], "beat": BEAT, "ancho": W, "alto": H,
        "cuerpo_s": round(fr[-1] / FPS, 3), "fin_s": round(round(cfg["fin_pulsos"] * BEAT * FPS) / FPS, 3),
        "planos": edl}, ensure_ascii=False, indent=2))
    print("LISTO cuerpo", round(fr[-1] / FPS, 2), "s en", round(time.time() - t_all), "s")
