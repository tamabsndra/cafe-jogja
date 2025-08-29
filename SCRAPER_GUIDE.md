# 🎯 Ultimate Cafe Scraper Guide

## Satu File Scraper untuk Semua Kebutuhan!

**File utama:** `cafe_scraper.py`

---

## ✨ Features Lengkap

### 🎯 **Koordinat Presisi**
- ✅ Extract koordinat real dari Google Maps URL
- ✅ Multiple extraction methods (URL → data-attrs → onclick → aria-label)
- ✅ Precision score tracking (0.0-1.0)
- ✅ Smart fallback estimation

### 📊 **Data Lengkap**
- ✅ Nama, alamat, rating, reviews, price range
- ✅ Koordinat presisi (lat/lon dengan 6-7 decimal)
- ✅ Geocoding otomatis (regency, district, village)
- ✅ Klasifikasi tipe cafe (Traditional, Modern, Coffee Shop, Roastery)
- ✅ Jam buka, phone, website (jika tersedia)

### 🛡️ **Anti-Detection**
- ✅ Smart rate limiting dengan random delays
- ✅ Auto-scroll untuk load semua hasil
- ✅ User agent rotation
- ✅ Progress tracking dan resume capability

### 💾 **Multiple Output Formats**
- ✅ JSON dengan metadata lengkap
- ✅ CSV untuk analisis spreadsheet
- ✅ Precision statistics dan quality metrics

---

## 🚀 Cara Menggunakan

### **1. Quick Test (Rekomendasi untuk mulai)**
```bash
python3 cafe_scraper.py --quick-test
```
- Test dengan 5 cafe di area Malioboro
- Hasil: `data/cafes_test_results_TIMESTAMP.json`

### **2. Full Scraping**
```bash
python3 cafe_scraper.py --full-scrape --max-cafes 1000
```
- Scraping lengkap dengan semua strategi
- Target: 1000 cafe (bisa disesuaikan)
- Hasil: `data/cafes_final_TIMESTAMP.json`

### **3. Area Specific**
```bash
python3 cafe_scraper.py --area malioboro --max-cafes 50
python3 cafe_scraper.py --area sleman --max-cafes 100
python3 cafe_scraper.py --area bantul --max-cafes 75
```

### **4. Custom Query**
```bash
python3 cafe_scraper.py --query "coffee shop ugm" --max-cafes 30
python3 cafe_scraper.py --query "traditional warung kopi jogja" --max-cafes 50
```

### **5. Headless Mode (untuk server)**
```bash
python3 cafe_scraper.py --full-scrape --headless --max-cafes 500
```

---

## 📊 Contoh Output

### **JSON Structure:**
```json
{
  "metadata": {
    "total_cafes": 5,
    "scraper_version": "ultimate_v1.0",
    "precision_stats": {
      "avg_precision": 0.900,
      "high_precision_count": 5,
      "coordinate_sources": {
        "extract_from_url": 5
      }
    }
  },
  "cafes": [
    {
      "name": "Loko Cafe - Malioboro",
      "lat": -7.7897901,
      "lon": 110.3657681,
      "coordinate_source": "extract_from_url",
      "precision_score": 0.90,
      "rating": 4.5,
      "reviews_count": 7602,
      "price_range": "Rp 25–50 rb",
      "regency": "Yogyakarta",
      "type": "Modern"
    }
  ]
}
```

### **Precision Levels:**
- **0.90-1.00:** Extract dari Google Maps URL (SANGAT AKURAT)
- **0.80-0.89:** Extract dari data attributes (AKURAT)
- **0.70-0.79:** Extract dari onclick events (CUKUP AKURAT)
- **0.60-0.69:** Extract dari aria-label (SEDANG)
- **0.30-0.59:** Smart estimation (FALLBACK)

---

## 🎯 Search Strategies

Scraper menggunakan 20+ strategi pencarian:

### **Base Queries:**
- "cafe yogyakarta", "coffee shop yogyakarta"
- "cafe sleman", "coffee sleman"
- "cafe bantul", "coffee bantul"
- "cafe malioboro", "coffee malioboro"

### **Area Specific:**
- "cafe dekat malioboro", "coffee shop tugu"
- "cafe sekitar ugm", "coffee shop condongcatur"
- "warung kopi sleman", "cafe bantul selatan"

### **Type Specific:**
- "traditional coffee yogyakarta"
- "roastery yogyakarta"
- "specialty coffee yogyakarta"

---

## 📁 File Output

Semua hasil disimpan di folder `data/` dengan format:
- `cafes_test_results_TIMESTAMP.json/csv` - untuk quick test
- `cafes_final_TIMESTAMP.json/csv` - untuk full scrape
- `cafes_custom_TIMESTAMP.json/csv` - untuk custom query

---

## ⚡ Performance Tips

### **Untuk Hasil Terbaik:**
1. **Mulai dengan quick test** untuk verifikasi
2. **Gunakan area filter** untuk target spesifik
3. **Set max-cafes realistis** (50-500 per session)
4. **Monitor logs** untuk track progress

### **Troubleshooting:**
- Jika stuck: Stop (Ctrl+C) → otomatis save progress
- Jika koordinat tidak akurat: Check precision_score
- Jika terlalu lambat: Kurangi max-cafes atau gunakan --headless

---

## 🎉 Hasil Test Terbukti

```
✅ Test completed: 5 cafes extracted
🎯 5 cafes, avg precision: 0.900
📍 All coordinates from extract_from_url (highest precision)
📊 Success rate: 100%
```

**Sekarang tinggal satu file scraper yang powerful untuk semua kebutuhan! 🚀**
