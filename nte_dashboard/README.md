# 📦 NTE Stock Dashboard
**Sistem Pelaporan Stok Harian Network Terminal Environment**  
Telkom Indonesia — Area Bandung & Soreang

---

## 🚀 Cara Instalasi & Menjalankan

### 1. Prasyarat
- Python 3.9 atau lebih baru
- pip

### 2. Install Dependencies
```bash
cd nte_dashboard
pip install -r requirements.txt
```

### 3. Jalankan Dashboard
```bash
streamlit run app.py
```
Dashboard akan terbuka otomatis di browser: `http://localhost:8501`

---

## 📁 Struktur File

```
nte_dashboard/
├── app.py                  # Home page (overview & KPI)
├── requirements.txt
├── data/
│   ├── master_data.py      # Konfigurasi area, WH, katalog NTE
│   └── nte_stok.db         # Database SQLite (auto-generated)
├── utils/
│   ├── database.py         # CRUD & query functions
│   └── export_utils.py     # Generator Excel
└── pages/
    ├── 1_Input_Stok.py     # Input manual per warehouse
    ├── 2_Upload_Excel.py   # Upload batch dari Excel
    ├── 3_Rekap_Otomatis.py # ⚡ 1-klik rekap per area
    ├── 4_Tren_Stok.py      # Grafik tren stok harian
    └── 5_Master_Data.py    # Referensi data & info
```

---

## 📋 Cara Pakai Harian

### Alur Normal:
1. **PIC Warehouse** → buka menu **Input Stok** atau upload Excel
2. Isi closing stock per type NTE dan status (Baru/Refurbish)
3. **Admin/Koordinator** → buka **Rekap Otomatis**
4. Pilih tanggal → klik **GENERATE REKAP SEKARANG**
5. Dashboard otomatis:
   - Menampilkan pivot table per area
   - Menghitung grand total per type NTE lintas warehouse
   - Tombol export Excel per area

### Upload Excel Batch:
1. Download template dari menu **Upload Excel**
2. Isi data (bisa untuk banyak WH sekaligus)
3. Upload → simpan ke database

---

## 🏢 Konfigurasi Area

| Area | Jumlah WH |
|------|-----------|
| TELKOM BANDUNG | 12 warehouse |
| TELKOM SOREANG | 5 warehouse |
| **Total** | **17 warehouse** |

---

## 🔧 Kustomisasi

### Tambah Warehouse Baru
Edit `data/master_data.py` → bagian `AREA_CONFIG`

### Tambah Type NTE Baru  
Edit `data/master_data.py` → bagian `NTE_CATALOG`

### Ubah Nama Warehouse yang Sudah Ada
Edit `data/master_data.py` dan pastikan nama di database lama juga disesuaikan

---

## 📊 Format Rekap Otomatis (Output Excel)

Setiap file Excel rekap berisi:
- **Sheet 'Rekap [Area]'**: Pivot table dengan kolom per warehouse + grand total per type NTE
- **Sheet 'Data Detail'**: Raw data untuk keperluan audit

Contoh grand total:
```
Type NTE               | WH Banjaran | WH Kadipaten | WH Majalaya | WH Majalengka | WH Sumedang | GRAND TOTAL
AP_Cisco_C9105AXI-F   |      2      |      3       |     10      |      30       |      1      |     46
```

---

## 🗄️ Database

Menggunakan **SQLite** — tidak perlu instalasi server database.  
File `data/nte_stok.db` ter-generate otomatis saat pertama kali dijalankan.

Untuk backup: cukup copy file `nte_stok.db`

---

*Dibuat untuk menggantikan sistem pelaporan Google Sheets*  
*v1.0.0 | NTE Operations*
