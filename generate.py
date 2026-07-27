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
# --- UBAH DI SINI: Tembak langsung file index.php agar melewati blokir folder ---
API_NEWS_URL = f"{URL_UTAMA}/data/berita/index.php"
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
    Mengambil data berita dengan menyertakan User-Agent khusus (untuk Cloudflare)
    dan Token Rahasia khusus (untuk verifikasi index.php) disertai log pelacak.
    """
    all_news = []
    
    # Mengambil token rahasia dari environment GitHub Actions
    SECRET_TOKEN = os.environ.get("ASRAMA_NEWS_TOKEN", "")
    
    print("-> [LOG] Memulai fungsi fetch_all_news()...")
    print(f"-> [LOG] Menembak URL: {API_NEWS_URL}")
    
    try:
        # Mengirimkan User-Agent (Cloudflare) DAN Token Header (PHP) sekaligus
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
        print(f"Error komunikasi: {e}")

    return all_news
