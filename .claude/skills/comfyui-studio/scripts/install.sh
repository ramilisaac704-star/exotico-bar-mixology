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

# --- 4. CPU con AMX/AVX512-BF16: media precisión nativa (3-6 veces más rápido) --
if [ "$TIER" = "cpu" ] && grep -q -E "amx_bf16|avx512_bf16" /proc/cpuinfo; then
  # ComfyUI desactiva bf16 en CPU por defecto; comfy.py lo reactiva con COMFY_CPU_BF16=1.
  python3 - "$COMFY_DIR/comfy/model_management.py" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
if "COMFY_CPU_BF16" not in s:
    i = s.index("def should_use_bf16")
    head, body = s[:i], s[i:]
    body = body.replace("            return False\n", '            return os.environ.get("COMFY_CPU_BF16") == "1"\n', 1)
    body = body.replace("    if cpu_mode():\n        return False", '    if cpu_mode():\n        return os.environ.get("COMFY_CPU_BF16") == "1"', 1)
    if "import os" not in head.split("def ")[0]:
        head = "import os\n" + head
    open(p, "w").write(head + body)
PY
  XL="models/checkpoints/RealVisXL_V5.0_Lightning_fp16.safetensors"   # OpenRAIL++, 6,9 GB
  if [ ! -s "$XL" ] && [ "$RAM_GB" -ge 14 ] && [ "$DISK_GB" -ge 12 ]; then
    curl -sSL --fail --retry 3 -o "$XL" \
      "https://huggingface.co/SG161222/RealVisXL_V5.0_Lightning/resolve/main/RealVisXL_V5.0_Lightning_fp16.safetensors"
  fi
fi

echo "$TIER" > "$COMFY_DIR/.exotico-tier"
echo "Instalación completa en $COMFY_DIR (nivel: $TIER)"
