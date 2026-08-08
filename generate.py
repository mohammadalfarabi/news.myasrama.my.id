import os
import re
import html
import json
from datetime import datetime

URL_PREVIEW = "https://news.myasrama.my.id"
OUTPUT_DIR = "docs"


def buat_slug(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text


def dapatkan_potongan_teks(text, length=160):
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = html.unescape(clean_text).replace('\n', ' ').strip()

    if len(clean_text) <= length:
        return clean_text

    return clean_text[:length].rsplit(' ', 1)[0] + '...'


def fetch_all_news():
    all_news = []

    raw_payload = os.environ.get("RAW_PAYLOAD_DATA", "").strip()

    if not raw_payload or raw_payload == "null":
        print("Payload kosong.")
        return all_news

    try:
        # Payload kadang dikirim sebagai JSON string
        if raw_payload.startswith('"') and raw_payload.endswith('"'):
            try:
                raw_payload = json.loads(raw_payload)
            except Exception:
                raw_payload = (
                    raw_payload[1:-1]
                    .replace('\\"', '"')
                    .replace('\\\\', '\\')
                )

        news_data = json.loads(raw_payload)

        # Jika hasil parsing masih berupa string JSON
        if isinstance(news_data, str):
            news_data = json.loads(news_data)

        if isinstance(news_data, list):
            print(
                f"Berhasil memuat {len(news_data)} data berita dari payload."
            )
            return news_data

    except Exception as e:
        print(f"Gagal memparsing payload: {e}")

    return all_news


def tentukan_gambar(gambar):
    """
    Menentukan URL gambar.
    Karena sekarang gambar dari ImgBB biasanya sudah berupa URL penuh.
    """

    fallback = (
        "https://i.ibb.co.com/G4NGrYXh/"
        "logo-baru-asrama.png"
    )

    if not gambar:
        return fallback

    gambar = str(gambar).strip()

    if gambar.startswith("http://") or gambar.startswith("https://"):
        return gambar

    return fallback


def buat_rekomendasi_html(
    rekomendasi_ids,
    news_by_id,
    current_id
):
    if not rekomendasi_ids:
        return ""

    cards = ""

    for rekomendasi_id in rekomendasi_ids:

        try:
            rid = int(rekomendasi_id)
        except (ValueError, TypeError):
            continue

        # Jangan merekomendasikan berita yang sedang dibaca
        if rid == current_id:
            continue

        item = news_by_id.get(rid)

        if not item:
            continue

        judul = item.get("judul", "Berita")
        tanggal = item.get("tanggal", "")
        gambar = tentukan_gambar(item.get("gambar"))

        slug = buat_slug(judul)

        url = f"{URL_PREVIEW}/berita/{slug}/"

        cards += f"""
        <a href="{html.escape(url, quote=True)}"
           class="rekomendasi-card">

            <img
                src="{html.escape(gambar, quote=True)}"
                class="rekomendasi-img"
                alt="{html.escape(judul, quote=True)}"
                loading="lazy"
            >

            <div class="rekomendasi-body">

                <span class="rekomendasi-date">
                    {html.escape(str(tanggal))}
                </span>

                <div class="rekomendasi-item-title">
                    {html.escape(judul)}
                </div>

            </div>

        </a>
        """

    if not cards:
        return ""

    return f"""
    <section class="rekomendasi-section">

        <h3 class="rekomendasi-title">
            Rekomendasi Berita Terkait
        </h3>

        <div class="rekomendasi-grid">
            {cards}
        </div>

    </section>
    """


def build_site():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Membaca template HTML
    with open(
        "template.html",
        "r",
        encoding="utf-8"
    ) as f:
        template_content = f.read()

    berita_list = fetch_all_news()

    generated_items = []

    # Index berdasarkan ID untuk rekomendasi
    news_by_id = {}

    for item in berita_list:

        try:
            nid = int(item.get("id"))
            news_by_id[nid] = item
        except (ValueError, TypeError):
            continue

    print(
        f"Index berita berhasil dibuat: "
        f"{len(news_by_id)} berita."
    )

    for item in berita_list:

        nid = item.get("id")
        judul = item.get("judul")
        tanggal = item.get("tanggal", "")
        gambar = item.get("gambar")
        isi = item.get("isi", "")

        if not judul or not nid:
            continue

        try:
            nid = int(nid)
        except (ValueError, TypeError):
            continue

        slug = buat_slug(judul)

        if not slug:
            slug = f"berita-{nid}"

        # Deskripsi untuk OG
        potongan = dapatkan_potongan_teks(
            isi,
            160
        )

        # URL artikel SEKARANG langsung di news.myasrama
        url_artikel = (
            f"{URL_PREVIEW}/berita/{slug}/"
        )

        # Gambar
        url_gambar_aman = tentukan_gambar(gambar)

        # ------------------------------------------------
        # REKOMENDASI
        # ------------------------------------------------

        rekomendasi_ids = item.get(
            "rekomendasi",
            []
        )

        if not isinstance(
            rekomendasi_ids,
            list
        ):
            rekomendasi_ids = []

        rekomendasi_html = buat_rekomendasi_html(
            rekomendasi_ids,
            news_by_id,
            nid
        )

        # ------------------------------------------------
        # OPEN GRAPH
        # ------------------------------------------------

        og_meta_tags = f"""
<meta property="og:type" content="article">
<meta property="og:url"
      content="{html.escape(url_artikel, quote=True)}">
<meta property="og:title"
      content="{html.escape(judul, quote=True)}">
<meta property="og:description"
      content="{html.escape(potongan, quote=True)}">
<meta property="og:image"
      content="{html.escape(url_gambar_aman, quote=True)}">
<meta property="og:image:secure_url"
      content="{html.escape(url_gambar_aman, quote=True)}">
<meta property="og:image:type"
      content="image/jpeg">
<meta property="og:image:width"
      content="1200">
<meta property="og:image:height"
      content="630">
<meta property="og:site_name"
      content="Asrama UTM">
<meta property="og:locale"
      content="id_ID">

<meta name="twitter:card"
      content="summary_large_image">
<meta name="twitter:title"
      content="{html.escape(judul, quote=True)}">
<meta name="twitter:description"
      content="{html.escape(potongan, quote=True)}">
<meta name="twitter:image"
      content="{html.escape(url_gambar_aman, quote=True)}">
        """.strip()

        # ------------------------------------------------
        # ISI BERITA
        # ------------------------------------------------
        #
        # JANGAN html.escape() isi berita.
        #
        # Karena isi berita kamu kemungkinan sudah berupa
        # HTML dari editor.
        #
        isi_html = isi

        # ------------------------------------------------
        # REPLACE TEMPLATE
        # ------------------------------------------------

        html_rendered = template_content

        replacements = {

            "{og_meta}":
                og_meta_tags,

            "{judul}":
                html.escape(judul),

            "{deskripsi}":
                html.escape(potongan),

            "{url_gambar}":
                html.escape(
                    url_gambar_aman,
                    quote=True
                ),

            "{url_berita}":
                html.escape(
                    url_artikel,
                    quote=True
                ),

            "{url_preview}":
                html.escape(
                    url_artikel,
                    quote=True
                ),

            "{tanggal}":
                html.escape(str(tanggal)),

            "{isi}":
                isi_html,

            "{rekomendasi}":
                rekomendasi_html,

            # Supaya placeholder lama tidak
            # menyebabkan URL MyAsrama muncul
            "{url_tujuan}":
                url_artikel,

            "{potongan_isi}":
                html.escape(
                    dapatkan_potongan_teks(
                        isi,
                        250
                    )
                ),
        }

        for placeholder, value in replacements.items():
            html_rendered = html_rendered.replace(
                placeholder,
                value
            )

        # ------------------------------------------------
        # FOLDER ARTIKEL
        # ------------------------------------------------

        artikel_dir = os.path.join(
            OUTPUT_DIR,
            "berita",
            slug
        )

        os.makedirs(
            artikel_dir,
            exist_ok=True
        )

        artikel_file = os.path.join(
            artikel_dir,
            "index.html"
        )

        with open(
            artikel_file,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(html_rendered)

        print(
            f"[OK] Berita dibuat: "
            f"{url_artikel}"
        )

        generated_items.append({

            "id": nid,

            "judul": judul,

            "slug": slug,

            "tanggal": tanggal,

            "gambar": url_gambar_aman,

            "potongan": potongan,

            "url_preview": url_artikel
        })

    # ----------------------------------------------------
    # GENERATE FILE TAMBAHAN
    # ----------------------------------------------------

    generate_index_page(
        generated_items
    )

    generate_sitemap(
        generated_items
    )

    generate_rss(
        generated_items
    )

    generate_robots_txt()

    # CNAME
    with open(
        os.path.join(
            OUTPUT_DIR,
            "CNAME"
        ),
        "w",
        encoding="utf-8"
    ) as f:
        f.write(
            "news.myasrama.my.id"
        )

    print("")
    print("==============================")
    print("BUILD SELESAI")
    print(
        f"Total berita: "
        f"{len(generated_items)}"
    )
    print("==============================")


def generate_index_page(items):

    items_html = ""

    for item in items:

        gambar = item.get(
            "gambar",
            ""
        )

        items_html += f"""
        <article class="news-card">

            <a
                href="{html.escape(
                    item["url_preview"],
                    quote=True
                )}"
            >

                <img
                    src="{html.escape(
                        gambar,
                        quote=True
                    )}"
                    alt="{html.escape(
                        item["judul"],
                        quote=True
                    )}"
                    loading="lazy"
                >

                <div class="news-card-body">

                    <div class="news-date">
                        {html.escape(
                            str(item["tanggal"])
                        )}
                    </div>

                    <h2>
                        {html.escape(
                            item["judul"]
                        )}
                    </h2>

                    <p>
                        {html.escape(
                            item["potongan"]
                        )}
                    </p>

                </div>

            </a>

        </article>
        """

    index_content = f"""<!DOCTYPE html>
<html lang="id">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1.0"
>

<title>Berita Asrama UTM</title>

<meta
    name="description"
    content="Portal berita resmi Asrama UTM."
>

<style>

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        Helvetica,
        Arial,
        sans-serif;

    background: #f4f6f9;
    color: #1e293b;
    padding: 30px 20px;
}}

.container {{
    max-width: 1000px;
    margin: auto;
}}

.header {{
    margin-bottom: 30px;
}}

.header h1 {{
    font-size: 2rem;
    margin-bottom: 8px;
}}

.header p {{
    color: #64748b;
}}

.news-grid {{
    display: grid;
    grid-template-columns:
        repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
}}

.news-card {{
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow:
        0 4px 20px rgba(0,0,0,.05);
    transition:
        transform .2s,
        box-shadow .2s;
}}

.news-card:hover {{
    transform: translateY(-3px);
    box-shadow:
        0 8px 25px rgba(0,0,0,.08);
}}

.news-card a {{
    color: inherit;
    text-decoration: none;
}}

.news-card img {{
    width: 100%;
    height: 190px;
    object-fit: cover;
    display: block;
}}

.news-card-body {{
    padding: 18px;
}}

.news-date {{
    color: #64748b;
    font-size: .8rem;
    margin-bottom: 8px;
}}

.news-card h2 {{
    font-size: 1.05rem;
    line-height: 1.4;
    margin-bottom: 10px;
}}

.news-card p {{
    color: #64748b;
    font-size: .9rem;
    line-height: 1.6;
}}

@media(max-width:600px) {{

    body {{
        padding: 20px 12px;
    }}

    .header h1 {{
        font-size: 1.5rem;
    }}

    .news-grid {{
        grid-template-columns: 1fr;
    }}
}}

</style>

</head>

<body>

<div class="container">

    <header class="header">

        <h1>
            Berita Asrama UTM
        </h1>

        <p>
            Informasi dan berita terbaru
            Asrama Universitas Trunojoyo Madura.
        </p>

    </header>

    <main class="news-grid">

        {items_html}

    </main>

</div>

</body>

</html>
"""

    with open(
        os.path.join(
            OUTPUT_DIR,
            "index.html"
        ),
        "w",
        encoding="utf-8"
    ) as f:
        f.write(index_content)


def generate_sitemap(items):

    now = datetime.utcnow().strftime(
        '%Y-%m-%dT%H:%M:%S+00:00'
    )

    xml = """<?xml version="1.0"
encoding="UTF-8"?>
<urlset
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""

    xml += f"""
    <url>
        <loc>{URL_PREVIEW}/</loc>
        <lastmod>{now}</lastmod>
        <priority>1.0</priority>
    </url>
"""

    for item in items:

        xml += f"""
    <url>
        <loc>{html.escape(
            item["url_preview"]
        )}</loc>
        <lastmod>{now}</lastmod>
        <priority>0.8</priority>
    </url>
"""

    xml += """
</urlset>
"""

    with open(
        os.path.join(
            OUTPUT_DIR,
            "sitemap.xml"
        ),
        "w",
        encoding="utf-8"
    ) as f:
        f.write(xml)


def generate_rss(items):

    now = datetime.utcnow().strftime(
        '%a, %d %b %Y %H:%M:%S GMT'
    )

    xml = f"""<?xml version="1.0"
encoding="UTF-8"?>

<rss version="2.0">

<channel>

<title>Asrama UTM News</title>

<link>{URL_PREVIEW}</link>

<description>
Portal berita resmi Asrama UTM
</description>

<lastBuildDate>{now}</lastBuildDate>
"""

    for item in items:

        xml += f"""
<item>

<title>
{html.escape(item["judul"])}
</title>

<link>
{html.escape(item["url_preview"])}
</link>

<description>
{html.escape(item["potongan"])}
</description>

<guid>
{html.escape(item["url_preview"])}
</guid>

</item>
"""

    xml += """
</channel>

</rss>
"""

    with open(
        os.path.join(
            OUTPUT_DIR,
            "rss.xml"
        ),
        "w",
        encoding="utf-8"
    ) as f:
        f.write(xml)


def generate_robots_txt():

    content = f"""User-agent: *
Allow: /

Sitemap: {URL_PREVIEW}/sitemap.xml
"""

    with open(
        os.path.join(
            OUTPUT_DIR,
            "robots.txt"
        ),
        "w",
        encoding="utf-8"
    ) as f:
        f.write(content)


if __name__ == "__main__":
    build_site()
