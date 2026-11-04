# Podología y Posturología SCR — Web

Web estática (HTML/CSS/JS, sin dependencias) del Centro de Podología y Posturología SCR · Silvia Cáceres Romano (La Palma · Tenerife).

- Idiomas: español (principal, en el HTML), inglés y alemán (`assets/js/i18n.js`). Selector ES/EN/DE; también `?lang=en` / `?lang=de`.
- Solicitud de cita: el formulario valida los datos y abre WhatsApp (640 997 860) con la solicitud redactada en español. La cita queda pendiente hasta su confirmación.
- Burbuja flotante de WhatsApp con mensaje inicial según el idioma.

## Publicar
Basta con servir la carpeta (GitHub Pages, Netlify, cualquier hosting). Para verla en local: abrir `index.html`.

## Estructura y generación

La web se genera con `python3 tools/build.py` (sin dependencias). No edites a mano `index.html` ni `noticias/`: se sobrescriben.

| Carpeta | Contenido |
|---|---|
| `partials/` | Elementos comunes: `head`, `header`, `footer`, `whatsapp`, `icons`, `scripts`, `news-card`, `article-cta`. Se incluyen con `{{> nombre}}`; `{{root}}` es la ruta a la raíz. |
| `src/index.html` | Plantilla de la portada. |
| `templates/` | Plantillas de artículo y del listado de Actualidad. |
| `content/noticias/` | Artículos: `slug.html` (español) + `slug.en.html` y `slug.de.html`. El generador avisa si falta alguna traducción. |
| `assets/js/i18n.js` | Textos de la interfaz en inglés y alemán (el español está en el HTML). |

Genera: `index.html`, `noticias/*.html`, `noticias/feed.xml`, `sitemap.xml` y `robots.txt`.

Publicación: la web se sirve desde la rama `gh-pages` (https://retuertographic.github.io/podo/).

## Pendiente de completar
