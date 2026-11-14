# Reel «Todo listo» (v1)

Recorrido real de la barra montada en un hotel, grabado con el teléfono (`ramil_isaac-20261114-0003.mp4`, 720 × 1280, 20 s), editado al estilo de la marca.

- **Montaje:** 9 planos cortados al pulso de la música (117 ppm). Abre con el barrido por las botellas, recorre siropes, cocteleras y utensilios, y termina con la vista al lobby. Tiempos en `edl.json`.
- **Estabilización:** vid.stab en dos pasadas (la toma original se movía bastante al caminar).
- **Color:** más cálido, contraste suave y viñeta ligera; el plano general se aclaró porque era el más oscuro.
- **Resolución:** el original es 720p y se amplió a 1080p con Lanczos y un enfoque leve. Con el archivo original de la cámara se vería más nítido.
- **Audio:** el video original traía una canción comercial con letra; se eliminó por derechos. Música: «House D Reasonably Cool», colección FreePD (dominio público, CC0), elegida por análisis y no por escucha. Dos efectos suaves sintetizados (aire antes del lobby, destello en la tarjeta final). Sonoridad: −14 LUFS.
- **Textos:** `textos.html` — «Antes de que lleguen tus invitados… / cada detalle en su lugar. / Todo listo.» y tarjeta final con sello y WhatsApp.

Rehacer: `python3 build.py <video_original.mp4> <House_D_Reasonably_Cool.mp3> <carpeta_trabajo>`.
