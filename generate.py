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
    Mengambil daftar ID berita secara otomatis dengan memanggil file index.php secara langsung.
    """
    all_news = []
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        # Menembak ke file index.php agar server tidak memblokir aksesnya
        response = requests.get(API_NEWS_URL, headers=headers, timeout=15)
        
        print(f"Status Cek Server: {response.status_code}")
        
        if response.status_code == 200:
            try:
                raw_ids = response.json() 
            except Exception as json_err:
                print(f"Gagal memparsing JSON dari index.php: {json_err}. Isi response: {response.text[:200]}")
                return all_news

            if not isinstance(raw_ids, list):
                print(f"Format dari index.php tidak sesuai list, tipe: {type(raw_ids)}")
                return all_news
                
            # Pastikan semua ID diubah jadi string bersih dan tidak duplikat
            news_ids = list(set([str(nid).strip() for nid in raw_ids if nid]))
            print(f"Sistem mendeteksi {len(news_ids)} ID berita secara otomatis: {news_ids}")
            
            for nid in news_ids:
                clean_id = nid.replace('.json', '')
                target_url = f"{DATA_NEWS_URL}{clean_id}.json"
                
                try:
                    res = requests.get(target_url, headers=headers, timeout=5)
                    print(f"Mengunduh {target_url} -> Status: {res.status_code}")
                    if res.status_code == 200:
                        all_news.append(res.json())
                except Exception as e:
                    print(f"Gagal mengunduh berita ID {clean_id}: {e}")
            
            return all_news
    except Exception as e:
        print(f"Gagal melakukan scanning folder berita otomatis: {e}")

    return all_news
