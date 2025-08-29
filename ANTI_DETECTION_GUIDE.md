# 🛡️ Anti-Detection Guide for Cafe Scraper

## Overview

Scraper ini dilengkapi dengan sistem anti-detection yang canggih untuk menghindari deteksi Google Maps dan memastikan scraping berjalan lancar tanpa terblokir.

## 🔧 Fitur Anti-Detection

### 1. **Rate Limiting yang Realistis**
- **Human-like delays**: 3-8 detik dengan variasi random ±50%
- **Break system**: Jeda 3-8 menit setiap 12-18 request
- **Occasional pauses**: 10% kemungkinan jeda ekstra 8-20 detik

### 2. **Rotating User Agents & Browser Settings**
- **10 User Agents**: Chrome, Firefox, Safari, Edge dari berbagai OS
- **Random screen resolution**: 8 resolusi berbeda (1920x1080, 1366x768, dll)
- **Dynamic viewport**: Posisi window random
- **Language variation**: en-US, en-GB dengan prioritas berbeda

### 3. **Advanced Browser Fingerprint Masking**
- **Stealth scripts**: Sembunyikan navigator.webdriver
- **Plugin simulation**: Fake plugin list
- **Chrome runtime**: Simulasi lingkungan Chrome normal
- **Permission handling**: Mock permission API

### 4. **Behavioral Randomization**
- **Mouse movements**: 2-4 gerakan random per aksi
- **Random scrolling**: 40% kemungkinan scroll dengan jarak random
- **Element hovering**: 30% kemungkinan hover pada elemen random
- **Human typing**: Ketik karakter per karakter dengan delay 0.05-0.15s

### 5. **Batch Processing dengan Jeda Panjang**
- **Batch size**: 5 queries per batch (configurable)
- **Long intervals**: 30 menit antar batch (configurable)
- **Session restart**: Driver restart setiap batch untuk fresh fingerprint
- **Random variation**: ±20% variasi pada interval

### 6. **Multi-Session Approach**
- **Session rotation**: Otomatis ganti session setiap 10 queries atau 1 jam
- **Fresh driver**: Driver baru untuk setiap session
- **Rotation delays**: 5-15 menit antar session
- **Session tracking**: Monitor queries per session

## 🚀 Cara Penggunaan

### Mode Standar (Recommended)
```bash
python3 cafe_scraper.py --full-scrape --max-cafes 500 --headless
```

### Stealth Mode (Batch Processing)
```bash
# Batch mode dengan jeda 30 menit
python3 cafe_scraper.py --full-scrape --max-cafes 1000 --stealth-mode --stealth-batch-size 5 --stealth-interval 1800 --headless

# Batch mode dengan jeda 1 jam
python3 cafe_scraper.py --full-scrape --max-cafes 2000 --stealth-mode --stealth-batch-size 3 --stealth-interval 3600 --headless
```

### Multi-Session Mode
```bash
# Multi-session dengan 10 queries per session
python3 cafe_scraper.py --full-scrape --max-cafes 1000 --multi-session --queries-per-session 10 --session-duration 3600 --headless

# Multi-session dengan session singkat
python3 cafe_scraper.py --full-scrape --max-cafes 500 --multi-session --queries-per-session 5 --session-duration 1800 --headless
```

### Ultra Stealth (Kombinasi)
```bash
# Gunakan batch mode untuk target besar
python3 cafe_scraper.py --full-scrape --max-cafes 5000 --stealth-mode --stealth-batch-size 3 --stealth-interval 2700 --headless
```

## ⚙️ Parameter Anti-Detection

### Rate Limiting
- `base_delay`: 5 detik (dapat disesuaikan)
- `break_frequency`: Setiap 12-18 requests
- `break_duration`: 3-8 menit

### Batch Processing
- `--stealth-mode`: Enable batch processing
- `--stealth-batch-size`: Queries per batch (default: 5)
- `--stealth-interval`: Detik antar batch (default: 1800 = 30 menit)

### Multi-Session
- `--multi-session`: Enable session rotation
- `--session-duration`: Max durasi session dalam detik (default: 3600 = 1 jam)
- `--queries-per-session`: Max queries per session (default: 10)

## 📊 Monitoring & Statistics

Scraper akan menampilkan informasi real-time:
- **Rate limiting**: Delay yang diterapkan
- **Session info**: Nomor session dan queries tersisa
- **Batch progress**: Progress batch saat ini
- **Break notifications**: Kapan break diambil dan durasi

## 🎯 Rekomendasi Berdasarkan Target

### Target Kecil (< 500 cafes)
```bash
python3 cafe_scraper.py --full-scrape --max-cafes 500 --headless
```

### Target Sedang (500-2000 cafes)
```bash
python3 cafe_scraper.py --full-scrape --max-cafes 1500 --multi-session --queries-per-session 8 --headless
```

### Target Besar (2000+ cafes)
```bash
python3 cafe_scraper.py --full-scrape --max-cafes 3000 --stealth-mode --stealth-batch-size 4 --stealth-interval 2400 --headless
```

### Ultra Safe Mode (Maximum Stealth)
```bash
python3 cafe_scraper.py --full-scrape --max-cafes 1000 --stealth-mode --stealth-batch-size 2 --stealth-interval 3600 --headless
```

## ⚠️ Tips & Best Practices

1. **Jangan terlalu agresif**: Gunakan target realistis (< 5000 cafes per run)
2. **Monitor logs**: Perhatikan warning dan error messages
3. **Gunakan headless**: Selalu gunakan `--headless` untuk production
4. **Variasi timing**: Jangan jalankan pada jam yang sama setiap hari
5. **Check results**: Periksa kualitas data secara berkala

## 🔍 Troubleshooting

### Jika Masih Terdeteksi:
1. **Increase intervals**: Perbesar `--stealth-interval`
2. **Reduce batch size**: Kecilkan `--stealth-batch-size`
3. **Use multi-session**: Coba mode multi-session
4. **Lower queries per session**: Kurangi `--queries-per-session`

### Error Handling:
- Scraper akan otomatis retry pada error
- Session akan direset jika terjadi masalah
- Progress tersimpan secara berkala

## 📈 Performance vs Stealth

| Mode | Speed | Stealth Level | Recommended For |
|------|-------|---------------|-----------------|
| Standard | ⚡⚡⚡ | 🛡️🛡️ | Testing, small targets |
| Multi-Session | ⚡⚡ | 🛡️🛡️🛡️ | Medium targets |
| Stealth Batch | ⚡ | 🛡️🛡️🛡️🛡️ | Large targets, production |

Pilih mode yang sesuai dengan kebutuhan Anda!
