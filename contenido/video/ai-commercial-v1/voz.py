#!/usr/bin/env python3
"""Sintetiza la narración con Kokoro (Apache-2.0), voz masculina en español, en CPU.

Uso: python voz.py <carpeta_modelo> <carpeta_salida>
<carpeta_modelo> contiene kokoro-v1.0.onnx y voices-v1.0.bin (huggingface.co/fastrtc/kokoro-onnx).
Requiere: pip install kokoro-onnx soundfile
"""
import json, sys
from pathlib import Path
import soundfile as sf
from kokoro_onnx import Kokoro

model, out = Path(sys.argv[1]), Path(sys.argv[2])
cfg = json.loads((Path(__file__).resolve().parent / "montaje.json").read_text())
k = Kokoro(str(model / "kokoro-v1.0.onnx"), str(model / "voices-v1.0.bin"))
for i, esc in enumerate(cfg["escenas"], 1):
    audio, sr = k.create(esc["narracion"], voice="em_alex", speed=cfg["voz"]["velocidad"], lang="es")
    sf.write(out / f"linea_{i}.wav", audio, sr)
    print(i, round(len(audio) / sr, 2), "s", esc["narracion"])
