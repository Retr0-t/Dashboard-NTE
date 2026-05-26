# 🤖 NTE WhatsApp Bot
Bot WhatsApp untuk laporan stok harian NTE Telkom Indonesia.

---

## 📋 Prasyarat

- Node.js v18 atau lebih baru
- Google Chrome / Chromium (untuk whatsapp-web.js)
- Dashboard NTE sudah berjalan (`api_server.py`)

---

## 🚀 Instalasi

```bash
# 1. Masuk folder bot
cd nte_whatsapp_bot

# 2. Install dependencies
npm install

# 3. Buat file konfigurasi
cp .env.example .env

# 4. Edit .env sesuai kebutuhan
nano .env   # atau buka dengan text editor

# 5. Jalankan bot
node bot.js
```

---

## ⚙️ Konfigurasi (.env)

| Key | Keterangan |
|-----|-----------|
| `API_BASE_URL` | URL API dashboard NTE (default: http://localhost:8502) |
| `ALLOWED_NUMBERS` | Nomor WA yang boleh pakai bot (628xxx, pisahkan koma) |
| `REPORT_TARGET` | Tujuan laporan otomatis (nomor@c.us atau groupid@g.us) |
| `CRON_SCHEDULE` | Jadwal kirim otomatis (cron syntax) |
| `AUTO_REPORT_FORMAT` | Format laporan otomatis: `pdf` atau `jpg` |

---

## 📱 Cara Scan QR

1. Jalankan `node bot.js`
2. QR code muncul di terminal
3. Buka WhatsApp di HP → titik tiga → Perangkat Tertaut → Tautkan Perangkat
4. Scan QR code
5. Bot siap digunakan ✅

Session tersimpan otomatis di folder `.wwebjs_auth` — tidak perlu scan ulang kecuali logout.

---

## 💬 Daftar Perintah

### Laporan PDF / JPG

| Perintah | Keterangan |
|----------|-----------|
| `/laporan` | Semua laporan hari ini (ZIP PDF) |
| `/laporan semua jpg` | Semua laporan hari ini dalam JPG (dikirim satu per satu) |
| `/laporan telkomsel bandung` | 1 laporan PDF |
| `/laporan telkomsel bandung jpg` | 1 laporan JPG |
| `/laporan tsel bdg 2025-05-19` | Laporan tanggal tertentu |
| `/laporan telkom` | Semua area Telkom hari ini |

### Ringkasan Teks

| Perintah | Keterangan |
|----------|-----------|
| `/stok` | Ringkasan semua stok hari ini |
| `/stok telkomsel` | Ringkasan per operator |
| `/stok tif bandung` | Ringkasan per area |

### Informasi

| Perintah | Keterangan |
|----------|-----------|
| `/bantuan` | Daftar semua perintah |
| `/tanggal` | Daftar tanggal yang ada data |
| `/status` | Cek koneksi server |

---

## 🔄 Menjalankan Dashboard + Bot Bersamaan

Buka **2 terminal terpisah**:

**Terminal 1 — Dashboard Streamlit:**
```bash
cd nte_dashboard
streamlit run app.py --server.port 8501
```

**Terminal 2 — API Server:**
```bash
cd nte_dashboard
pip install fastapi uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8502
```

**Terminal 3 — WhatsApp Bot:**
```bash
cd nte_whatsapp_bot
node bot.js
```

---

## 🖥️ Menjalankan sebagai Service (Linux — agar berjalan terus)

```bash
# Install PM2
npm install -g pm2

# Jalankan bot dengan PM2
pm2 start bot.js --name nte-bot

# Auto-start saat server reboot
pm2 startup
pm2 save

# Lihat log
pm2 logs nte-bot
```

---

## 💡 Tips

- Gunakan nomor WA **khusus** untuk bot (bukan nomor pribadi)
- Jangan kirim terlalu banyak pesan sekaligus (risiko banned)
- Untuk produksi lebih aman gunakan **Fonnte** atau **WA Business API**

---

*NTE Operations · Telkom Indonesia*
