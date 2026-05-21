"""
Page: Master Data - Kelola daftar NTE types
"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.master_data import AREA_CONFIG, NTE_CATALOG, NTE_STATUS, ALL_NTE_TYPES

st.set_page_config(page_title="Master Data | NTE Dashboard", page_icon="🗂️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #37474F, #546E7A);
    color: white; padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem;
}
.page-header h2 { font-family: 'Space Grotesk', sans-serif; margin: 0; font-size: 1.5rem; }
.page-header p { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>🗂️ Master Data</h2>
    <p>Referensi data warehouse, area, dan katalog NTE</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🏭 Daftar Warehouse", "📦 Katalog NTE", "ℹ️ Info Sistem"])

with tab1:
    st.markdown("### Daftar Warehouse per Area")
    
    for area, config in AREA_CONFIG.items():
        whs = config["warehouses"]
        with st.expander(f"🏢 {area} — {len(whs)} Warehouse", expanded=True):
            cols = st.columns(3)
            for i, wh in enumerate(whs):
                cols[i % 3].markdown(f"**{i+1}.** {wh}")
    
    # Table view
    st.divider()
    st.markdown("#### Tabel Lengkap")
    rows = []
    for area, config in AREA_CONFIG.items():
        for i, wh in enumerate(config["warehouses"], 1):
            rows.append({"No": i, "Area": area, "Warehouse": wh})
    df_wh = pd.DataFrame(rows)
    st.dataframe(df_wh, use_container_width=True, hide_index=True)

with tab2:
    st.markdown("### Katalog NTE")
    st.caption(f"Total: **{len(ALL_NTE_TYPES)} type NTE** dalam **{len(NTE_CATALOG)} kategori**")
    
    for jenis, types in NTE_CATALOG.items():
        with st.expander(f"📁 {jenis} — {len(types)} type", expanded=False):
            for t in types:
                st.markdown(f"- `{t}`")
    
    st.divider()
    # Full table
    rows = []
    for jenis, types in NTE_CATALOG.items():
        for t in types:
            rows.append({"Jenis NTE": jenis, "Type NTE": t})
    df_nte = pd.DataFrame(rows)
    st.dataframe(df_nte, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### ℹ️ Informasi Sistem")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **NTE Stock Dashboard v1.0.0**
        
        Sistem pelaporan stok harian NTE (Network Terminal Environment) untuk:
        - Area **Telkom Bandung** (12 warehouse)
        - Area **Telkom Soreang** (5 warehouse)
        
        **Fitur:**
        - ✏️ Input stok manual per warehouse
        - 📤 Upload batch via Excel
        - ⚡ Rekap otomatis 1-klik per area
        - 📊 Grand total per type NTE lintas warehouse
        - 📉 Tren stok harian dengan grafik
        - ⬇️ Export ke Excel dengan format rapi
        """)
    with col2:
        st.markdown("""
        **Alur Penggunaan Harian:**
        
        1. Setiap PIC warehouse mengisi stok closing
        2. Input via form manual atau upload Excel
        3. Admin klik **Rekap Otomatis** setelah semua WH lapor
        4. Rekap otomatis generate pivot table per area
        5. Export Excel untuk arsip / distribusi
        
        **Format Tanggal:** YYYY-MM-DD
        
        **Status NTE:**
        - 🟢 **Baru** — perangkat baru belum pernah dipakai
        - 🟡 **Refurbish** — perangkat bekas yang sudah diperbaiki
        """)
    
    st.divider()
    st.markdown("**Kontak:** Tim IT Telkom Indonesia | NTE Operations")
