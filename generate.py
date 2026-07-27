import os
import re
import html
import json
import requests
from datetime import datetime

# Konfigurasi Alamat URL
URL_UTAMA = "https://myasrama.my.id"
URL_PREVIEW = "https://news.myasrama.my.id"
DATA_NEWS_URL = f"{URL_UTAMA}/data/berita/"
API_NEWS_URL = f"{URL_UTAMA}/data/berita/index.php"
IMAGE_BASE_URL = f"{URL_UTAMA}/upload/berita/"
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
    """
    Mengambil data berita dengan menyertakan User-Agent khusus (untuk Cloudflare)
    dan Token Rahasia khusus (untuk verifikasi index.php) disertai log pelacak.
    """
    all_news = []
    SECRET_TOKEN = os.environ.get("ASRAMA_NEWS_TOKEN", "")
    
    print("-> [LOG] Memulai fungsi fetch_all_news()...")
    print(f"-> [LOG] Menembak URL: {API_NEWS_URL}")
    
    try:
        headers = {
            'User-Agent': 'AsramaBot-GitHub-Actions', 
            'X-MyAsrama-Token': SECRET_TOKEN,
            'Accept': 'application/json'
        }
        
        print("-> [LOG] Mengirim request ke server... (Menunggu respon Cloudflare/Hosting)")
        response = requests.get(API_NEWS_URL, headers=headers, timeout=15)
        
        print(f"-> [LOG] Status Cek Server Berhasil Diterima: {response.status_code}")
        
        if response.status_code == 200:
            try:
                raw_ids = response.json() 
            except Exception as json_err:
                print(f"-> [ERROR] Gagal memparsing JSON dari index.php: {json_err}.")
                print(f"-> [ERROR] Isi response awal: {response.text[:500]}")
                return all_news

            if not isinstance(raw_ids, list):
                print(f"-> [WARNING] Format dari index.php tidak sesuai list, tipe: {type(raw_ids)}")
                return all_news
                
            news_ids = list(set([str(nid).strip() for nid in raw_ids if nid]))
            print(f"-> [SUCCESS] Sistem mendeteksi {len(news_ids)} ID berita secara otomatis: {news_ids}")
            
            for nid in news_ids:
                clean_id = nid.replace('.json', '')
                target_url = f"{DATA_NEWS_URL}{clean_id}.json"
                
                try:
                    res = requests.get(target_url, headers=headers, timeout=5)
                    if res.status_code == 200:
                        all_news.append(res.json())
                except Exception as e:
                    print(f"-> [ERROR] Gagal mengunduh berita ID {clean_id}: {e}")
            
            return all_news
        else:
            print(f"-> [BUNTU] Gagal menembus server. Kode Status: {response.status_code}")
            print(f"-> [BUNTU] Isi potongan halaman penolakan: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("-> [FATAL ERROR] Koneksi TIMEOUT! Server menggantung atau tidak merespon bot dalam 15 detik.")
    except Exception as e:
        print(f"-> [FATAL ERROR] Terjadi kendala komunikasi: {e}")

    return all_news

def build_site():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
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
        url_gambar_full = f"{IMAGE_BASE_URL}{gambar}"
        
        html_rendered = template_content.format(
            judul=html.escape(judul),
            deskripsi=html.escape(potongan),
            url_preview=url_preview_artikel,
            url_gambar=url_gambar_full,
            url_tujuan=url_tujuan,
            tanggal=tanggal,
            potongan_isi=html.escape(dapatkan_potongan_teks(isi, 250))
        )
        
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
