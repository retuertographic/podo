# Podología y Posturología SCR — Web

Web estática (HTML/CSS/JS, sin dependencias) del Centro de Podología y Posturología SCR · Silvia Cáceres Romano (La Palma · Tenerife).

- Idiomas: español (principal, en el HTML), inglés y alemán (`assets/js/i18n.js`). Selector ES/EN/DE; también `?lang=en` / `?lang=de`.
- Solicitud de cita: el formulario valida los datos y abre WhatsApp (640 997 860) con la solicitud redactada en español. La cita queda pendiente hasta su confirmación.
- Burbuja flotante de WhatsApp con mensaje inicial según el idioma.

## Publicar
Basta con servir la carpeta (GitHub Pages, Netlify, cualquier hosting). Para verla en local: abrir `index.html`.

## Actualidad (noticias y consejos)
Los artículos se escriben en `content/noticias/*.html` (ver el formato al inicio de `tools/build_news.py`). Después:

```
python3 tools/build_news.py
```

Esto genera las páginas de `noticias/`, el listado, el RSS (`noticias/feed.xml`), las 3 últimas tarjetas de la portada, `sitemap.xml` y `robots.txt`. La cabecera y el pie de las páginas de noticias se copian de `index.html`, así que vuelve a ejecutarlo si cambias esas partes.

Publicación: la web se sirve desde la rama `gh-pages` (https://retuertographic.github.io/podo/).

## Pendiente de completar
