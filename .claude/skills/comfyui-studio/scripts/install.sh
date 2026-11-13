#!/usr/bin/env bash
# Instala ComfyUI (GPL-3.0) fuera del proyecto y descarga un modelo acorde al hardware.
# Uso: bash install.sh [--solo-comprobar]
set -euo pipefail

COMFY_DIR="${COMFY_DIR:-$HOME/ComfyUI}"

# --- 1. Comprobación de hardware -------------------------------------------
CPUS=$(nproc)
RAM_GB=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
DISK_GB=$(df -Pk "$HOME" | awk 'NR==2 {printf "%d", $4/1024/1024}')
VRAM_GB=0
if command -v nvidia-smi >/dev/null 2>&1; then
  VRAM_GB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | sort -nr | head -1 | awk '{printf "%d", $1/1024}')
fi

if   [ "$VRAM_GB" -ge 12 ]; then TIER="gpu-alta"
elif [ "$VRAM_GB" -ge 6  ]; then TIER="gpu-media"
elif [ "$VRAM_GB" -ge 1  ]; then TIER="gpu-baja"
else TIER="cpu"; fi

echo "CPU: $CPUS núcleos | RAM: ${RAM_GB} GB | Disco libre: ${DISK_GB} GB | VRAM: ${VRAM_GB} GB | Nivel: $TIER"
if [ "${1:-}" = "--solo-comprobar" ]; then exit 0; fi

if [ "$RAM_GB" -lt 8 ] || [ "$DISK_GB" -lt 12 ]; then
  echo "Hardware insuficiente: se necesitan al menos 8 GB de RAM y 12 GB libres." >&2
  exit 1
fi

# --- 2. ComfyUI --------------------------------------------------------------
if [ ! -d "$COMFY_DIR/.git" ]; then
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi
cd "$COMFY_DIR"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip

if [ "$TIER" = "cpu" ]; then
  pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
else
  pip install --quiet torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
fi
pip install --quiet -r requirements.txt

# --- 3. Modelo base (Stable Diffusion 1.5, licencia CreativeML OpenRAIL-M) ----
# Funciona en todos los niveles, incluida CPU. Los modelos pesados (FLUX, Wan)
# solo se descargan a mano en niveles con GPU: ver SKILL.md.
CKPT="models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors"
if [ ! -s "$CKPT" ]; then
  curl -sSL --fail --retry 3 -o "$CKPT" \
    "https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/resolve/main/v1-5-pruned-emaonly-fp16.safetensors"
fi

echo "$TIER" > "$COMFY_DIR/.exotico-tier"
echo "Instalación completa en $COMFY_DIR (nivel: $TIER)"
