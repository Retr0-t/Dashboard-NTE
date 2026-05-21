"""
Page: Upload Excel
"""

import streamlit as st
import pandas as pd
import sys, os
from datetime import date
import io

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.database import init_db, bulk_upsert_stok
from utils.export_utils import build_excel_template
from data.master_data import AREA_CONFIG, ALL_WAREHOUSES, NTE_STATUS, ALL_NTE_TYPES, NTE_TYPE_TO_JENIS, WAREHOUSE_TO_AREA

init_db()

st.set_page_config(page_title="Upload Excel | NTE Dashboard", page_icon="📤", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #1B5E20, #2E7D32);
    color: white; padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem;
}
.page-header h2 { font-family: 'Space Grotesk', sans-serif; margin: 0; font-size: 1.5rem; }
.page-header p { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.9rem; }
.info-box {
    background: #E8F5E9; border-left: 4px solid #2E7D32; border-radius: 8px;
    padding: 1rem 1.25rem; margin-bottom: 1rem;
}
.error-box {
    background: #FFEBEE; border-left: 4px solid #C62828; border-radius: 8px;
    padding: 1rem; margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>📤 Upload Data Excel</h2>
    <p>Upload file Excel berisi data stok harian untuk satu atau banyak warehouse sekaligus</p>
</div>
""", unsafe_allow_html=True)

# ── Download Template ─────────────────────────────────────────────────────────
st.markdown("### 📋 Langkah 1: Download Template")
st.markdown("""
<div class="info-box">
    <b>Format file Excel yang diterima:</b><br>
    Kolom wajib: <code>tanggal</code>, <code>area</code>, <code>warehouse</code>, 
    <code>jenis_nte</code>, <code>type_nte</code>, <code>status_nte</code>, <code>closing_stock</code><br>
    Format tanggal: <code>YYYY-MM-DD</code> (contoh: 2025-01-15)
</div>
""", unsafe_allow_html=True)

col_dl, col_info = st.columns([1, 2])
with col_dl:
    template_bytes = build_excel_template(ALL_WAREHOUSES)
    st.download_button(
        label="⬇️ Download Template Excel",
        data=template_bytes,
        file_name=f"template_input_stok_NTE.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary"
    )
with col_info:
    st.markdown("""
    Template berisi:
    - **Sheet 'Template Input Stok'**: Form pengisian dengan contoh data
    - **Sheet 'Referensi'**: Daftar lengkap nama area, warehouse, jenis & type NTE yang valid
    """)

st.divider()

# ── Upload File ────────────────────────────────────────────────────────────────
st.markdown("### 📂 Langkah 2: Upload File Excel")

uploaded_file = st.file_uploader(
    "Pilih file Excel (.xlsx)",
    type=["xlsx", "xls"],
    help="File bisa berisi data untuk banyak tanggal / banyak warehouse sekaligus"
)

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0)
        
        st.success(f"✅ File berhasil dibaca: **{len(df_raw)} baris** data")
        
        # Validate columns
        required_cols = {"tanggal", "area", "warehouse", "jenis_nte", "type_nte", "status_nte", "closing_stock"}
        missing_cols = required_cols - set(df_raw.columns.str.lower().tolist())
        
        if missing_cols:
            st.error(f"❌ Kolom berikut tidak ditemukan: **{', '.join(missing_cols)}**")
            st.stop()
        
        # Normalize columns
        df_raw.columns = df_raw.columns.str.lower().str.strip()
        df_clean = df_raw[list(required_cols)].copy()
        df_clean["closing_stock"] = pd.to_numeric(df_clean["closing_stock"], errors="coerce").fillna(0).astype(int)
        df_clean["tanggal"] = pd.to_datetime(df_clean["tanggal"]).dt.strftime("%Y-%m-%d")
        
        # Preview
        st.markdown("#### 👁️ Preview Data (10 baris pertama)")
        st.dataframe(df_clean.head(10), use_container_width=True, hide_index=True)
        
        # Stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Baris", len(df_clean))
        col2.metric("Jumlah Tanggal", df_clean["tanggal"].nunique())
        col3.metric("Jumlah Warehouse", df_clean["warehouse"].nunique())
        
        # Validation warnings
        unknown_wh = set(df_clean["warehouse"].unique()) - set(ALL_WAREHOUSES)
        unknown_nte = set(df_clean["type_nte"].unique()) - set()  # flexible
        unknown_status = set(df_clean["status_nte"].unique()) - set(NTE_STATUS)
        
        if unknown_wh:
            st.warning(f"⚠️ Nama warehouse tidak dikenal: **{', '.join(unknown_wh)}**. Pastikan sesuai dengan daftar referensi.")
        if unknown_status:
            st.warning(f"⚠️ Status NTE tidak dikenal: **{', '.join(unknown_status)}**. Gunakan: Baru / Refurbish.")
        
        st.divider()
        st.markdown("### 💾 Langkah 3: Simpan ke Database")
        
        if st.button("⬆️ Upload & Simpan Semua Data", type="primary", use_container_width=True):
            with st.spinner("Menyimpan data ke database..."):
                success, errors = bulk_upsert_stok(df_clean)
            
            if errors:
                st.error(f"❌ {len(errors)} baris gagal disimpan:")
                for e in errors[:10]:
                    st.markdown(f'<div class="error-box">{e}</div>', unsafe_allow_html=True)
            
            if success > 0:
                st.success(f"✅ **{success} baris** berhasil disimpan ke database!")
                st.balloons()
                
                # Summary
                st.markdown("#### 📊 Ringkasan Upload")
                summary = df_clean.groupby(["tanggal", "area", "warehouse"])["closing_stock"].sum().reset_index()
                summary.columns = ["Tanggal", "Area", "Warehouse", "Total Stok (Unit)"]
                st.dataframe(summary, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"❌ Gagal membaca file: {str(e)}")
        st.exception(e)

else:
    st.markdown("""
    <div style="text-align:center; padding: 3rem; color: #9E9E9E; border: 2px dashed #BDBDBD; border-radius: 12px;">
        <div style="font-size: 3rem;">📊</div>
        <div style="font-size: 1rem; margin-top: 0.5rem;">Drag & drop file Excel di sini atau klik untuk memilih</div>
        <div style="font-size: 0.8rem; margin-top: 0.25rem;">Format: .xlsx | Bisa berisi data banyak warehouse sekaligus</div>
    </div>
    """, unsafe_allow_html=True)
