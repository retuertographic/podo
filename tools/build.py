#!/usr/bin/env python3
"""Genera la web estática a partir de plantillas, partials y contenidos.

Estructura:
  partials/   Elementos comunes (head, header, footer, whatsapp, icons,
              scripts, news-card, article-cta). Se incluyen con {{> nombre}}.
  src/        Páginas sueltas (index.html = portada).
  templates/  Plantillas de artículo y de listado de Actualidad.
  content/noticias/
              Un artículo = slug.html (español, obligatorio)
                          + slug.en.html y slug.de.html (traducciones).

Cada archivo de artículo empieza con metadatos:

    <!--
    title: Título
    description: Resumen (Google y tarjetas)
    date: 2026-10-23           (solo en el archivo en español)
    image: foto.jpg            (solo en español; en assets/img/)
    alt: Descripción de la foto
    category: Noticias         (Noticias | Consejos; solo en español)
    -->
    <p>Contenido en HTML…</p>

Variables: {{root}} es la ruta a la raíz ("" en la portada, "../" en noticias/).

Uso:  python3 tools/build.py
Genera index.html, noticias/*.html, noticias/feed.xml, sitemap.xml y robots.txt.
"""
import html, json, pathlib, re, sys
from email.utils import format_datetime
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://podo.retuertographicdesign.com/"
LANGS = ["es", "en", "de"]
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
CATEGORIES = {"Noticias": "nw.cat.news", "Consejos": "nw.cat.tips"}
warnings = []


def fecha(d):
    y, m, dd = map(int, d.split("-"))
    return f"{dd} de {MONTHS[m - 1]} de {y}"


def esc(t):
    return html.escape(t, quote=True)


# ---------- Plantillas ----------
def partial(name):
    return (ROOT / "partials" / f"{name}.html").read_text(encoding="utf-8").rstrip("\n")


def render(tpl, ctx):
    for _ in range(5):  # partials anidados
        tpl = re.sub(r"\{\{>\s*([\w-]+)\s*\}\}", lambda m: partial(m.group(1)), tpl)

    def var(m):
        k = m.group(1)
        if k not in ctx:
            sys.exit(f"Falta la variable {{{{{k}}}}}")
        return str(ctx[k])
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", var, tpl)


def ml(values, tag="span", attrs=""):
    """Un bloque por idioma; el CSS muestra solo el del idioma activo."""
    out = [f'<{tag}{attrs} data-l="{lang}" lang="{lang}">{values[lang]}</{tag}>' for lang in LANGS]
    return "".join(out) if tag == "span" else "\n".join(out)


# ---------- Contenidos ----------
def parse(path):
    txt = path.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--(.*?)-->(.*)", txt, re.S)
    if not m:
        sys.exit(f"{path}: falta el bloque de metadatos")
    meta = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    meta["body"] = m.group(2).strip()
    return meta


def load_posts():
    posts = []
    for f in sorted((ROOT / "content/noticias").glob("*.html")):
        if f.name.endswith((".en.html", ".de.html")):
            continue
        p = parse(f)
        p["slug"] = f.stem
        p.setdefault("category", "Noticias")
        p["t"] = {"es": p}
        for lang in ("en", "de"):
            tf = f.with_name(f"{f.stem}.{lang}.html")
            if tf.exists():
                p["t"][lang] = parse(tf)
            else:
                warnings.append(f"{f.stem}: falta la traducción «{lang}» (se muestra en español)")
                p["t"][lang] = p
        posts.append(p)
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def field(p, key):
    return {lang: p["t"][lang].get(key) or p.get(key, "") for lang in LANGS}


def card(p, root):
    if p.get("image"):
        thumb = f'<div class="news-thumb"><img src="{root}assets/img/{p["image"]}" alt="" loading="lazy"></div>'
    else:
        thumb = '<div class="news-thumb noimg"><svg class="ico" aria-hidden="true"><use href="#i-news"/></svg></div>'
    return render(partial("news-card"), {
        "href": f'{root}noticias/{p["slug"]}.html',
        "thumb": thumb,
        "cat_key": CATEGORIES[p["category"]], "cat_es": esc(p["category"]),
        "date": p["date"], "date_es": fecha(p["date"]),
        "title_ml": ml({k: esc(v) for k, v in field(p, "title").items()}),
        "desc_ml": ml({k: esc(v) for k, v in field(p, "description").items()}),
        "root": root,
    })


def main():
    posts = load_posts()
    out = ROOT / "noticias"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.html"):
        old.unlink()

    # Artículos
    for p in posts:
        url = f"{SITE}noticias/{p['slug']}.html"
        titles, descs, alts = field(p, "title"), field(p, "description"), field(p, "alt")
        ld = {
            "@context": "https://schema.org",
            "@type": "NewsArticle" if p["category"] == "Noticias" else "BlogPosting",
            "headline": p["title"], "description": p["description"],
            "datePublished": p["date"], "inLanguage": "es", "mainEntityOfPage": url,
            "author": {"@type": "Person", "name": "Silvia Cáceres Romano"},
            "publisher": {"@type": "Organization", "name": "Podología y Posturología SCR"},
        }
        cover, og_image = "", ""
        if p.get("image"):
            ld["image"] = f"{SITE}assets/img/{p['image']}"
            og_image = f'  <meta property="og:image" content="{SITE}assets/img/{p["image"]}">'
            cover = (f'        <figure class="article-cover"><img src="../assets/img/{p["image"]}" '
                     f'alt="{esc(alts["es"] or titles["es"])}" data-alt-en="{esc(alts["en"] or titles["en"])}" '
                     f'data-alt-de="{esc(alts["de"] or titles["de"])}"></figure>')
        body = ml({lang: "\n" + p["t"][lang]["body"] + "\n" for lang in LANGS}, tag="div", attrs=' class="prose"')
        others = [o for o in posts if o is not p][:3]
        more = ""
        if others:
            more = ('    <section class="more-news container">\n      <h2 data-i18n="nw.more">Más actualidad</h2>\n'
                    '      <div class="news-grid">\n' + "\n".join(card(o, "../") for o in others) +
                    '\n      </div>\n    </section>')
        page = render((ROOT / "templates/article.html").read_text(encoding="utf-8"), {
            "root": "../", "url": url,
            "title_es": esc(titles["es"]), "desc_es": esc(descs["es"]),
            "title_attrs": " ".join(f'data-title-{l}="{esc(titles[l])} · Podología y Posturología SCR"' for l in ("en", "de")),
            "og_image": og_image, "jsonld": json.dumps(ld, ensure_ascii=False),
            "cat_key": CATEGORIES[p["category"]], "cat_es": esc(p["category"]),
            "title_ml": ml({k: esc(v) for k, v in titles.items()}),
            "date": p["date"], "date_es": fecha(p["date"]),
            "cover": cover, "body_ml": body, "more": more,
        })
        (out / f"{p['slug']}.html").write_text(page, encoding="utf-8")

    # Listado
    listing = render((ROOT / "templates/news-list.html").read_text(encoding="utf-8"), {
        "root": "../", "url": f"{SITE}noticias/",
        "cards": "\n".join(card(p, "../") for p in posts),
    })
    (out / "index.html").write_text(listing, encoding="utf-8")

    # Portada
    home = render((ROOT / "src/index.html").read_text(encoding="utf-8"), {
        "root": "", "news_cards": "\n".join(card(p, "") for p in posts[:3]),
    })
    (ROOT / "index.html").write_text(home, encoding="utf-8")

    # RSS
    items = ""
    for p in posts:
        d = datetime.strptime(p["date"], "%Y-%m-%d").replace(hour=9, tzinfo=timezone.utc)
        items += (f'  <item>\n    <title>{esc(p["title"])}</title>\n'
                  f'    <link>{SITE}noticias/{p["slug"]}.html</link>\n'
                  f'    <guid>{SITE}noticias/{p["slug"]}.html</guid>\n'
                  f'    <pubDate>{format_datetime(d)}</pubDate>\n'
                  f'    <description>{esc(p["description"])}</description>\n  </item>\n')
    (out / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>\n'
        '  <title>Actualidad · Podología y Posturología SCR</title>\n'
        f'  <link>{SITE}noticias/</link>\n'
        '  <description>Novedades y consejos de podología y posturología en La Palma y Tenerife.</description>\n'
        f'  <language>es</language>\n{items}</channel></rss>\n', encoding="utf-8")

    # Sitemap y robots
    last = posts[0]["date"] if posts else None
    urls = [(SITE, last), (f"{SITE}noticias/", last)] + [(f"{SITE}noticias/{p['slug']}.html", p["date"]) for p in posts]
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')
    for u, d in urls:
        alts = f'<xhtml:link rel="alternate" hreflang="es" href="{u}"/>'
        alts += "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{u}?lang={l}"/>' for l in ("en", "de"))
        sm += f"  <url><loc>{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + alts + "</url>\n"
    (ROOT / "sitemap.xml").write_text(sm + "</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n", encoding="utf-8")

    for w in warnings:
        print("AVISO:", w)
    print(f"Portada + {len(posts)} artículos generados.")


if __name__ == "__main__":
    main()
