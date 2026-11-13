---
name: visual-design
description: Dirección de arte e identidad visual de EXÓTICO BAR & MIXOLOGY — paleta negra y dorada, tipografía, composición, tratamiento de fotos y uso del sello. Úsala al diseñar piezas para redes, flyers, cartas, presentaciones, secciones web o cualquier decisión de color, tipografía, maquetación o estilo visual.
---

# Visual design — EXÓTICO BAR & MIXOLOGY

Dirección de arte: **negro, dorado, elegante y minimalista.** La referencia es el sello de la marca (`contenido/fotos/sello.webp`): fondo negro, aro dorado, fotografía en tono dorado y logotipo en serif de trazo fino.

## Fuentes de verdad

1. Lo que el dueño haya entregado: sello, fotos en `contenido/fotos/`, textos confirmados.
2. Lo ya producido en `contenido/graficos/` (mantén la coherencia con esas piezas).
3. Esta skill.

**No inventes elementos de marca:** no redibujes ni "mejores" el logotipo, no crees variantes del sello, no generes fotos y no atribuyas a la marca eslóganes, datos o servicios que el dueño no haya confirmado. Si falta un recurso (logo vectorial, tipografía oficial, códigos de color exactos), pídelo y trabaja mientras tanto con las aproximaciones de abajo, diciendo que lo son.

## Color

| Token | Valor | Uso |
|---|---|---|
| Negro | `#0a0806` | Fondo principal |
| Superficie | `#14110c` | Tarjetas y bloques sobre el fondo |
| Oro | `#d9ad52` | Acentos, filetes, etiquetas, botón principal |
| Oro claro | `#f3d78c` | Brillo del degradado, estados hover |
| Oro oscuro | `#9c6f1f` | Sombra del degradado |
| Crema | `#f4ead6` | Texto principal |

Valores aproximados extraídos del sello, no códigos oficiales.

- **Proporción 80 / 15 / 5:** negro, crema (texto), dorado.
- El dorado nunca es un bloque grande plano; va en líneas, palabras y botones. El degradado dorado (claro → oro → oscuro, ~100°) imita metal: úsalo en una palabra del titular o en el botón, no en ambos a la vez dentro del mismo bloque.
- No añadas otros colores de acento. El color lo aportan las fotos (cócteles, luces cálidas).

## Tipografía

El sello usa una serif romana de mayúsculas con mucho espaciado. La tipografía oficial no está confirmada; estas son equivalentes libres:

| Rol | Fuente | Estilo |
|---|---|---|
| Marca y etiquetas | Cinzel 400–500 | Mayúsculas, espaciado 0.14–0.4em |
| Titulares | Cormorant Garamond 600 | Interlineado 0.95–1.05; cursiva 500 para la palabra enfatizada |
| Texto | Outfit 300–400 | Interlineado 1.3–1.6 |

- Máximo dos tamaños de titular por pieza y un solo énfasis en cursiva dorada por titular.
- Escala modular ~1.25–1.333. En piezas de 1080 px: titular 120–150 px, texto 34–40 px, etiquetas 22–26 px.
- Nunca mayúsculas en párrafos; nunca texto justificado; nunca contornos ni sombras en el texto.

## Composición

- **Márgenes amplios:** ~9 % del ancho (96 px en 1080).
- **Marco fino dorado** a 36 px del borde, 2 px, ~55 % de opacidad, como firma de las piezas.
- **Un punto focal.** La foto o el titular mandan, no ambos. Texto abajo a la izquierda sobre velo; marca arriba a la izquierda.
- Alineación a la izquierda por defecto; centrada solo en piezas de cierre (reserva, sello).
- Pie con dos palabras en versalitas unidas por una línea fina.

## Fotografía

- Solo fotos reales del negocio. Prefiere las de luz cálida y fondo oscuro; encajan con la paleta sin retoque.
- Siempre con **velo degradado negro** bajo el texto (de 0 a ~95 % de opacidad) para garantizar contraste.
- Recorta para que el sujeto quede en el tercio opuesto al texto; no tapes caras ni manos en acción.
- No estires, no voltees (los textos de botellas quedarían al revés) y no apliques filtros de color distintos entre fotos de una misma serie.
- Las fotos de menos de ~1000 px de lado se ven suaves a pantalla completa: úsalas en tamaños pequeños o pide el original.
- Hay marcas comerciales de licores visibles en varias fotos: no las destaques ni sugieras patrocinio.

## Uso del sello

- Úsalo tal cual, sin recortar el aro, deformar ni recolorear.
- Zona de respeto: al menos 1/4 de su diámetro libre alrededor.
- Sobre fondo negro o muy oscuro; nunca sobre fotos claras.
- Como marca compacta, puede usarse el texto "EXÓTICO / BAR & MIXOLOGY" en Cinzel dorado; no es un sustituto del logotipo oficial.

## Ejemplo: pieza para Instagram (1080 × 1350)

```html
<section class="pieza">
  <img class="bg" src="../fotos/g-balance.webp" alt="">
  <div class="velo"></div>
  <div class="marco"></div>
  <div class="marca"><b>EXÓTICO</b><span>BAR &amp; MIXOLOGY</span></div>
  <div class="cont">
    <div class="eti">Experiencia · 01</div>
    <h2>Show de <em>flair</em></h2>
    <p>Una línea de apoyo, máximo dos.</p>
  </div>
</section>
```

La implementación completa de este sistema está en `contenido/graficos/piezas.html`; parte de ahí para nuevas piezas en lugar de empezar de cero.

## Formatos habituales

| Uso | Tamaño | Zona segura |
|---|---|---|
| Publicación Instagram | 1080 × 1350 | 96 px por lado |
| Historia / Reel / TikTok | 1080 × 1920 | 250 px arriba y 340 px abajo libres de texto |
| Cuadrado | 1080 × 1080 | 96 px |
| Portada web (OG) | 1200 × 630 | 60 px |

## Comprobación

- [ ] ¿Se lee el titular en miniatura (a 25 % del tamaño)?
- [ ] ¿El dorado ocupa poco y señala lo importante?
- [ ] ¿Contraste del texto ≥ 4.5:1 sobre su fondo real (con velo)?
- [ ] ¿Coherente con las piezas existentes (marco, marca, pie, tipografías)?
- [ ] ¿Todo el contenido y las imágenes son reales o están confirmados?
