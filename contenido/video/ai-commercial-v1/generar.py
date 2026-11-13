#!/usr/bin/env python3
"""Genera las tomas del comercial con SDXL (RealVisXL V5 Lightning) en ComfyUI local.

Uso: python3 generar.py <carpeta_salida> [id ...] [--seed-offset N]
Sin ids genera todas las tomas de tomas.json. Con --seed-offset crea variantes.
"""
import json, sys, importlib.util, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[2] / ".claude" / "skills" / "comfyui-studio"
spec = importlib.util.spec_from_file_location("comfy", SKILL / "scripts" / "comfy.py")
comfy = importlib.util.module_from_spec(spec); spec.loader.exec_module(comfy)

args = sys.argv[1:]
offset = 0
if "--seed-offset" in args:
    i = args.index("--seed-offset"); offset = int(args[i + 1]); del args[i:i + 2]
out = Path(args[0]); ids = set(args[1:])
cfg = json.loads((HERE / "tomas.json").read_text())
base = json.loads((SKILL / "workflows" / "txt2img-sdxl-lightning.json").read_text())

for toma in cfg["tomas"]:
    if ids and toma["id"] not in ids:
        continue
    seed = toma["seed"] + offset
    name = f"{toma['id']}_s{seed}"
    if (out / f"{name}.png").exists():
        continue
    wf = json.loads(json.dumps(base))
    wf["6"]["inputs"]["text"] = toma["prompt"] + cfg["estilo"]
    wf["7"]["inputs"]["text"] = "text, watermark, logo, cartoon, illustration, deformed, blurry"
    wf["3"]["inputs"]["seed"] = seed
    wf["9"]["inputs"]["filename_prefix"] = name
    saved = comfy.submit_and_wait(wf, out / "_tmp", 1800)
    shutil.move(saved[0], out / f"{name}.png")
    print("OK", name, flush=True)
