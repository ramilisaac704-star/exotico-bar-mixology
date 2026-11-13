---
name: responsive-design
description: Adaptación del sitio de EXÓTICO BAR & MIXOLOGY a Android, iPhone, tablet y escritorio. Úsala al maquetar o revisar layouts, puntos de quiebre, tipografía fluida, imágenes adaptables, zonas táctiles, navegación móvil, áreas seguras de iPhone o cualquier problema de visualización en un dispositivo.
---

# Responsive design — EXÓTICO BAR & MIXOLOGY

La mayoría de visitantes llegará desde Instagram, TikTok o WhatsApp en un teléfono. **El móvil es el diseño principal;** tablet y escritorio son ampliaciones.

## Método

1. **Mobile-first.** Escribe los estilos base para 360 px y amplía con `min-width`. Evita `max-width` en media queries salvo casos puntuales.
2. **Fluido antes que por saltos.** Usa `clamp()`, `min()`, `max()`, grid con `auto-fit` y flex con `wrap`; añade puntos de quiebre solo cuando el contenido lo pide.
3. **El contenido manda.** Los puntos de quiebre se ponen donde el diseño se rompe, no en los tamaños de dispositivos concretos.

## Puntos de quiebre de referencia

| Nombre | Desde | Dispositivos |
|---|---|---|
| base | 0 | Teléfonos (360–430 px) |
| `sm` | 600 px | Teléfonos grandes en horizontal, tablets pequeñas |
| `md` | 900 px | Tablets, portátiles pequeños |
| `lg` | 1200 px | Escritorio |
| `xl` | 1600 px | Pantallas grandes (limitar ancho del contenido) |

Ancho máximo del contenido: ~1200 px; de los párrafos: 60–70 caracteres.

## Reglas

**Base del documento**
- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`. Nunca `user-scalable=no` ni `maximum-scale=1`.
- `box-sizing: border-box` global; `img, video { max-width: 100%; height: auto; }`.
- Sin desplazamiento horizontal en ningún ancho desde 320 px.

**Tipografía**
- Texto base ≥ 16 px (evita el zoom automático de iOS en campos de formulario).
- Titulares fluidos con `clamp()`; unidades `rem`, no `px` fijos.

**Táctil**
- Zonas táctiles ≥ 48 × 48 px con ≥ 8 px de separación.
- Los efectos `hover` van dentro de `@media (hover: hover)`; nada debe depender del hover para funcionar.
- Botón de acción principal fijo abajo en móvil para reservar o abrir WhatsApp.

**iPhone**
- Respeta las áreas seguras: `padding-bottom: max(1rem, env(safe-area-inset-bottom))` en barras fijas.
- Usa `100svh` / `100dvh` para alturas de pantalla completa (con `100vh` como alternativa previa); `100vh` solo queda cortado por la barra del navegador.
- `-webkit-text-size-adjust: 100%`.
- Videos con `playsinline muted` para que no abran a pantalla completa.

**Android**
- Prueba a 360 px de ancho (el más común) y con el tamaño de fuente del sistema aumentado.
- `<meta name="theme-color" content="#0a0806">` para que la barra del navegador sea negra.

**Imágenes**
- `srcset` + `sizes` para servir el tamaño adecuado; formatos WebP/AVIF.
- `object-fit: cover` con `object-position` ajustado por foto para no cortar al bartender ni al cóctel al cambiar la proporción.
- Dirección de arte con `<picture>` cuando el recorte vertical (móvil) y el horizontal (escritorio) deban ser fotos distintas.
- Siempre `width` y `height` (o `aspect-ratio`) para evitar saltos al cargar.

**Navegación**
- Móvil: logotipo + botón de menú; menú a pantalla completa en negro con enlaces grandes.
- Escritorio (`md`+): enlaces en línea y botón de reserva a la derecha.
- El menú se puede abrir, recorrer y cerrar con teclado (`Esc`), con `aria-expanded` actualizado.

## Ejemplo: base fluida

```css
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; font-size: 1rem; line-height: 1.6; overflow-x: clip; }
img, video { display: block; max-width: 100%; height: auto; }

:root {
  --margen: clamp(1.25rem, 5vw, 4rem);
  --titulo-1: clamp(2.5rem, 1.4rem + 5.5vw, 5.5rem);
  --titulo-2: clamp(1.9rem, 1.3rem + 3vw, 3.5rem);
  --seccion: clamp(4rem, 10vw, 9rem);
}

.contenedor { width: min(100% - 2 * var(--margen), 1200px); margin-inline: auto; }
.seccion { padding-block: var(--seccion); }

.hero { min-height: 100vh; min-height: 100svh; }

/* 1 columna en móvil → 2 → 3, sin media queries */
.experiencias {
  display: grid; gap: clamp(1rem, 3vw, 2rem);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
}

.barra-reserva {
  position: fixed; inset: auto 0 0 0;
  padding: .75rem var(--margen) max(.75rem, env(safe-area-inset-bottom));
  background: rgb(10 8 6 / .92); backdrop-filter: blur(8px);
}
@media (min-width: 900px) { .barra-reserva { display: none; } }

@media (hover: hover) {
  .tarjeta:hover img { transform: scale(1.04); }
}
```

## Ejemplo: imagen adaptable

```html
<picture>
  <source media="(min-width: 900px)" srcset="fotos/g-balance.webp" width="1600" height="1064">
  <img src="fotos/g-barra.webp" width="1064" height="1600"
       alt="Bartender de Exótico preparando un cóctel en la barra"
       fetchpriority="high" decoding="async">
</picture>
```

## Cómo probar

Hazlo con capturas reales, no de memoria. Con Playwright:

```js
const { chromium, devices } = require('playwright');
const perfiles = ['Pixel 7', 'iPhone 14', 'iPhone SE', 'iPad Mini', 'Desktop Chrome'];
(async () => {
  const navegador = await chromium.launch();
  for (const nombre of perfiles) {
    const contexto = await navegador.newContext({ ...devices[nombre] });
    const pagina = await contexto.newPage();
    await pagina.goto(process.argv[2]);
    const desborde = await pagina.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    console.log(nombre, desborde ? 'DESBORDA' : 'ok');
    await pagina.screenshot({ path: `captura-${nombre.replace(/\s/g, '-')}.png`, fullPage: true });
    await contexto.close();
  }
  await navegador.close();
})();
```

Chromium emula tamaño y táctil, no el motor de Safari: indica al dueño que confirme en un iPhone real lo relacionado con áreas seguras, video y formularios.

## Comprobación

- [ ] Sin desplazamiento horizontal a 320, 360, 390, 768, 1024 y 1440 px.
- [ ] Vertical y horizontal en móvil.
- [ ] Texto legible sin zoom; campos de formulario ≥ 16 px.
- [ ] Zonas táctiles ≥ 48 px; acción principal alcanzable con el pulgar.
- [ ] Nada tapado por la muesca o la barra inferior del iPhone.
- [ ] Las fotos no cortan caras ni cócteles en ningún ancho.
- [ ] Zoom del navegador al 200 % sin pérdida de contenido.
