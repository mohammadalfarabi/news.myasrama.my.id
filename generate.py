import os
import re
import html
import json
import random
from datetime import datetime

# ============================================================
# KONFIGURASI
# ============================================================

URL_UTAMA = "https://myasrama.my.id"
URL_PREVIEW = "https://news.myasrama.my.id"

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

def buat_rekomendasi_html(item, berita_list, max_rekomendasi=3):
    rekomendasi = item.get("rekomendasi", [])
    selected_news = []

    # Ambil ID berita yang sedang dibuka
    current_id = str(item.get("id"))

    # Kumpulkan semua berita lain (selain berita yang sedang dibuka)
    other_news = [
        news for news in berita_list 
        if str(news.get("id")) != current_id and news.get("judul")
    ]

    if not other_news:
        return ""

    # 1. Cari berita berdasarkan ID di array "rekomendasi"
    if isinstance(rekomendasi, list) and len(rekomendasi) > 0:
        berita_by_id = {str(news.get("id")): news for news in other_news}
        for id_rek in rekomendasi:
            rek = berita_by_id.get(str(id_rek))
            if rek:
                selected_news.append(rek)

    # 2. Jika rekomendasi kurang dari max_rekomendasi (misal < 3), isi dengan berita lain secara acak
    if len(selected_news) < max_rekomendasi:
        sisa_kuota = max_rekomendasi - len(selected_news)
        
        # Hindari berita yang sudah terpilih sebelumnya
        existing_ids = {str(n.get("id")) for n in selected_news}
        available_news = [n for n in other_news if str(n.get("id")) not in existing_ids]
        
        # Ambil acak sisa berita yang tersedia
        if available_news:
            fallback_news = random.sample(available_news, min(sisa_kuota, len(available_news)))
            selected_news.extend(fallback_news)

    if not selected_news:
        return ""

    # 3. Render Komponen HTML
    html_output = """
<section class="rekomendasi-section">
<h3 class="rekomendasi-title">Rekomendasi Berita Lainnya</h3>
<div class="rekomendasi-grid">
"""

    for rek in selected_news:
        rek_judul = rek.get("judul", "")
        rek_tanggal = rek.get("tanggal", "")
        rek_gambar = rek.get("gambar")
        rek_slug = buat_slug(rek_judul)
        
        # Menggunakan link relatif aman
        rek_url = f"/berita/{rek_slug}/"
        rek_img = rek_gambar if rek_gambar else "https://i.ibb.co.com/G4NGrYXh/logo-baru-asrama.png"

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

    with open("template.html", "r", encoding="utf-8") as f:
        template_content = f.read()

    berita_list = fetch_all_news()
    generated_items = []

    for item in berita_list:
        nid = item.get("id")
        judul = item.get("judul")
        tanggal = item.get("tanggal", "")
        gambar = item.get("gambar")
        isi = item.get("isi", "")

        if not judul or not nid:
            continue

        slug = buat_slug(judul)
        potongan = dapatkan_potongan_teks(isi, 160)
        
        # Relative path untuk tautan internal
        relative_url = f"/berita/{slug}/"
        # Absolute URL khusus untuk Meta Tags / Open Graph
        url_preview_artikel = f"{URL_PREVIEW}/berita/{slug}/"
        
        url_gambar_aman = gambar if gambar else "https://i.ibb.co.com/G4NGrYXh/logo-baru-asrama.png"

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
            "relative_url": relative_url,
            "url_preview": url_preview_artikel
        })

    generate_index_page(generated_items)
    generate_sitemap(generated_items)
    generate_rss(generated_items)
    generate_robots_txt()

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
        # Menggunakan relative_url (/berita/slug/) untuk tautan di index.html
        items_html += f"""
    <article class="news-card">
        <h2>
            <a href="{html.escape(item['relative_url'], quote=True)}">
                {html.escape(item['judul'])}
            </a>
        </h2>
        <p class="date">{html.escape(str(item['tanggal']))}</p>
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            background: #f8fafc;
            color: #1e293b;
        }}
        h1 {{
            font-size: 2rem;
            color: #0f172a;
            margin-bottom: 24px;
        }}
        .news-card {{
            background: white;
            padding: 24px;
            margin-bottom: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }}
        .news-card h2 {{
            margin: 0 0 8px 0;
            font-size: 1.25rem;
        }}
        .news-card h2 a {{
            color: #2563eb;
            text-decoration: none;
        }}
        .news-card h2 a:hover {{
            text-decoration: underline;
        }}
        .date {{
            color: #64748b;
            font-size: 0.85rem;
            margin-bottom: 12px;
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
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
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
<link>https://news.myasrama.my.id</link>
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
