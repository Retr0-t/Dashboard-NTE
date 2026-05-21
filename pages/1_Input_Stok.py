"""
Page: Input Stok Manual
"""

import streamlit as st
import sys, os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.database import init_db, upsert_stok, get_stok_by_date, delete_stok_by_date_wh
from data.master_data import AREA_CONFIG, WAREHOUSE_TO_AREA, NTE_STATUS, NTE_CATALOG, ALL_NTE_TYPES, NTE_TYPE_TO_JENIS

init_db()

st.set_page_config(page_title="Input Stok | NTE Dashboard", page_icon="✏️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #1E3A5F, #2E6DA4);
    color: white; padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem;
}
.page-header h2 { font-family: 'Space Grotesk', sans-serif; margin: 0; font-size: 1.5rem; }
.page-header p { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.9rem; }
.form-section {
    background: #F8FAFF; border: 1px solid #E0EAF5; border-radius: 12px;
    padding: 1.5rem; margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>✏️ Input Stok Manual</h2>
    <p>Input data stok harian per warehouse secara manual</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar filter ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan Input")
    selected_date = st.date_input("📅 Tanggal", value=date.today())
    
    all_wh = []
    for area, cfg in AREA_CONFIG.items():
        all_wh.extend(cfg["warehouses"])
    
    selected_area = st.selectbox("🏢 Area", list(AREA_CONFIG.keys()))
    selected_wh = st.selectbox("🏭 Warehouse", AREA_CONFIG[selected_area]["warehouses"])

# ── Input Form ─────────────────────────────────────────────────────────────────
st.markdown(f"### Input Stok: **{selected_wh}** — {selected_date.strftime('%d %B %Y')}")

# Tampilkan data yang sudah ada
existing = get_stok_by_date(str(selected_date))
existing_wh = existing[existing["warehouse"] == selected_wh] if not existing.empty else existing

if not existing_wh.empty:
    st.success(f"✅ Sudah ada **{len(existing_wh)} entri** untuk warehouse ini. Data baru akan menimpa yang lama.")
    with st.expander("Lihat data yang sudah ada"):
        st.dataframe(existing_wh[["jenis_nte","type_nte","status_nte","closing_stock"]], 
                     hide_index=True, use_container_width=True)

st.divider()

# Form input per NTE type
st.markdown("#### 📦 Isi Stok Closing per Type NTE")
st.caption("Hanya isi type NTE yang tersedia di warehouse ini. Kosongkan atau isi 0 jika tidak ada.")

inputs = {}

for jenis, types in NTE_CATALOG.items():
    with st.expander(f"📁 {jenis}", expanded=False):
        for status in NTE_STATUS:
            st.markdown(f"**Status: {status}**")
            cols = st.columns(2)
            for i, type_nte in enumerate(types):
                key = f"{type_nte}||{status}"
                
                # Prefill existing value
                default_val = 0
                if not existing_wh.empty:
                    match = existing_wh[
                        (existing_wh["type_nte"] == type_nte) &
                        (existing_wh["status_nte"] == status)
                    ]
                    if not match.empty:
                        default_val = int(match.iloc[0]["closing_stock"])
                
                with cols[i % 2]:
                    val = st.number_input(
                        type_nte.replace("_", " "),
                        min_value=0,
                        value=default_val,
                        key=key,
                        help=f"Closing stock {type_nte} ({status})"
                    )
                    inputs[key] = val

st.divider()

# Submit
col_save, col_clear = st.columns([3, 1])
with col_save:
    if st.button("💾 Simpan Data Stok", type="primary", use_container_width=True):
        saved = 0
        for key, val in inputs.items():
            if val > 0:  # Hanya simpan yang > 0
                type_nte, status_nte = key.split("||")
                jenis_nte = NTE_TYPE_TO_JENIS.get(type_nte, "Lainnya")
                upsert_stok(
                    tanggal=str(selected_date),
                    area=selected_area,
                    warehouse=selected_wh,
                    jenis_nte=jenis_nte,
                    type_nte=type_nte,
                    status_nte=status_nte,
                    closing_stock=val
                )
                saved += 1
        
        if saved > 0:
            st.success(f"✅ Berhasil menyimpan **{saved} entri** stok untuk {selected_wh}!")
            st.balloons()
            st.rerun()
        else:
            st.warning("⚠️ Tidak ada data yang disimpan. Pastikan ada nilai stok > 0.")

with col_clear:
    if st.button("🗑️ Hapus Data WH Ini", type="secondary", use_container_width=True):
        if not existing_wh.empty:
            delete_stok_by_date_wh(str(selected_date), selected_wh)
            st.warning(f"Data stok {selected_wh} untuk {selected_date} telah dihapus.")
            st.rerun()
        else:
            st.info("Tidak ada data untuk dihapus.")

# Preview
if inputs:
    non_zero = {k: v for k, v in inputs.items() if v > 0}
    if non_zero:
        st.markdown("#### 👁️ Preview Data yang Akan Disimpan")
        preview_rows = []
        for key, val in non_zero.items():
            type_nte, status = key.split("||")
            preview_rows.append({
                "Jenis NTE": NTE_TYPE_TO_JENIS.get(type_nte, "-"),
                "Type NTE": type_nte,
                "Status": status,
                "Closing Stock": val
            })
        st.dataframe(pd.DataFrame(preview_rows), hide_index=True, use_container_width=True)

import pandas as pd
