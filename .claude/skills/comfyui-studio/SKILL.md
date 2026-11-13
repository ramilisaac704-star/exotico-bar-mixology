---
name: comfyui-studio
description: Estudio de generación multimedia con IA para EXÓTICO BAR & MIXOLOGY usando ComfyUI local, gratuito y de código abierto. Úsala para generar imágenes desde texto, transformar fotografías (img2img), preparar fondos, texturas y variaciones para publicidad, Reels e Instagram, o cuando se pida instalar, arrancar o comprobar ComfyUI y sus modelos. Sin APIs de pago.
---

# ComfyUI Studio — EXÓTICO

Genera imágenes (y, con GPU, video) en un servidor ComfyUI **local**. Nada sale a servicios de pago: el cliente solo habla con `127.0.0.1:8188`.

Antes de generar nada para la marca, aplica `exotico-brand-director`.

## Regla de marca para la IA

- **Permitido:** fondos, texturas, humo, ambientes abstractos, ilustraciones claramente gráficas, variaciones estilizadas de fotos reales, mejoras de material real, conceptos y moodboards internos.
- **Prohibido:** generar escenas que aparenten ser eventos, clientes, bartenders o cócteles reales de EXÓTICO; rostros de personas reales; logotipos.
- Toda imagen generada que se publique debe ser reconocible como gráfica o ir declarada como creada con IA.
- Publicar sigue requiriendo aprobación del dueño.

## Componentes

| Archivo | Función |
|---|---|
| `scripts/install.sh` | Comprueba el hardware, instala ComfyUI en `~/ComfyUI` (fuera del proyecto) y descarga el modelo base |
| `scripts/comfy.py` | Cliente: `start`, `stop`, `status`, `txt2img`, `img2img`, `run` |
| `workflows/txt2img-sd15.json` | Texto → imagen |
| `workflows/img2img-sd15.json` | Foto → imagen |
| `workflows/txt2img-sdxl-lightning.json` | Texto → imagen fotorrealista (SDXL, requiere CPU con AMX o GPU) |

Todo es software libre: ComfyUI (GPL-3.0), PyTorch (BSD), Stable Diffusion 1.5 (CreativeML OpenRAIL-M, permite uso comercial con restricciones de contenido).

## Paso 1: comprobar el hardware (siempre primero)

```bash
bash .claude/skills/comfyui-studio/scripts/install.sh --solo-comprobar
```

| Nivel | Requisito | Qué permite de forma realista |
|---|---|---|
| `cpu` | Sin GPU, ≥ 8 GB RAM | Imágenes SD 1.5 a 512 px en **5–7 minutos cada una**. Sin video. Solo para bocetos y fondos |
| `gpu-baja` | NVIDIA 4–6 GB | SD 1.5 en segundos |
| `gpu-media` | NVIDIA 6–12 GB | SDXL; video corto con Wan 2.1 1.3B |
| `gpu-alta` | NVIDIA ≥ 12 GB | FLUX.1-schnell, Wan 2.1 14B, LTX-Video |

**No descargues modelos pesados en un nivel que no los soporta.** Si el nivel es `cpu`, dilo con claridad y no prometas video ni calidad publicitaria.

## Paso 2: instalar y arrancar

```bash
bash .claude/skills/comfyui-studio/scripts/install.sh      # ~10 min, ~7 GB de disco
python3 .claude/skills/comfyui-studio/scripts/comfy.py start
python3 .claude/skills/comfyui-studio/scripts/comfy.py status
```

En las sesiones en la nube el contenedor es temporal: ComfyUI y los modelos **desaparecen al terminar la sesión** y hay que reinstalar. `status` devuelve `apagado` si no está.

## Paso 3: generar

**Texto → imagen**

```bash
python3 .claude/skills/comfyui-studio/scripts/comfy.py txt2img \
  --prompt "elegant golden smoke swirling on pure black background, cinematic lighting, macro, minimal" \
  --width 512 --height 768 --steps 20 --seed 7 --out /ruta/de/salida
```

**Foto → imagen**

```bash
python3 .claude/skills/comfyui-studio/scripts/comfy.py img2img \
  --image contenido/fotos/hero-poster.jpg \
  --prompt "oil painting illustration of a smoked cocktail, golden and black palette, luxury poster art" \
  --denoise 0.5 --width 512 --height 896 --out /ruta/de/salida
```

`--denoise`: 0.2–0.35 conserva la foto casi intacta; 0.4–0.55 la estiliza; más de 0.6 la reinventa.

**Flujo propio** (exportado desde ComfyUI con «Save (API Format)»):

```bash
python3 .claude/skills/comfyui-studio/scripts/comfy.py run mi-flujo.json \
  --set 6.inputs.text="nuevo prompt" --image 10.inputs.image=foto.jpg --out /ruta
```

Guarda las salidas de prueba en el directorio temporal de la sesión. Solo copia al proyecto (`contenido/ia/`) las que el dueño apruebe.

## Tamaños para Instagram

SD 1.5 trabaja bien cerca de 512 px. Genera pequeño y amplía después.

| Destino | Generar a | Escalar a |
|---|---|---|
| Historia / Reel 9:16 | 512 × 896 | 1080 × 1920 |
| Publicación 4:5 | 512 × 640 | 1080 × 1350 |
| Cuadrado | 512 × 512 | 1080 × 1080 |

## Prompts

- En inglés, sujeto primero, luego luz y estilo.
- Vocabulario de marca: `black background, gold accents, cinematic lighting, low key, luxury, minimal, shallow depth of field`.
- Fija `--seed` para repetir un resultado y variar solo el prompt.
- SD 1.5 no escribe texto legible: los titulares se añaden después con las plantillas HTML de `contenido/`.

## Usos para publicidad y Reels

1. **Fondo para pieza gráfica:** `txt2img` de humo, mármol o textura dorada → usar como `.bg` en `contenido/graficos/piezas.html` con velo y tipografía de marca.
2. **Portada estilizada:** `img2img` de una foto real con `--denoise 0.35` para unificar el look de una serie.
3. **Variaciones para anuncios:** misma foto y prompt con 3–4 semillas; elegir una.
4. **Video (solo con GPU):** animar una foto real con un modelo imagen → video. No disponible en nivel `cpu`.

## Video: estado real

No hay flujos de video incluidos porque no se pudieron verificar sin GPU. Modelos abiertos adecuados cuando haya tarjeta gráfica:

| Modelo | Licencia | VRAM | Uso |
|---|---|---|---|
| Wan 2.1 T2V 1.3B | Apache 2.0 | ~8 GB | Texto → video 480p |
| Wan 2.1 I2V 14B | Apache 2.0 | ≥ 16 GB (menos con versiones cuantizadas) | Imagen → video |
| LTX-Video | Licencia propia abierta; revisar condiciones | ≥ 12 GB | Video rápido |
| FLUX.1-schnell | Apache 2.0 | ≥ 12 GB | Imagen de alta calidad |

Con GPU: carga la plantilla oficial del modelo en ComfyUI (menú *Workflow → Browse Templates*), expórtala en formato API, guárdala en `workflows/` y ejecútala con `comfy.py run`. Verifica la licencia de cada modelo antes de usarlo en publicidad.

## CPU con AMX: SDXL fotorrealista sin GPU

Los Xeon recientes (indicadores `amx_bf16` o `avx512_bf16` en `/proc/cpuinfo`) calculan en media precisión de 3 a 6 veces más rápido. `install.sh` lo detecta, parchea ComfyUI y descarga **RealVisXL V5.0 Lightning** (SDXL, OpenRAIL++); `comfy.py start` activa el modo solo.

```bash
python3 .claude/skills/comfyui-studio/scripts/comfy.py run txt2img-sdxl-lightning.json \
  --set "6.inputs.text=cinematic photograph of ..., ultra realistic photograph, cinematic lighting" \
  --set 3.inputs.seed=11 --out /ruta
```

- 768 × 1344 (9:16), 6 pasos, `euler` / `sgm_uniform`, CFG 1: **unos 95 s por imagen**, calidad apta para piezas finales.
- SDXL ocupa ~9 GB de RAM: no ejecutes a la vez otros procesos pesados (el contenedor se reinicia si se agota la memoria) y detén el servidor con `comfy.py stop` al terminar.
- Revisa cada imagen a resolución completa: manos, caras en grupo y objetos apilados fallan a menudo; regenera con otra semilla.
- Ejemplo completo de producción: `contenido/video/ai-commercial-v1/` (imágenes → paralaje 3D → voz → música → montaje).

## Resultados verificados (sesión en la nube, 4 núcleos, 15 GB RAM, sin GPU)

| Prueba | Tamaño | Tiempo |
|---|---|---|
| `txt2img`, 20 pasos | 512 × 768 | 347 s |
| `img2img`, 20 pasos, denoise 0.5 | 512 × 896 | 429 s |
| SDXL Lightning, 6 pasos, media precisión | 768 × 1344 | ~95 s |

Calidad: suficiente para fondos y bocetos; por debajo del estándar de marca para piezas finales.

## Problemas frecuentes

- **`ComfyUI no está en marcha`** → `comfy.py start`; si falla, revisar `~/ComfyUI/.exotico-server.log`.
- **`ComfyUI rechazó el flujo`** → el JSON referencia un modelo o nodo que no está instalado; `status` lista los checkpoints disponibles.
- **Muy lento** → nivel `cpu`; reduce a 512 × 512 y 12–15 pasos, o usa una máquina con GPU.

## Procedencia

Inspirada en `MastroMimmo/comfyui-claude-skill` (MIT), que no se instaló: es un repositorio de un solo commit y sin historial verificable. El cliente de esta Skill se escribió desde cero contra la API pública de ComfyUI.
