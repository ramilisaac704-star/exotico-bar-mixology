---
name: seo-optimization
description: Posicionamiento en Google, SEO local, velocidad de carga y optimización técnica del sitio de EXÓTICO BAR & MIXOLOGY. Úsala al crear o revisar títulos, metadescripciones, encabezados, datos estructurados, sitemap, robots.txt, Open Graph, rendimiento, Core Web Vitals, optimización de imágenes o al auditar una página antes de publicarla.
---

# SEO optimization — EXÓTICO BAR & MIXOLOGY

Objetivo: que quien busque una barra de cócteles para su evento en la zona de servicio encuentre el sitio, cargue rápido en el móvil y pida una cotización.

## Regla de veracidad

El SEO de este proyecto **no inventa datos**. Ciudad, zona de servicio, teléfono, dirección, horarios, precios, reseñas, valoraciones y perfiles sociales solo se publican si el dueño los ha confirmado. Si faltan:

- usa marcadores `[DATO PENDIENTE: …]` y enuméralos en la respuesta;
- omite del JSON-LD las propiedades desconocidas (un dato estructurado falso puede acarrear una penalización);
- nunca añadas `aggregateRating` ni `review` sin reseñas reales y verificables.

## 1. Palabras clave

Negocio de servicio local: las búsquedas útiles combinan **servicio + evento + lugar**.

- Servicio: barra móvil, barra de cócteles, bartender para eventos, coctelería para eventos, show de flair, mixología molecular.
- Evento: bodas, cumpleaños, eventos corporativos, fiestas privadas.
- Lugar: `[DATO PENDIENTE: ciudad y zonas donde se presta el servicio]`.

Una intención principal por página. No repitas palabras clave de forma forzada; escribe para personas.

## 2. SEO en la página

| Elemento | Criterio |
|---|---|
| `<title>` | 50–60 caracteres, único: servicio + lugar + marca |
| Metadescripción | 140–160 caracteres con beneficio y llamada a la acción |
| `<h1>` | Uno por página, con la intención principal |
| Encabezados | Jerarquía ordenada `h2` → `h3`, descriptivos |
| URL | Corta, minúsculas, guiones, sin acentos: `/barra-movil-bodas/` |
| Imágenes | `alt` que describa la foto real; nombre de archivo descriptivo |
| Enlaces internos | Texto descriptivo, nunca "clic aquí" |
| Idioma | `<html lang="es">` (o la variante regional confirmada) |
| Canónica | `<link rel="canonical">` absoluta en cada página |

## 3. SEO técnico

- HTTPS, una sola versión del dominio (redirige `www` ↔ sin `www`).
- `robots.txt` que permita el rastreo y enlace al sitemap; `sitemap.xml` con todas las URL canónicas.
- Contenido principal en el HTML inicial, no inyectado solo con JavaScript.
- Página 404 propia; sin enlaces rotos ni cadenas de redirecciones.
- Etiquetas Open Graph y Twitter Card con imagen de 1200 × 630 (usando una foto real).
- Favicon e iconos a partir del sello.

## 4. Velocidad (Core Web Vitals)

| Métrica | Objetivo | Cómo lograrlo aquí |
|---|---|---|
| LCP | < 2.5 s | Imagen del hero en WebP/AVIF, tamaño justo, `fetchpriority="high"`, sin `loading="lazy"` |
| CLS | < 0.1 | `width`/`height` en imágenes, `font-display: swap` con fuente alternativa de métricas similares |
| INP | < 200 ms | JavaScript mínimo y diferido, sin tareas largas |

- Presupuesto orientativo por página: < 1.5 MB en total, < 100 KB de JS, imagen del hero < 200 KB.
- Imágenes: `srcset`/`sizes`, `loading="lazy"` y `decoding="async"` bajo el pliegue.
- Fuentes: máximo 2 familias y 4 archivos; `preconnect` al origen o, mejor, alojarlas en el propio sitio; `preload` de la del titular.
- CSS crítico en línea si el archivo es grande; elimina CSS y JS sin usar.
- Caché larga para recursos con nombre versionado; compresión Brotli o gzip.
- Las fotos son oscuras y comprimen bien: prueba calidad 70–80 en WebP antes de dar una por buena.

## 5. SEO local

- **Perfil de Empresa de Google:** es el factor más importante para un negocio local. Al ser un servicio a domicilio, se configura como *empresa de servicio en la zona* (sin dirección pública). Lo crea y verifica el dueño; no se puede hacer desde el código.
- Nombre, teléfono y zona idénticos en el sitio, el perfil de Google y las redes.
- Página o sección por tipo de evento (bodas, corporativos…) solo si hay contenido real para cada una.
- Reseñas: pedirlas a clientes reales tras cada evento; nunca redactarlas.

## Ejemplo: `<head>`

```html
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Barra móvil de cócteles para eventos en [DATO PENDIENTE: ciudad] | Exótico Bar &amp; Mixology</title>
  <meta name="description" content="Barra móvil, coctelería de autor y show en vivo para bodas, fiestas y eventos privados en [DATO PENDIENTE: ciudad]. Cotiza tu fecha.">
  <link rel="canonical" href="https://[DATO PENDIENTE: dominio]/">
  <meta name="theme-color" content="#0a0806">

  <meta property="og:type" content="website">
  <meta property="og:locale" content="es_[DATO PENDIENTE: país]">
  <meta property="og:title" content="Exótico Bar &amp; Mixology — Llevamos el bar a tu evento">
  <meta property="og:description" content="Barra móvil, coctelería de autor y show en vivo para tu evento.">
  <meta property="og:url" content="https://[DATO PENDIENTE: dominio]/">
  <meta property="og:image" content="https://[DATO PENDIENTE: dominio]/img/og-portada.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
</head>
```

## Ejemplo: datos estructurados

Incluye solo las propiedades confirmadas; borra las líneas de datos que no se tengan.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Exótico Bar & Mixology",
  "description": "Barra móvil de coctelería para bodas, fiestas y eventos privados.",
  "url": "https://[DATO PENDIENTE: dominio]/",
  "image": "https://[DATO PENDIENTE: dominio]/img/og-portada.jpg",
  "logo": "https://[DATO PENDIENTE: dominio]/img/sello.png",
  "telephone": "[DATO PENDIENTE: teléfono con prefijo internacional]",
  "areaServed": "[DATO PENDIENTE: ciudad o región]",
  "sameAs": ["[DATO PENDIENTE: URL de Instagram]"]
}
</script>
```

## Cómo auditar

1. **Estructura:** un `h1`, título y descripción únicos, canónica, `lang`, todos los `alt`.
2. **Datos estructurados:** JSON válido, sin marcadores pendientes en producción; validar en la Prueba de resultados enriquecidos de Google.
3. **Rendimiento:** Lighthouse en modo móvil con el Chromium instalado:
   ```bash
   npx lighthouse http://localhost:8080 --form-factor=mobile \
     --chrome-flags="--headless --no-sandbox" \
     --only-categories=performance,seo,accessibility,best-practices \
     --output=html --output-path=./lighthouse.html
   ```
   Objetivo: ≥ 90 en las cuatro categorías. Informa las puntuaciones reales, sin redondear al alza.
4. **Rastreo:** `robots.txt` y `sitemap.xml` accesibles, sin enlaces rotos.

Las pruebas de laboratorio no garantizan la posición en Google: el posicionamiento depende también de la antigüedad del dominio, las reseñas y la competencia. No prometas posiciones ni plazos.

## Comprobación antes de publicar

- [ ] Título y metadescripción únicos y dentro de la longitud.
- [ ] Un `h1`; encabezados en orden.
- [ ] Todas las imágenes con `alt`, dimensiones y formato moderno.
- [ ] Canónica, Open Graph, favicon, `theme-color`.
- [ ] JSON-LD válido y sin datos inventados ni marcadores pendientes.
- [ ] `robots.txt` y `sitemap.xml` presentes.
- [ ] Lighthouse móvil ≥ 90 (resultados reales adjuntos).
- [ ] Lista de datos pendientes entregada al dueño.
