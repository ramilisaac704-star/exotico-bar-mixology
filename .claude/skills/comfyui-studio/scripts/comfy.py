#!/usr/bin/env python3
"""Cliente mínimo de ComfyUI para el estudio creativo de EXÓTICO.

Solo usa la biblioteca estándar y solo habla con el servidor local
(127.0.0.1). No llama a ningún servicio externo ni de pago.

Ejemplos:
  comfy.py start
  comfy.py txt2img --prompt "..." --out salida/
  comfy.py img2img --image foto.jpg --prompt "..." --denoise 0.45 --out salida/
  comfy.py run flujo.json --set 6.inputs.text="..." --out salida/
  comfy.py stop
"""
import argparse
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

COMFY_DIR = Path(os.environ.get("COMFY_DIR", Path.home() / "ComfyUI"))
HOST = "127.0.0.1"
PORT = int(os.environ.get("COMFY_PORT", "8188"))
BASE = f"http://{HOST}:{PORT}"
PID_FILE = COMFY_DIR / ".exotico-server.pid"
LOG_FILE = COMFY_DIR / ".exotico-server.log"
WORKFLOWS = Path(__file__).resolve().parent.parent / "workflows"

# El servidor es local: nunca debe pasar por un proxy.
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api(path, payload=None, timeout=30):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with _opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read() or b"{}")


def is_up():
    try:
        api("/system_stats", timeout=3)
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def tier():
    f = COMFY_DIR / ".exotico-tier"
    return f.read_text().strip() if f.exists() else "cpu"


def cmd_start(_args):
    if is_up():
        print(json.dumps({"status": "ya estaba en marcha", "url": BASE}))
        return
    python = COMFY_DIR / ".venv" / "bin" / "python"
    if not python.exists():
        sys.exit("ComfyUI no está instalado. Ejecuta scripts/install.sh primero.")
    cmd = [str(python), "main.py", "--listen", HOST, "--port", str(PORT)]
    if tier() == "cpu":
        cmd.append("--cpu")
    with open(LOG_FILE, "ab") as log:
        proc = subprocess.Popen(cmd, cwd=COMFY_DIR, stdout=log, stderr=log, start_new_session=True)
    PID_FILE.write_text(str(proc.pid))
    for _ in range(180):
        if is_up():
            print(json.dumps({"status": "en marcha", "url": BASE, "pid": proc.pid, "nivel": tier()}))
            return
        if proc.poll() is not None:
            sys.exit(f"ComfyUI se cerró al arrancar. Revisa {LOG_FILE}")
        time.sleep(1)
    sys.exit(f"ComfyUI no respondió a tiempo. Revisa {LOG_FILE}")


def cmd_stop(_args):
    if PID_FILE.exists():
        try:
            os.killpg(int(PID_FILE.read_text()), signal.SIGTERM)
        except (ProcessLookupError, ValueError):
            pass
        PID_FILE.unlink(missing_ok=True)
    print(json.dumps({"status": "detenido"}))


def cmd_status(_args):
    if not is_up():
        print(json.dumps({"status": "apagado", "nivel": tier()}))
        return
    stats = api("/system_stats")
    models = api("/object_info/CheckpointLoaderSimple")["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
    print(json.dumps({
        "status": "en marcha",
        "nivel": tier(),
        "dispositivos": [d.get("name") for d in stats.get("devices", [])],
        "checkpoints": models,
    }, ensure_ascii=False))


def set_path(workflow, dotted, value):
    """Asigna workflow['6']['inputs']['text'] a partir de '6.inputs.text'."""
    keys = dotted.split(".")
    node = workflow
    for key in keys[:-1]:
        node = node[key]
    old = node.get(keys[-1])
    if isinstance(old, bool):
        value = value.lower() in ("1", "true", "si", "sí")
    elif isinstance(old, int):
        value = int(value)
    elif isinstance(old, float):
        value = float(value)
    node[keys[-1]] = value


def stage_image(path):
    """Copia una imagen a la carpeta input de ComfyUI y devuelve su nombre."""
    src = Path(path).resolve()
    if not src.is_file():
        sys.exit(f"No existe la imagen: {src}")
    name = f"exotico_{int(time.time())}_{src.name}"
    shutil.copy2(src, COMFY_DIR / "input" / name)
    return name


def submit_and_wait(workflow, out_dir, timeout):
    if not is_up():
        sys.exit("ComfyUI no está en marcha. Ejecuta: comfy.py start")
    try:
        prompt_id = api("/prompt", {"prompt": workflow})["prompt_id"]
    except urllib.error.HTTPError as err:
        sys.exit("ComfyUI rechazó el flujo: " + err.read().decode(errors="replace")[:2000])
    started = time.time()
    while time.time() - started < timeout:
        history = api(f"/history/{prompt_id}")
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("status_str") == "error":
                sys.exit("Error durante la generación: " + json.dumps(status.get("messages", []))[:2000])
            return save_outputs(entry, out_dir, time.time() - started)
        time.sleep(2)
    sys.exit(f"Tiempo agotado tras {timeout} s (el trabajo sigue en la cola de ComfyUI).")


def save_outputs(entry, out_dir, seconds):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for node_output in entry.get("outputs", {}).values():
        for kind in ("images", "gifs", "videos"):
            for item in node_output.get(kind, []):
                query = urllib.parse.urlencode({
                    "filename": item["filename"],
                    "subfolder": item.get("subfolder", ""),
                    "type": item.get("type", "output"),
                })
                target = out_dir / item["filename"]
                with _opener.open(f"{BASE}/view?{query}", timeout=120) as resp, open(target, "wb") as fh:
                    shutil.copyfileobj(resp, fh)
                saved.append(str(target))
    print(json.dumps({"archivos": saved, "segundos": round(seconds, 1)}, ensure_ascii=False))
    return saved


def load_workflow(name_or_path):
    path = Path(name_or_path)
    if not path.is_file():
        path = WORKFLOWS / name_or_path
    return json.loads(path.read_text())


def common_fill(workflow, args):
    workflow["6"]["inputs"]["text"] = args.prompt
    workflow["7"]["inputs"]["text"] = args.negative
    sampler = workflow["3"]["inputs"]
    sampler["seed"] = args.seed if args.seed is not None else random.randrange(2**32)
    sampler["steps"] = args.steps
    sampler["cfg"] = args.cfg
    if args.checkpoint:
        workflow["4"]["inputs"]["ckpt_name"] = args.checkpoint
    workflow["9"]["inputs"]["filename_prefix"] = args.prefix
    return sampler["seed"]


def cmd_txt2img(args):
    workflow = load_workflow("txt2img-sd15.json")
    seed = common_fill(workflow, args)
    workflow["5"]["inputs"].update(width=args.width, height=args.height, batch_size=args.batch)
    print(json.dumps({"seed": seed}), file=sys.stderr)
    submit_and_wait(workflow, args.out, args.timeout)


def cmd_img2img(args):
    workflow = load_workflow("img2img-sd15.json")
    seed = common_fill(workflow, args)
    workflow["10"]["inputs"]["image"] = stage_image(args.image)
    workflow["12"]["inputs"].update(width=args.width, height=args.height)
    workflow["3"]["inputs"]["denoise"] = args.denoise
    print(json.dumps({"seed": seed}), file=sys.stderr)
    submit_and_wait(workflow, args.out, args.timeout)


def cmd_run(args):
    workflow = load_workflow(args.workflow)
    for assignment in args.set or []:
        key, _, value = assignment.partition("=")
        set_path(workflow, key, value)
    for assignment in args.image or []:
        key, _, value = assignment.partition("=")
        set_path(workflow, key, stage_image(value))
    submit_and_wait(workflow, args.out, args.timeout)


NEGATIVE = ("text, watermark, logo, signature, blurry, low quality, deformed, extra fingers, "
            "bad anatomy, oversaturated, cartoon")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("start").set_defaults(func=cmd_start)
    sub.add_parser("stop").set_defaults(func=cmd_stop)
    sub.add_parser("status").set_defaults(func=cmd_status)

    def gen_args(p):
        p.add_argument("--prompt", required=True)
        p.add_argument("--negative", default=NEGATIVE)
        p.add_argument("--width", type=int, default=512)
        p.add_argument("--height", type=int, default=768)
        p.add_argument("--steps", type=int, default=20)
        p.add_argument("--cfg", type=float, default=7.0)
        p.add_argument("--seed", type=int)
        p.add_argument("--checkpoint")
        p.add_argument("--prefix", default="exotico")
        p.add_argument("--out", default="salida-ia")
        p.add_argument("--timeout", type=int, default=1800)

    t2i = sub.add_parser("txt2img")
    gen_args(t2i)
    t2i.add_argument("--batch", type=int, default=1)
    t2i.set_defaults(func=cmd_txt2img)

    i2i = sub.add_parser("img2img")
    gen_args(i2i)
    i2i.add_argument("--image", required=True)
    i2i.add_argument("--denoise", type=float, default=0.45,
                     help="0.2 conserva casi todo; 0.6 reinterpreta mucho")
    i2i.set_defaults(func=cmd_img2img)

    run = sub.add_parser("run", help="Ejecuta un flujo en formato API de ComfyUI")
    run.add_argument("workflow")
    run.add_argument("--set", action="append", metavar="NODO.inputs.CAMPO=VALOR")
    run.add_argument("--image", action="append", metavar="NODO.inputs.image=RUTA")
    run.add_argument("--out", default="salida-ia")
    run.add_argument("--timeout", type=int, default=3600)
    run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
