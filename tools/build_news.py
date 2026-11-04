#!/usr/bin/env python3
"""Genera la sección «Actualidad» a partir de content/noticias/*.html.

Cada artículo empieza con un bloque de metadatos:

    <!--
    title: Título del artículo
    date: 2026-10-23
    description: Resumen breve (aparece en Google y en las tarjetas)
    image: agenda-abierta.jpg        (opcional, en assets/img/)
    category: Noticias               (Noticias | Consejos)
    -->
    <p>Contenido en HTML…</p>

Uso:  python3 tools/build_news.py
Genera: noticias/*.html, noticias/index.html, noticias/feed.xml,
        las 3 últimas tarjetas en index.html, sitemap.xml y robots.txt.
"""
import html, json, pathlib, re
from email.utils import format_datetime
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://retuertographic.github.io/podo/"
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha(d):
    y, m, dd = map(int, d.split("-"))
    return f"{dd} de {MONTHS[m - 1]} de {y}"


def load_posts():
    posts = []
    for f in sorted((ROOT / "content/noticias").glob("*.html")):
        txt = f.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--(.*?)-->(.*)", txt, re.S)
        meta = {}
        for line in m.group(1).strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        meta["slug"] = f.stem
        meta["body"] = m.group(2).strip()
        meta.setdefault("category", "Noticias")
        posts.append(meta)
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def relink(fragment, prefix="../"):
    """Ajusta los enlaces relativos de la cabecera/pie para páginas en subcarpetas."""
    def fix(m):
        attr, val = m.group(1), m.group(2)
        if re.match(r"(https?:|tel:|mailto:|data:|/)", val):
            return m.group(0)
        if val.startswith("#"):
            # los iconos <use href="#…"> se quedan igual
            return m.group(0) if attr == "use" else f'href="{prefix}{val}"'
        return f'{attr}="{prefix}{val}"'
    fragment = re.sub(r'<use href="(#[^"]+)"', lambda m: f'<use HREFKEEP="{m.group(1)}"', fragment)
    fragment = re.sub(r'\b(href|src)="([^"]*)"', fix, fragment)
    return fragment.replace("HREFKEEP=", "href=")


def card(p, prefix):
    if p.get("image"):
        thumb = (f'<div class="news-thumb"><img src="{prefix}assets/img/{p["image"]}" '
                 f'alt="" loading="lazy"></div>')
    else:
        thumb = '<div class="news-thumb noimg"><svg class="ico" aria-hidden="true"><use href="#i-news"/></svg></div>'
    link = f"{prefix}noticias/{p['slug']}.html"
    return f'''          <a class="news-card" href="{link}">
            {thumb}
            <div class="news-body">
              <p class="news-meta"><span class="news-cat">{html.escape(p["category"])}</span><time datetime="{p["date"]}">{fecha(p["date"])}</time></p>
              <h3>{html.escape(p["title"])}</h3>
              <p>{html.escape(p["description"])}</p>
              <span class="news-more" data-i18n="nw.read">Leer más →</span>
            </div>
          </a>'''


def head(title, desc, url, image=None, extra=""):
    img = f'\n  <meta property="og:image" content="{SITE}assets/img/{image}">' if image else ""
    return f'''<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(desc)}">
  <link rel="canonical" href="{url}">
  <meta name="theme-color" content="#3c5045">
  <link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">
  <link rel="alternate" type="application/rss+xml" title="Actualidad · Podología y Posturología SCR" href="feed.xml">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">{img}
  <meta property="og:locale" content="es_ES">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Allura&family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../assets/css/styles.css">{extra}
</head>
<body>
  <a class="skip-link" href="#main" data-i18n="skip">Saltar al contenido</a>
'''


def main():
    index_path = ROOT / "index.html"
    index = index_path.read_text(encoding="utf-8")
    header = re.search(r"<!--HEADER-->(.*?)<!--/HEADER-->", index, re.S).group(1)
    footer = re.search(r"<!--FOOTER-->(.*?)<!--/FOOTER-->", index, re.S).group(1)
    header, footer = relink(header), relink(footer)
    scripts = '\n  <script src="../assets/js/i18n.js"></script>\n  <script src="../assets/js/main.js"></script>\n</body>\n</html>\n'
    posts = load_posts()
    out = ROOT / "noticias"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.html"):
        old.unlink()

    cta = '''        <aside class="article-cta">
          <div>
            <h2 data-i18n="nw.ctaT">¿Quieres que valoremos tu caso?</h2>
            <p data-i18n="nw.ctaD">Pide tu cita y te la confirmamos personalmente.</p>
          </div>
          <a href="../#cita" class="btn btn-light btn-lg" data-i18n="hero.cta">Solicitar cita</a>
        </aside>'''

    for p in posts:
        url = f"{SITE}noticias/{p['slug']}.html"
        ld = {
            "@context": "https://schema.org",
            "@type": "BlogPosting" if p["category"] != "Noticias" else "NewsArticle",
            "headline": p["title"],
            "description": p["description"],
            "datePublished": p["date"],
            "inLanguage": "es",
            "mainEntityOfPage": url,
            "author": {"@type": "Person", "name": "Silvia Cáceres Romano"},
            "publisher": {"@type": "Organization", "name": "Podología y Posturología SCR"},
        }
        if p.get("image"):
            ld["image"] = f"{SITE}assets/img/{p['image']}"
        extra = f'\n  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
        cover = (f'        <figure class="article-cover"><img src="../assets/img/{p["image"]}" alt="{html.escape(p["title"])}"></figure>\n'
                 if p.get("image") else "")
        others = [o for o in posts if o is not p][:3]
        more = ""
        if others:
            more = ('      <section class="more-news container">\n        <h2 data-i18n="nw.more">Más actualidad</h2>\n'
                    '        <div class="news-grid">\n' + "\n".join(card(o, "../") for o in others) +
                    '\n        </div>\n      </section>\n')
        page = head(f'{p["title"]} · Podología y Posturología SCR', p["description"], url, p.get("image"), extra)
        page += header + f'''
  <main id="main">
    <article class="article">
      <div class="container narrow page-hero">
        <p class="breadcrumb"><a href="../">Inicio</a> / <a href="./" data-i18n="nav.news">Actualidad</a></p>
        <p class="eyebrow">{html.escape(p["category"])}</p>
        <h1>{html.escape(p["title"])}</h1>
        <p class="article-meta"><time datetime="{p["date"]}">{fecha(p["date"])}</time><span>·</span><span>Silvia Cáceres Romano</span></p>
        <p class="es-note" data-i18n="nw.esnote">Este artículo está disponible en español.</p>
{cover}        <div class="prose">
{p["body"]}
        </div>
{cta}
        <p style="margin-top:28px"><a href="./" data-i18n="nw.back">← Volver a Actualidad</a></p>
      </div>
    </article>
{more}  </main>
''' + footer + scripts
        (out / f"{p['slug']}.html").write_text(page, encoding="utf-8")

    # Listado
    listing = head("Actualidad · Podología y Posturología SCR · Breña Alta (La Palma) y Tenerife",
                   "Novedades de la consulta y consejos de podología y posturología de Silvia Cáceres Romano en La Palma y Tenerife.",
                   f"{SITE}noticias/")
    listing = listing.replace('<meta property="og:type" content="article">', '<meta property="og:type" content="website">')
    listing += header + '''
  <main id="main">
    <section class="section" style="padding-top:clamp(40px,6vw,72px)">
      <div class="container">
        <div class="section-head">
          <p class="breadcrumb"><a href="../">Inicio</a> / <span data-i18n="nav.news">Actualidad</span></p>
          <p class="eyebrow" data-i18n="nw.eyebrow">Actualidad</p>
          <h1 data-i18n="nw.listT">Novedades y consejos</h1>
          <p data-i18n="nw.listD">Novedades de la consulta y consejos sobre salud del pie y postura de la mano de Silvia Cáceres Romano.</p>
        </div>
        <div class="news-grid">
''' + "\n".join(card(p, "../") for p in posts) + '''
        </div>
      </div>
    </section>
  </main>
''' + footer + scripts
    (out / "index.html").write_text(listing, encoding="utf-8")

    # Tarjetas en la portada
    cards = "\n".join(card(p, "") for p in posts[:3])
    index = re.sub(r"<!--NEWS-->.*?<!--/NEWS-->", lambda m: f"<!--NEWS-->\n{cards}\n<!--/NEWS-->", index, flags=re.S)
    index_path.write_text(index, encoding="utf-8")

    # RSS
    items = ""
    for p in posts:
        d = datetime.strptime(p["date"], "%Y-%m-%d").replace(hour=9, tzinfo=timezone.utc)
        items += f'''  <item>
    <title>{html.escape(p["title"])}</title>
    <link>{SITE}noticias/{p["slug"]}.html</link>
    <guid>{SITE}noticias/{p["slug"]}.html</guid>
    <pubDate>{format_datetime(d)}</pubDate>
    <description>{html.escape(p["description"])}</description>
  </item>
'''
    (out / "feed.xml").write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Actualidad · Podología y Posturología SCR</title>
  <link>{SITE}noticias/</link>
  <description>Novedades y consejos de podología y posturología en La Palma y Tenerife.</description>
  <language>es</language>
{items}</channel></rss>
''', encoding="utf-8")

    # Sitemap y robots
    urls = [(SITE, posts[0]["date"] if posts else None), (f"{SITE}noticias/", posts[0]["date"] if posts else None)]
    urls += [(f"{SITE}noticias/{p['slug']}.html", p["date"]) for p in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, d in urls:
        sm += f"  <url><loc>{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>\n"
    (ROOT / "sitemap.xml").write_text(sm + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")
    print(f"{len(posts)} artículos generados.")


if __name__ == "__main__":
    main()
