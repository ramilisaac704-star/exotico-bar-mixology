# Reel promocional v1 — EXÓTICO BAR & MIXOLOGY

22,9 s · 1080 × 1920 · 30 fps · H.264 + AAC · −14 LUFS.

## Material

| Fuente | Archivo | Uso |
|---|---|---|
| a | `20261117_180621.mp4` (4K, 17 s) | Botellas de colores, medidores y cocteleras |
| b | `VID_20261117_151324_655.mp4` (720p, 60 s, poca luz) | Jugo a las cocteleras, lanzamiento de botella |
| c | `VID_20261117_151417_850.mp4` (720p, 60 s) | Coctelera sobre la cabeza, vertidos, vertido alto, presentación y entrega |
| j | `20260621_220247.mp4` (4K 60 fps, junio) | Humo en el vaso (gancho), coctelera congelada en lo alto, humo en la mesa |

## Montaje (`planos.json`, tiempos en `edl.json`)

0–1,8 s humo en el vaso a 5× lento (gancho, sin música aún) · 1,8 s entra la música: coctelera sobre la cabeza · botellas · jugo · doble vertido · medidores · lanzamiento de botella · preparación · vertido al pecho · coctelera congelada en lo alto · **vertido alto a 3× lento (plano héroe, 4,4 s)** · presenta · entrega · humo en la mesa · tarjeta final animada (3,5 s).

- Cortes al pulso del bombo (136 ppm, anclados a la rejilla real de graves).
- Cámara lenta con fotogramas reales + interpolación RIFE 4.9 (solo en los tramos lentos).
- Estabilización vid.stab en las tomas en mano; reducción de ruido y exposición en el video de poca luz.
- Etalonaje por fuente con bloom cálido (mezclado en RGB), grano fino y viñeta suave.
- Transiciones: destello en la entrada de la música y antes de la tarjeta; dos barridos con desenfoque direccional.
- Textos: «MIXOLOGÍA DE AUTOR», «SHOWTENDING», «No solo preparo cócteles.», «Creo experiencias.»; tarjeta final con sello, nombre, servicios, WhatsApp e Instagram.

## Sonido

Música: «Electronic K Deep Nyah» (FreePD, dominio público CC0), con barrido de filtro al final. Efectos sintetizados: subida, golpes graves, barridos, aire en las cámaras lentas, destello. Sonido real de hielo y metal (> 2,5 kHz) en los planos a velocidad normal. La transcripción automática de la mezcla no detecta letras.

## Rehacer

```bash
~/ComfyUI/.venv/bin/python cine3.py planos.json <carpeta_con_drive4_y_drive3> <planos>
python3 montar.py <planos> Electronic_K_Deep_Nyah.mp3 <carpeta_con_drive4_y_drive3> <final>
```
