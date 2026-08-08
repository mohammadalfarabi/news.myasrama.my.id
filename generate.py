import os
import re
import html
import json
from datetime import datetime

# ============================================================
# KONFIGURASI
# ============================================================

URL_UTAMA = "[https://myasrama.my.id](https://myasrama.my.id)"
URL_PREVIEW = "[https://news.myasrama.my.id](https://news.myasrama.my.id)"

OUTPUT_DIR = "docs"

# ============================================================
# BUAT SLUG
# ============================================================

def buat_slug(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    text = text.strip('-')
    return text

# ============================================================
# POTONGAN TEKS
# ============================================================

def dapatkan_potongan_teks(text, length=160):
    clean_text = re.sub(r'<[^>]+>', '', str(text))
    clean_text = html.unescape(clean_text)
    clean_text = clean_text.replace('\n', ' ').strip()

    if len(clean_text) <= length:
        return clean_text

    return clean_text[:length].rsplit(' ', 1)[0] + '...'

# ============================================================
# AMBIL DATA BERITA DARI PAYLOAD
# ============================================================

def fetch_all_news():
    all_news = []
    raw_payload = os.environ.get("RAW_PAYLOAD_DATA", "").strip()

    if not raw_payload or raw_payload == "null":
        print("Payload kosong.")
        return all_news

    try:
        # Kadang GitHub memberikan JSON dalam bentuk string yang ter-encode.
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

        # Jika masih berupa string, decode sekali lagi.
        if isinstance(news_data, str):
            news_data = json.loads(news_data)

        if isinstance(news_data, list):
            print(f"Berhasil memuat {len(news_data)} data berita dari payload.")
            return news_data

    except Exception as e:
        print(f"Gagal memparsing payload: {e}")

    return all_news

# ============================================================
# MEMBUAT REKOMENDASI
# ============================================================

def buat_rekomendasi_html(item, berita_list):
    rekomendasi = item.get("rekomendasi", [])

    if not isinstance(rekomendasi, list) or not rekomendasi:
        return ""

    # Buat index berdasarkan ID
    berita_by_id = {
        str(news.get("id")): news
        for news in berita_list
        if news.get("id") is not None
    }

    html_output = """
<section class="rekomendasi-section">
<h3 class="rekomendasi-title">
    Rekomendasi Berita Terkait
</h3>
<div class="rekomendasi-grid">
"""

    for id_rek in rekomendasi:
        rek = berita_by_id.get(str(id_rek))

        if not rek:
            continue

        rek_judul = rek.get("judul", "")
        rek_tanggal = rek.get("tanggal", "")
        rek_gambar = rek.get("gambar")

        if not rek_judul:
            continue

        rek_slug = buat_slug(rek_judul)
        rek_url = f"{URL_PREVIEW}/berita/{rek_slug}/"
        rek_img = rek_gambar if rek_gambar else "[https://i.ibb.co.com/G4NGrYXh/logo-baru-asrama.png](https://i.ibb.co.com/G4NGrYXh/logo-baru-asrama.png)"

        html_output += f"""
    <a href="{html.escape(rek_url, quote=True)}" class="rekomendasi-card">
        <img src="{html.escape(rek_img, quote=True)}" class="rekomendasi-img" alt="{html.escape(rek_judul, quote=True)}">
        <div class="rekomendasi-body">
            <span class="rekomendasi-date">{html.escape(str(rek_tanggal))}</span>
            <div class="rekomendasi-item-title">{html.escape(rek_judul)}</div>
        </div>
    </a>
"""

    html_output += """
</div>
</section>
"""
    return html_output

# ============================================================
# BUILD WEBSITE
# ============================================================

def build_site():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --------------------------------------------------------
    # BACA TEMPLATE
    # --------------------------------------------------------
    with open("template.html", "r", encoding="utf-8") as f:
        template_content = f.read()

    # --------------------------------------------------------
    # AMBIL DATA
    # --------------------------------------------------------
    berita_list = fetch_all_news()
    generated_items = []

    # --------------------------------------------------------
    # GENERATE SETIAP BERITA
    # --------------------------------------------------------
    for item in berita_list:
        nid = item.get("id")
        judul = item.get("judul")
        tanggal = item.get("tanggal", "")
        gambar = item.get("gambar")
        isi = item.get("isi", "")

        # Berita tanpa ID / judul dilewati.
        if not judul or not nid:
            continue

        slug = buat_slug(judul)
        potongan = dapatkan_potongan_teks(isi, 160)
        url_preview_artikel = f"{URL_PREVIEW}/berita/{slug}/"
        url_gambar_aman = gambar if gambar else "[https://i.ibb.co.com/G4NGrYXh/logo-baru-asrama.png](https://i.ibb.co.com/G4NGrYXh/logo-baru-asrama.png)"

        og_meta_tags = f"""
<meta property="og:type" content="article">
<meta property="og:url" content="{html.escape(url_preview_artikel, quote=True)}">
<meta property="og:title" content="{html.escape(judul, quote=True)}">
<meta property="og:description" content="{html.escape(potongan, quote=True)}">
<meta property="og:image" content="{html.escape(url_gambar_aman, quote=True)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(judul, quote=True)}">
<meta name="twitter:description" content="{html.escape(potongan, quote=True)}">
<meta name="twitter:image" content="{html.escape(url_gambar_aman, quote=True)}">
""".strip()

        rekomendasi_html = buat_rekomendasi_html(item, berita_list)

        html_rendered = template_content
        html_rendered = html_rendered.replace("{og_meta}", og_meta_tags)
        html_rendered = html_rendered.replace("{judul}", html.escape(judul))
        html_rendered = html_rendered.replace("{deskripsi}", html.escape(potongan))
        html_rendered = html_rendered.replace("{url_preview}", URL_PREVIEW)
        html_rendered = html_rendered.replace("{url_berita}", url_preview_artikel)
        html_rendered = html_rendered.replace("{url_gambar}", html.escape(url_gambar_aman, quote=True))
        html_rendered = html_rendered.replace("{tanggal}", html.escape(str(tanggal)))
        html_rendered = html_rendered.replace("{isi}", isi)
        html_rendered = html_rendered.replace("{rekomendasi}", rekomendasi_html)

        artikel_dir = os.path.join(OUTPUT_DIR, "berita", slug)
        os.makedirs(artikel_dir, exist_ok=True)

        artikel_file = os.path.join(artikel_dir, "index.html")
        with open(artikel_file, "w", encoding="utf-8") as f:
            f.write(html_rendered)

        print(f"[OK] Berita dibuat: {url_preview_artikel}")

        generated_items.append({
            "id": nid,
            "judul": judul,
            "slug": slug,
            "tanggal": tanggal,
            "potongan": potongan,
            "url_preview": url_preview_artikel
        })

    # --------------------------------------------------------
    # GENERATE FILE TAMBAHAN
    # --------------------------------------------------------
    generate_index_page(generated_items)
    generate_sitemap(generated_items)
    generate_rss(generated_items)
    generate_robots_txt()

    # --------------------------------------------------------
    # CNAME
    # --------------------------------------------------------
    with open(os.path.join(OUTPUT_DIR, "CNAME"), "w", encoding="utf-8") as f:
        f.write("news.myasrama.my.id")

    print("==============================")
    print("BUILD SELESAI")
    print(f"Total berita: {len(generated_items)}")
    print("==============================")

# ============================================================
# INDEX
# ============================================================

def generate_index_page(items):
    items_html = ""
    for item in items:
        items_html += f"""
    <article>
        <h2>
            <a href="{html.escape(item['url_preview'], quote=True)}">
                {html.escape(item['judul'])}
            </a>
        </h2>
        <p>{html.escape(str(item['tanggal']))}</p>
        <p>{html.escape(item['potongan'])}</p>
    </article>
    """

    index_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My Asrama News</title>
<meta name="description" content="Berita terbaru My Asrama">
<style>
    body {{
        font-family: Arial, sans-serif;
        max-width: 900px;
        margin: 40px auto;
        padding: 20px;
        background: #f4f6f9;
        color: #2d3748;
    }}
    article {{
        background: white;
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 10px;
    }}
    a {{
        color: #2563eb;
        text-decoration: none;
    }}
</style>
</head>
<body>
<h1>My Asrama News</h1>
{items_html}
</body>
</html>
"""

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_content)

# ============================================================
# SITEMAP
# ============================================================

def generate_sitemap(items):
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="[http://www.sitemaps.org/schemas/sitemap/0.9](http://www.sitemaps.org/schemas/sitemap/0.9)">
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
    <loc>{html.escape(item["url_preview"])}</loc>
    <lastmod>{now}</lastmod>
    <priority>0.8</priority>
</url>
"""

    xml += "</urlset>\n"

    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

# ============================================================
# RSS
# ============================================================

def generate_rss(items):
    now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>My Asrama News</title>
<link>[https://news.myasrama.my.id](https://news.myasrama.my.id)</link>
<description>Preview portal berita resmi My Asrama</description>
"""

    xml += f"<pubDate>{now}</pubDate>\n"

    for item in items:
        xml += f"""
<item>
    <title>{html.escape(item["judul"])}</title>
    <link>{html.escape(item["url_preview"])}</link>
    <description>{html.escape(item["potongan"])}</description>
    <guid>{html.escape(item["url_preview"])}</guid>
</item>
"""

    xml += "</channel>\n</rss>\n"

    with open(os.path.join(OUTPUT_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

# ============================================================
# ROBOTS
# ============================================================

def generate_robots_txt():
    content = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {URL_PREVIEW}/sitemap.xml\n"
    )

    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(content)

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    build_site()
