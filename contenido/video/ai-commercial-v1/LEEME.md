# THE ART OF THE EXPERIENCE — comercial generado con IA (v1)

Comercial vertical de 45 s (1080 × 1920, 30 fps) para EXÓTICO BAR & MIXOLOGY.
**Todas las escenas son imágenes generadas con inteligencia artificial**; no muestran eventos, personas ni instalaciones reales de la marca. La tarjeta final lo indica.

## Cómo está hecho

| Parte | Herramienta | Licencia |
|---|---|---|
| Imágenes (19 tomas, 768 × 1344) | ComfyUI + RealVisXL V5.0 Lightning (SDXL), 6 pasos, en CPU | GPL-3.0 / OpenRAIL++ |
| Movimiento de cámara | Paralaje por profundidad con Depth Anything V2 Small (`parallax.py`) | Apache-2.0 |
| Narración | Kokoro, voz `em_alex`, tono bajado un 8 % (`voz.py`, `audio.py`) | Apache-2.0 |
| Música | «Romantic Inspiration», colección FreePD | Dominio público (CC0) |
| Efectos de sonido | Sintetizados con numpy en `audio.py` | Propios |
| Presentación de marca | Animación HTML/canvas renderizada fotograma a fotograma (`marca.html`, `marca.js`) | Propia |
| Montaje, color y mezcla | FFmpeg (`montar.py`) | LGPL/GPL |

Sin servicios de pago, créditos ni cuentas. Todo se ejecutó localmente.

## Límite importante

No hay video generativo: la máquina no tiene tarjeta gráfica. Cada plano es una imagen fija con movimiento de cámara en 3D; los líquidos, el humo y las personas no se mueven.

## Archivos

- `tomas.json` — prompt y semilla de cada toma. `generar.py` las produce.
- `montaje.json` — orden de planos, duración en pulsos musicales, movimiento de cámara, narración y selección de imágenes.
- `edl.json`, `subtitulos.json` — tiempos resultantes.
- `recursos/imagenes/` — las 19 imágenes elegidas. `recursos/voz/` — narración sin procesar. `recursos/audio/` — mezcla final y tiempos.
- `exotico-the-art-of-the-experience.mp4` — versión final con subtítulos.

## Rehacerlo

```bash
python3 generar.py <tomas>                                    # ~95 s por imagen
~/ComfyUI/.venv/bin/python parallax.py <tomas> <planos>
python voz.py <modelo_kokoro> <voz>                            # entorno con kokoro-onnx
python3 audio.py <voz> Romantic_Inspiration.mp3 <audio>
node marca.js <marca> 8.8 30
python3 montar.py <planos> <marca> <audio> <final>
```

## Verificación hecha

- Cada imagen revisada a resolución completa; siete se regeneraron por manos deformes, objetos incoherentes o estilo fuera de marca.
- Narración comprobada por transcripción automática sobre la mezcla final: las cinco frases se reconocen íntegras.
- Sonoridad integrada: −13,7 LUFS, pico −1,4 dBFS.
- La música y la voz se eligieron por análisis (tempo, tonalidad, energía, tono), no por escucha: conviene oírlas antes de publicar.
