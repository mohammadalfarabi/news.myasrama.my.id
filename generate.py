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
    Mengambil data berita dengan menyamar menggunakan User-Agent khusus
    yang telah diberi izin lolos bypass di WAF Cloudflare.
    """
    all_news = []
    
    try:
        # PENTING: User-Agent ini harus sama persis dengan 'Value' di Cloudflare
        headers = {
            'User-Agent': 'AsramaBot-GitHub-Actions',
            'Accept': 'application/json'
        }
        
        # Eksekusi langsung ke berkas index.php
        response = requests.get(API_NEWS_URL, headers=headers, timeout=15)
        print(f"Status Cek Server (Cloudflare Bypass): {response.status_code}")
        
        if response.status_code == 200:
            try:
                raw_ids = response.json() 
            except Exception as json_err:
                print(f"Gagal parsing JSON. Isi response: {response.text[:200]}")
                return all_news

            if not isinstance(raw_ids, list):
                return all_news
                
            news_ids = list(set([str(nid).strip() for nid in raw_ids if nid]))
            print(f"Sukses! Terdeteksi {len(news_ids)} ID berita: {news_ids}")
            
            for nid in news_ids:
                clean_id = nid.replace('.json', '')
                target_url = f"{DATA_NEWS_URL}{clean_id}.json"
                
                try:
                    res = requests.get(target_url, headers=headers, timeout=5)
                    if res.status_code == 200:
                        all_news.append(res.json())
                except Exception as e:
                    print(f"Gagal mengambil detail ID {clean_id}: {e}")
            
            return all_news
        else:
            print(f"Cloudflare masih menghadang. Kode Status: {response.status_code}")
            
    except Exception as e:
        print(f"Error pada koneksi: {e}")

    return all_news
