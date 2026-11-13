# Reel cinematográfico v1 — «Not just a bar. An experience.»

- **Duración:** 31,8 s · 1080 × 1920 · 30 fps.
- **Material:** tres tomas originales en 4K (un solo ángulo fijo). Los planos general, medio y de detalle son reencuadres del mismo original; ninguno amplía por encima de la resolución nativa.
- **Montaje:** `build.py` (lista `PLANOS`). Los tiempos exactos de cada corte quedan en `edl.json`.
- **Textos:** `textos.html`.
- **Color:** levantado de sombras para recuperar el rostro a contraluz, tonos cálidos, contraste suave y viñeta ligera.
- **Cámara lenta:** dos planos al 50 % con interpolación de movimiento.
- **Música:** «Electronic K Deep Nyah», de la colección FreePD (dominio público, CC0), descargada de archive.org/details/freepd. Se eligió por análisis de tempo (136 ppm) y energía, sin escucha humana: conviene oírla antes de publicar.
- **Sonido:** audio ambiente original de cada toma, bajo la música. Sin efectos añadidos ni narración.

Para rehacerlo: `python3 build.py <carpeta con v1.mp4 v2.mp4 v3.mp4> <musica.mp3> <carpeta de trabajo>`.
Los videos originales y los renders no se guardan en el repositorio por su tamaño.
