# Reel cinematográfico v2 (desde el 4K a 60 fps)

Rehecho desde `20260621_220247.mp4` (2160 × 3840, 59,94 fps, 89 s) con un planteamiento de cine en lugar de corte rápido.

## Qué cambia respecto a la v1

| | v1 | v2 |
|---|---|---|
| Duración | 19 s, 12 cortes de ~1 s | ~32 s, 12 planos de 1 a 6,5 s con respiración |
| Cámara | fija (recortes estáticos) | movimiento subpíxel sobre el 4K: avances, derivas y reencuadres con suavizado |
| Cámara lenta | 2× (fotogramas reales) | hasta 5× con fotogramas reales de 60 fps + interpolación RIFE 4.9 en CPU |
| Velocidad | constante por plano | rampas: el chorro y la coctelera entran a velocidad real y se congelan en el punto álgido |
| Formato | 9:16 lleno | bandas de cine de 100 px (imagen 1080 × 1720) |
| Color | corrección | etalonaje por ambiente + bloom cálido en altas luces + grano fino + viñeta |
| Música | dominio público elegida por análisis | «Simulacra» (Scott Buckley, CC BY 4.0): intro filtrada que se abre en el golpe, cortes al pulso |
| Sonido | brillo del audio real | audio real estirado con rubberband en los tramos lentos, dron, subida, golpe grave, aire en cada cámara lenta, swell final |
| Texto | 4 titulares grandes | tipografía de cine: cursiva fina, etiquetas espaciadas, entrada con deriva |

## Verificación hecha

- Encuadres inicial y final de los 12 planos revisados antes de renderizar; look de color probado en fotogramas reales (3 variantes por ambiente).
- Interpolación RIFE comprobada en pares de fotogramas reales: sin artefactos visibles en la coctelera ni en el humo.
- Montaje revisado plano a plano a tamaño completo: ningún texto tapa la acción; sin fotogramas negros salvo el corte a la tarjeta (0,2 s, intencional).
- Audio: −13,5 LUFS integrados, pico −1,5 dBFS; la transcripción automática de la mezcla no detecta letra (la canción del local quedó fuera).
- 963 fotogramas, 32,1 s, 1080 × 1920, 30 fps, 46 MB.

## Archivos

- `planos.json` — lista de planos: origen, pulsos, curva de velocidad, cámara inicial/final, ambiente, estabilización.
- `cine.py` — motor de planos (ejecutar con el Python de ComfyUI). `--preview` muestra encuadres sin renderizar.
- `rife_cpu.py` — interpolación RIFE 4.9 en CPU (pesos `rife49.pth`, nodo ComfyUI-Frame-Interpolation).
- `montar.py` — etalonaje, bloom, grano, bandas, textos, tarjeta final y banda sonora.
- `textos.html`, `portada.html` — tipografía.
- `edl.json`, `mezcla.json` — tiempos resultantes.

## Rehacer

```bash
~/ComfyUI/.venv/bin/python cine.py planos.json <original.mp4> <planos>
python3 montar.py <planos> Simulacra.mp3 <original.mp4> <final>
```

## Licencias

- Música: «Simulacra» de Scott Buckley, CC BY 4.0 — exige crédito al publicar (incluido en `publicacion.md`).
- RIFE (Apache-2.0), ComfyUI-Frame-Interpolation (MIT), FFmpeg, OpenCV, PyTorch. Sin servicios de pago.
