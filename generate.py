import os
import re
import html
import json
import urllib.request
from datetime import datetime

URL_UTAMA = "https://myasrama.my.id"
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
        if raw_payload.startswith('"') and raw_payload.endswith('"'):
            try:
                raw_payload = json.loads(raw_payload)
            except:
                raw_payload = raw_payload[1:-1].replace('\\"', '"').replace('\\\\', '\\')

        news_data = json.loads(raw_payload)
        if isinstance(news_data, str):
            news_data = json.loads(news_data)
            
        if isinstance(news_data, list):
            print(f"Berhasil memuat {len(news_data)} data berita dari payload.")
            return news_data
    except Exception as e:
        print(f"Gagal memparsing payload: {e}")
    return all_news

def download_gambar_bypass(nama_file, folder_tujuan):
    """Mendownload gambar dari InfinityFree dengan bypass User-Agent agar tidak diblokir"""
    url_sumber = f"{URL_UTAMA}/upload/berita/{nama_file}"
    path_lokal = os.path.join(folder_tujuan, nama_file)
    
    # Fake header menyerupai browser Google Chrome asli
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
    }
    
    try:
        req = urllib.request.Request(url_sumber, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response, open(path_lokal, 'wb') as out_file:
            out_file.write(response.read())
        print(f"✓ Berhasil mendownload & menyimpan gambar: {nama_file}")
        return f"{URL_PREVIEW}/images/{nama_file}"
    except Exception as e:
        print(f"✗ Gagal mendownload {nama_file} lewat Python, menggunakan fallback URL utama. Error: {e}")
        return url_sumber

def build_site():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    folder_gambar = os.path.join(OUTPUT_DIR, "images")
    os.makedirs(folder_gambar, exist_ok=True)
    
    with open("template.html", "r", encoding="utf-8") as f:
        template_content = f.read()
        
    berita_list = fetch_all_news()
    generated_items = []

    for item in berita_list:
        nid = item.get("id")
        judul = item.get("judul")
        tanggal = item.get("tanggal")
        gambar = item.get("gambar")
        isi = item.get("isi", "")
        
        if not judul or not nid:
            continue
            
        slug = buat_slug(judul)
        potongan = dapatkan_potongan_teks(isi, 160)
        
        url_tujuan = f"{URL_UTAMA}/berita/detail.php?id={nid}"
        url_preview_artikel = f"{URL_PREVIEW}/berita/{slug}/"
        
        # PROSES DOWNLOAD GAMBAR LANGSUNG BYPASS ANTI-BOT
        url_gambar_aman = f"{URL_UTAMA}/upload/berita/{gambar}" # Default fallback
        if gambar:
            url_gambar_aman = download_gambar_bypass(gambar, folder_gambar)
        
        og_meta_tags = f"""
    <meta property="og:type" content="article">
    <meta property="og:url" content="{url_preview_artikel}">
    <meta property="og:title" content="{html.escape(judul)}">
    <meta property="og:description" content="{html.escape(potongan)}">
    <meta property="og:image" content="{url_gambar_aman}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{html.escape(judul)}">
    <meta name="twitter:description" content="{html.escape(potongan)}">
    <meta name="twitter:image" content="{url_gambar_aman}">
        """.strip()
        
        html_rendered = template_content
        html_rendered = html_rendered.replace("{og_meta}", og_meta_tags)
        html_rendered = html_rendered.replace("{judul}", html.escape(judul))
        html_rendered = html_rendered.replace("{deskripsi}", html.escape(potongan))
        html_rendered = html_rendered.replace("{url_preview}", url_preview_artikel)
        html_rendered = html_rendered.replace("{url_gambar}", url_gambar_aman)
        html_rendered = html_rendered.replace("{url_tujuan}", url_tujuan)
        html_rendered = html_rendered.replace("{tanggal}", tanggal)
        html_rendered = html_rendered.replace("{potongan_isi}", html.escape(dapatkan_potongan_teks(isi, 250)))
        
        artikel_dir = os.path.join(OUTPUT_DIR, "berita", slug)
        os.makedirs(artikel_dir, exist_ok=True)
        
        with open(os.path.join(artikel_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_rendered)
            
        generated_items.append({
            "judul": judul,
            "slug": slug,
            "tanggal": tanggal,
            "potongan": potongan,
            "url_preview": url_preview_artikel,
            "url_tujuan": url_tujuan
        })

    generate_index_page(generated_items)
    generate_sitemap(generated_items)
    generate_rss(generated_items)
    generate_robots_txt()

    with open(os.path.join(OUTPUT_DIR, "CNAME"), "w", encoding="utf-8") as f:
        f.write("news.myasrama.my.id")

def generate_index_page(items):
    items_html = ""
    for item in items:
        items_html += f'<li><a href="{item["url_preview"]}">{item["judul"]}</a> ({item["tanggal"]})</li>\n'
    index_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Asrama News - Preview Center</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #1e3a8a; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>My Asrama News</h1>
    <p>Direktori preview berita untuk sosial media Asrama UTM.</p>
    <hr>
    <h3>Berita Terbaru:</h3>
    <ul>
        {items_html if items_html else '<li>Belum ada berita terbaru saat ini.</li>'}
    </ul>
</body>
</html>"""
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_content)

def generate_sitemap(items):
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url>\n    <loc>{URL_PREVIEW}/</loc>\n    <lastmod>{now}</lastmod>\n    <priority>1.0</priority>\n  </url>\n'
    for item in items:
        xml += f'  <url>\n    <loc>{item["url_preview"]}</loc>\n    <lastmod>{now}</lastmod>\n    <priority>0.8</priority>\n  </url>\n'
    xml += '</urlset>'
    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

def generate_rss(items):
    now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    xml = f'<?xml version="1.0" encoding="UTF-8" ?>\n<rss version="2.0">\n<channel>\n'
    xml += f'  <title>My Asrama News</title>\n  <link>{URL_PREVIEW}</link>\n  <description>Preview portal berita resmi My Asrama</description>\n  <pubDate>{now}</pubDate>\n'
    for item in items:
        xml += f'  <item>\n    <title>{html.escape(item["judul"])}</title>\n    <link>{item["url_preview"]}</link>\n    <description>{html.escape(item["potongan"])}</description>\n    <guid>{item["url_preview"]}</guid>\n  </item>\n'
    xml += '</channel>\n</rss>'
    with open(os.path.join(OUTPUT_DIR, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(xml)

def generate_robots_txt():
    content = f"User-agent: *\nAllow: /\n\nSitemap: {URL_PREVIEW}/sitemap.xml\n"
    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    build_site()
