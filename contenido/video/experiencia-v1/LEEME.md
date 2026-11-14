# Reel «Experiencia» (v1)

Editado desde `20260621_220247.mp4` (4K vertical, 60 fps, 89 s, grabado con el teléfono).

## Decisiones de edición

- **Selección:** 12 planos de 89 s de material. Se descartaron la ronda repetida de vertidos, los paneos al menú y las tomas movidas al caminar.
- **Estructura:** gancho con el vaso lleno de humo (cámara lenta) → entrada de la música en el sirope rojo → chorro alto, agitado y flair → la capa naranja sobre la roja → coctelera por encima de la cabeza → presenta el trago y se ríe a cámara → lleva el humo a la mesa de los invitados → tarjeta final.
- **Cámara lenta real:** los planos a 0,5× usan los fotogramas de 60 fps del original; no se inventan fotogramas.
- **Encuadres:** cada plano es un recorte 9:16 del 4K (planos generales, medios y de detalle sin pérdida de nitidez).
- **Estabilización:** vid.stab solo en las tomas del salón, grabadas en mano.
- **Color:** dos ajustes. Barra: blancos limpios, piel cálida, contraste suave. Salón: el morado de las luces LED se templó hacia ámbar para que case con la barra.
- **Textos:** «No solo preparo cócteles. / Creo experiencias. / Cada capa, a mano. / Y el humo llega a tu mesa.» Colocados donde no tapan la acción (el chorro y el vaso con el degradado quedan libres).
- **Música:** «Electronic K Deep Nyah», colección FreePD (dominio público, CC0). Su entrada fuerte coincide con el primer corte a la barra (2,63 s) y todos los cortes caen en pulso (136 ppm). Elegida por análisis, no por escucha.
- **Sonido:** se eliminó la canción que sonaba en el local. Del audio real solo queda el brillo del hielo y el metal en los planos a velocidad normal. Efectos sintetizados: silbido del humo, subida antes del corte, golpe grave, aire en las cámaras lentas y destello final. Sonoridad −14 LUFS, pico −1,4 dBFS.

## Archivos

- `planos.json` — lista de planos (origen, encuadre, velocidad, pulsos, ajuste de color).
- `build.py` — genera todo: `python3 build.py <original.mp4> <musica.mp3> <carpeta_trabajo>`.
- `textos.html`, `portada.html` — diseño de textos, tarjeta final y portada.
- `edl.json` — tiempos resultantes de cortes y textos.
