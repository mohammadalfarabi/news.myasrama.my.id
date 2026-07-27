import os
import re
import html
import json
import requests
from datetime import datetime

# Konfigurasi
URL_UTAMA = "https://myasrama.my.id"
URL_PREVIEW = "https://news.myasrama.my.id"
DATA_NEWS_URL = f"{URL_UTAMA}/data/berita/"
IMAGE_BASE_URL = f"{URL_UTAMA}/upload/berita/"
OUTPUT_DIR = "docs"

def buat_slug(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text

def dapatkan_potongan_teks(text, length=160):
    clean_text = re.sub(r'<[^>]+>', '', text)  # Hapus tag HTML jika ada
    clean_text = html.unescape(clean_text).replace('\n', ' ').strip()
    if len(clean_text) <= length:
        return clean_text
    return clean_text[:length].rsplit(' ', 1)[0] + '...'

def fetch_all_news():
    """
    Mengambil data dari endpoint utama. 
    Catatan: Karena berupa folder file JSON, disarankan memiliki satu file manifest index.json 
    atau memparsing daftar filenya. Kode ini mengasumsikan daftar ID didapatkan secara dinamis.
    """
    all_news = []
    
    try:
        # Asumsi pertama: mencoba mengambil manifest index list berita jika tersedia
        response = requests.get(f"{DATA_NEWS_URL}index.json", timeout=10)
        if response.status_code == 200:
            news_ids = response.json() # Ekspektasi berupa array ID: [1785069910, ...]
            for nid in news_ids:
                res = requests.get(f"{DATA_NEWS_URL}{nid}.json", timeout=5)
                if res.status_code == 200:
                    all_news.append(res.json())
            return all_news
    except Exception:
        pass

    # Fallback/Alternatif jika tidak ada index.json: 
    # Anda bisa menaruh daftar ID statis atau mem-parsing HTML directory listing jika diizinkan server
    # Di bawah ini adalah contoh hardcoded ID untuk validasi workflow internal developer
    sample_ids = [1785069910] 
    for nid in sample_ids:
        try:
            res = requests.get(f"{DATA_NEWS_URL}{nid}.json", timeout=5)
            if res.status_code == 200:
                all_news.append(res.json())
        except Exception as e:
            print(f"Gagal mengambil berita ID {nid}: {e}")
            
    return all_news

def build_site():
    # Buat direktori output utama jika belum ada
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load Template
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
        
        slug = buat_slug(judul)
        potongan = dapatkan_potongan_teks(isi, 160)
        
        url_tujuan = f"{URL_UTAMA}/berita/detail.php?id={nid}"
        url_preview_artikel = f"{URL_PREVIEW}/berita/{slug}/"
        url_gambar_full = f"{IMAGE_BASE_URL}{gambar}"
        
        # Inject data ke template
        html_rendered = template_content.format(
            judul=html.escape(judul),
            deskripsi=html.escape(potongan),
            url_preview=url_preview_artikel,
            url_gambar=url_gambar_full,
            url_tujuan=url_tujuan,
            tanggal=tanggal,
            potongan_isi=html.escape(dapatkan_potongan_teks(isi, 250))
        )
        
        # Simpan dalam struktur path berita/slug/index.html agar URL clean
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
        print(f"Generated: /berita/{slug}/")

    # 1. Buat halaman utama index.html (Daftar Berita Terbaru Preview)
    generate_index_page(generated_items)
    
    # 2. Buat sitemap.xml
    generate_sitemap(generated_items)
    
    # 3. Buat rss.xml
    generate_rss(generated_items)
    
    # 4. Buat robots.txt
    generate_robots_txt()

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
        ul {{ padding-left: 20px; }}
        li {{ margin-bottom: 10px; }}
        a {{ color: #2563eb; text-decoration: none; }}
        a:hover {{ text-underline-offset: 3px; text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>My Asrama News</h1>
    <p>Direktori preview tautan sosial media untuk My Asrama. Anda akan dialihkan secara otomatis ke platform utama saat membuka berita.</p>
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
