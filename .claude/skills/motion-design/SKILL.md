---
name: motion-design
description: Animaciones web, transiciones, microinteracciones y efectos visuales elegantes para EXÓTICO BAR & MIXOLOGY. Úsala al añadir o revisar animaciones CSS/JS, efectos al hacer scroll, hover, entradas de secciones, parallax, video de fondo o cualquier movimiento en el sitio.
---

# Motion design — EXÓTICO BAR & MIXOLOGY

El movimiento debe sentirse como servir un buen cóctel: **lento, preciso y sin derramar nada.** Si una animación llama más la atención que el contenido, sobra.

## Principios

1. **Propósito.** Cada animación responde a una de tres funciones: orientar (de dónde viene y a dónde va algo), confirmar (la interfaz respondió) o dar ritmo a la lectura. Si no cumple ninguna, no se añade.
2. **Sobriedad.** Desplazamientos cortos (8–32 px), opacidad y escala mínima (≤ 1.04). Nada de rebotes, giros, sacudidas ni elásticos.
3. **Una vez.** Las entradas al hacer scroll se reproducen una sola vez; no se repiten al volver a subir.
4. **Nunca bloquea.** El contenido es legible y utilizable aunque la animación no se ejecute o JavaScript falle.
5. **Respeta `prefers-reduced-motion`.** Siempre.

## Tiempos y curvas

| Tipo | Duración | Curva |
|---|---|---|
| Hover, foco, pulsación | 150–250 ms | `ease` o `cubic-bezier(.2,.7,.2,1)` |
| Entrada de elementos | 500–800 ms | `cubic-bezier(.16,1,.3,1)` (salida suave) |
| Transición de secciones / velos | 600–1000 ms | `cubic-bezier(.65,0,.35,1)` |
| Escalonado entre elementos | 60–120 ms | — |

Define las curvas y duraciones como tokens; no escribas valores sueltos.

## Rendimiento

- Anima solo `transform` y `opacity`. Nunca `width`, `height`, `top`, `left`, `margin` ni `box-shadow` en bucle.
- `will-change` solo en el elemento que se está animando y retíralo después; no lo pongas de forma global.
- Usa `IntersectionObserver` para activar entradas; no escuches el evento `scroll` para esto.
- Para efectos ligados al scroll, prefiere CSS (`animation-timeline: view()`) con alternativa estática donde no haya soporte.
- Sin librerías pesadas para efectos que CSS resuelve. Si hace falta una, cárgala con `defer` y solo en la página que la usa.
- Objetivo: 60 fps en un Android de gama media y CLS ≈ 0 (las animaciones no deben mover el resto de la página).

## Repertorio aprobado

- **Aparición con ascenso:** opacidad 0→1 y `translateY(24px)`→0 para titulares, tarjetas y listas, con escalonado.
- **Revelado de foto:** `clip-path` o velo negro que se retira, más escala 1.06→1.
- **Filete dorado que se dibuja:** `scaleX(0)`→1 con `transform-origin: left`.
- **Brillo dorado en el botón principal:** un destello que cruza al pasar el cursor, una vez.
- **Zoom muy lento en el hero** (efecto Ken Burns, 1→1.06 en 12–20 s).
- **Cabecera** que gana fondo negro translúcido al bajar.
- **Video de fondo:** solo material real del negocio, silenciado, `playsinline`, con póster y pausado si el usuario prefiere menos movimiento.

## Evitar

Parallax agresivo, texto que se escribe letra a letra, cursores personalizados, partículas o humo generados por código, contadores animados de cifras no confirmadas, carruseles automáticos y pantallas de carga decorativas.

## Ejemplo: entradas al hacer scroll

```css
:root {
  --curva-salida: cubic-bezier(.16, 1, .3, 1);
  --dur-entrada: 700ms;
}

/* El contenido es visible por defecto; solo se oculta si JS está activo */
.js [data-aparece] {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity var(--dur-entrada) var(--curva-salida),
              transform var(--dur-entrada) var(--curva-salida);
  transition-delay: calc(var(--orden, 0) * 90ms);
}
.js [data-aparece].es-visible {
  opacity: 1;
  transform: none;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  .js [data-aparece] { opacity: 1; transform: none; }
}
```

```js
document.documentElement.classList.add('js');

const observador = new IntersectionObserver((entradas) => {
  for (const entrada of entradas) {
    if (!entrada.isIntersecting) continue;
    entrada.target.classList.add('es-visible');
    observador.unobserve(entrada.target); // una sola vez
  }
}, { threshold: 0.2, rootMargin: '0px 0px -10% 0px' });

document.querySelectorAll('[data-aparece]').forEach((el) => observador.observe(el));
```

```html
<h2 data-aparece>Experiencias</h2>
<article data-aparece style="--orden: 1">…</article>
<article data-aparece style="--orden: 2">…</article>
```

## Ejemplo: destello dorado en el botón

```css
.btn--primario { position: relative; overflow: hidden; }
.btn--primario::after {
  content: ""; position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 35%, rgb(255 255 255 / .45) 50%, transparent 65%);
  transform: translateX(-120%);
}
.btn--primario:hover::after { transform: translateX(120%); transition: transform 700ms var(--curva-salida); }
```

## Comprobación

- [ ] Con "reducir movimiento" activado, la página funciona y se lee completa.
- [ ] Con JavaScript desactivado, todo el contenido es visible.
- [ ] Solo se animan `transform` y `opacity`.
- [ ] Sin saltos de diseño (CLS) causados por animaciones.
- [ ] Fluido en móvil; ninguna animación dura más de 1 s salvo el zoom lento del hero.
- [ ] Cada animación cumple una función (orientar, confirmar o dar ritmo).
