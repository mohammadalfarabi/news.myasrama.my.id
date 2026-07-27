# My Asrama News - Preview Platform

Repositori ini berfungsi sebagai generator halaman statis perantara (*bridge preview*) dari domain utama untuk kebutuhan Open Graph Meta Tags media sosial (WhatsApp, Telegram, Facebook, dll.).

## Spesifikasi URL & Infrastruktur
* **Website Utama (Pembaca):** [myasrama.my.id](https://myasrama.my.id)
* **Domain Preview (GitHub Pages):** [news.myasrama.my.id](https://news.myasrama.my.id)
* **Target Build Folder:** `/docs` (Diatur pada setelan GitHub Pages repositori)

## Sistem Kerja Automated Workflow
1. GitHub Actions berjalan secara terjadwal setiap **5 menit**.
2. Skrip `generate.py` melakukan *crawling data* dari endpoint penyimpanan data JSON objek `https://myasrama.my.id/data/berita/`.
3. Generator melakukan normalisasi String judul menjadi *Clean URL friendly path slug*.
4. Halaman statis dibentuk dan dibekali Meta Tag Open Graph optimasi tinggi serta *scripted Meta HTTP-refresh auto-redirect* ke artikel asli dalam rentang waktu **2 detik**.
