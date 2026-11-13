---
name: frontend-design
description: Diseño y construcción de interfaces web premium para EXÓTICO BAR & MIXOLOGY (barra móvil de coctelería para eventos). Úsala al crear o modificar páginas, secciones, componentes HTML/CSS/JS, landing pages, formularios de reserva o cualquier interfaz del sitio. Estética negra, dorada, elegante y minimalista.
---

# Frontend design — EXÓTICO BAR & MIXOLOGY

Construye interfaces que se sientan como la carta de un bar de lujo: oscuras, sobrias, con el dorado usado con moderación y la fotografía real como protagonista.

## Antes de escribir código

1. Lee lo que ya existe (`contenido/`, estilos, componentes) y reutilízalo. No dupliques tokens ni componentes.
2. Define el objetivo de la página en una frase. Para este negocio casi siempre es: **que el visitante pida una cotización**.
3. Decide la jerarquía: un solo mensaje principal por pantalla, una sola acción principal por sección.
4. Para decisiones de marca, movimiento, adaptación a pantallas o SEO, aplica también las skills `visual-design`, `motion-design`, `responsive-design` y `seo-optimization`.

## Reglas de marca (no negociables)

- **No inventes contenido de la marca.** Precios, teléfonos, direcciones, ciudad, testimonios, nombres de cócteles, cifras ("+200 eventos") y redes sociales solo se usan si el dueño los ha dado. Si falta un dato, deja un marcador visible `[DATO PENDIENTE: …]` y avisa en la respuesta.
- **No generes ni sustituyas imágenes de la marca.** Usa únicamente las de `contenido/fotos/` o las que el dueño aporte. Nada de fotos de stock ni generadas presentadas como eventos reales.
- **No modifiques ni borres archivos existentes** salvo que la tarea lo pida de forma explícita.

## Principios de interfaz

- **Negro primero.** El fondo es casi negro; las superficies se separan con cambios sutiles de luminosidad y líneas finas, no con sombras pesadas ni cajas de colores.
- **Dorado como acento, no como relleno.** Resérvalo para la acción principal, filetes, etiquetas pequeñas y una palabra enfatizada por titular. Si más del ~10 % de la pantalla es dorada, sobra dorado.
- **Aire.** Espaciado generoso y consistente (escala de 8 px). El lujo se percibe en el espacio vacío.
- **Fotografía grande, texto corto.** Titulares de 3 a 7 palabras; párrafos de 1 a 2 líneas.
- **Una acción principal por vista** ("Reserva tu fecha" / "Cotiza tu evento"), siempre visible en móvil.

## Estructura recomendada de una landing

1. **Hero:** foto real a pantalla completa con velo oscuro, titular, subtítulo y botón principal.
2. **Experiencias:** tarjetas con foto (flair, mixología molecular, coctelería de autor — confirma los nombres con el dueño).
3. **Qué incluye:** lista numerada con filetes finos.
4. **Galería:** fotos reales de eventos.
5. **Cómo funciona:** 3 pasos (cuéntanos → propuesta → brindis).
6. **Reserva:** formulario corto (nombre, fecha, tipo de evento, invitados, contacto) o enlace directo a WhatsApp.
7. **Pie:** sello, redes y contacto reales.

## Buenas prácticas de código

- HTML semántico: `header`, `nav`, `main`, `section` con `aria-labelledby`, `footer`; un solo `h1` por página y encabezados en orden.
- CSS con propiedades personalizadas para todos los colores, tipografías y espaciados; nada de valores sueltos repetidos.
- Clases con nombres por función (`.btn--primario`, `.tarjeta-experiencia`), no por apariencia (`.dorado-grande`).
- JavaScript mínimo, sin dependencias cuando no hacen falta, cargado con `defer`.
- Imágenes con `width`, `height`, `alt` descriptivo y `loading="lazy"` (excepto la del hero).
- Contraste AA como mínimo: texto crema sobre negro; el dorado sobre negro solo en texto de 18 px o más, o en negrita.
- Foco visible en todos los elementos interactivos (anillo dorado de 2 px).
- Formularios con `label` asociado, `autocomplete`, `inputmode` y mensajes de error junto al campo.

## Ejemplo: tokens y botón principal

```css
:root {
  /* Valores aproximados tomados del sello; sustituir por los oficiales si existen */
  --negro: #0a0806;
  --superficie: #14110c;
  --oro: #d9ad52;
  --oro-claro: #f3d78c;
  --oro-oscuro: #9c6f1f;
  --crema: #f4ead6;
  --linea: rgb(217 173 82 / 0.35);

  --esp-1: 0.5rem; --esp-2: 1rem; --esp-3: 1.5rem; --esp-4: 2rem;
  --esp-6: 3rem;   --esp-8: 4rem; --esp-12: 6rem;
  --radio-pildora: 999px;
}

.btn {
  display: inline-flex; align-items: center; justify-content: center;
  min-height: 48px; padding: 0 var(--esp-4);
  border-radius: var(--radio-pildora);
  font: 500 1rem/1 var(--fuente-texto); letter-spacing: 0.04em;
  text-decoration: none; cursor: pointer;
  transition: transform 0.2s ease, filter 0.2s ease;
}
.btn--primario {
  color: var(--negro);
  background: linear-gradient(100deg, var(--oro-claro), var(--oro) 60%, var(--oro-oscuro));
  border: 0;
}
.btn--secundario {
  color: var(--oro);
  background: transparent;
  border: 1px solid var(--linea);
}
.btn:hover { filter: brightness(1.08); transform: translateY(-1px); }
.btn:focus-visible { outline: 2px solid var(--oro-claro); outline-offset: 3px; }
```

## Ejemplo: hero

```html
<section class="hero" aria-labelledby="hero-titulo">
  <img class="hero__foto" src="contenido/fotos/g-barra.webp" alt="Bartender de Exótico preparando un cóctel en la barra durante un evento"
       width="1064" height="1600" fetchpriority="high">
  <div class="hero__contenido">
    <p class="etiqueta">Barra móvil de coctelería</p>
    <h1 id="hero-titulo">Llevamos el bar a <em>tu evento</em></h1>
    <a class="btn btn--primario" href="#reserva">Reserva tu fecha</a>
  </div>
</section>
```

## Lo que hay que evitar

- Degradados de colores vivos, neones, sombras duras, bordes gruesos, esquinas muy redondeadas en tarjetas.
- Más de dos familias tipográficas o más de un acento de color.
- Carruseles automáticos, ventanas emergentes al entrar, música o video con sonido automático.
- Texto sobre foto sin velo oscuro.
- Iconos de emoji como iconografía de la interfaz.

## Comprobación antes de entregar

- [ ] Se entiende qué es el negocio y qué hacer en los primeros 5 segundos.
- [ ] Hay una sola acción principal por sección y funciona.
- [ ] No hay ningún dato o imagen inventados; los pendientes están marcados y avisados.
- [ ] Probado a 360, 390, 768 y 1440 px de ancho sin desplazamiento horizontal.
- [ ] Navegable con teclado, foco visible, contraste AA.
- [ ] Sin errores en la consola del navegador.
