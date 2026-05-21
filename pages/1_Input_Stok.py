"""
Page: Input Stok Manual
"""

import streamlit as st
import pandas as pd
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
.page-header p  { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.9rem; }
.status-baru     { background:#D5F5E3; color:#1E8449; padding:2px 10px; border-radius:20px; font-size:.8rem; font-weight:600; }
.status-refurbish{ background:#FFF3CD; color:#856404; padding:2px 10px; border-radius:20px; font-size:.8rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>✏️ Input Stok Manual</h2>
    <p>Input data closing stock harian per warehouse</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Pilih Warehouse")
    selected_date  = st.date_input("📅 Tanggal", value=date.today())
    selected_area  = st.selectbox("🏢 Area", list(AREA_CONFIG.keys()))
    selected_wh    = st.selectbox("🏭 Warehouse", AREA_CONFIG[selected_area]["warehouses"])

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f"### 📦 Stok: **{selected_wh}**")
st.caption(f"Tanggal: {selected_date.strftime('%d %B %Y')} | Area: {selected_area}")

# Data existing
existing     = get_stok_by_date(str(selected_date))
existing_wh  = existing[existing["warehouse"] == selected_wh] if not existing.empty else pd.DataFrame()

if not existing_wh.empty:
    st.success(f"✅ Sudah ada **{len(existing_wh)} entri** tersimpan. Data baru akan menimpa.")
    with st.expander("Lihat data tersimpan"):
        st.dataframe(
            existing_wh[["jenis_nte","type_nte","status_nte","closing_stock"]],
            hide_index=True, use_container_width=True
        )

st.divider()

# ── Form per Jenis → per Type → per Status ────────────────────────────────────
st.markdown("#### Isi Closing Stock")
st.caption("Isi angka stok akhir (closing). Biarkan 0 jika tidak ada.")

inputs = {}   # key = "type||status" : value = int

for jenis, types in NTE_CATALOG.items():
    with st.expander(f"📁 **{jenis}** — {len(types)} type", expanded=False):
        for type_nte in types:
            cols = st.columns([3, 2, 2])
            cols[0].markdown(f"<small style='color:#555'>{type_nte.replace('_',' ')}</small>", unsafe_allow_html=True)

            for si, status in enumerate(NTE_STATUS):
                key = f"{type_nte}||{status}"
                # prefill dari data existing
                default = 0
                if not existing_wh.empty:
                    m = existing_wh[
                        (existing_wh["type_nte"]   == type_nte) &
                        (existing_wh["status_nte"] == status)
                    ]
                    if not m.empty:
                        default = int(m.iloc[0]["closing_stock"])

                label_html = (
                    '<span class="status-baru">NTE BARU</span>'
                    if status == "NTE BARU"
                    else '<span class="status-refurbish">REFURBISH</span>'
                )
                cols[si + 1].markdown(label_html, unsafe_allow_html=True)
                val = cols[si + 1].number_input(
                    label=f"{type_nte} {status}",
                    label_visibility="collapsed",
                    min_value=0, value=default,
                    key=key
                )
                inputs[key] = val

st.divider()

# ── Preview ────────────────────────────────────────────────────────────────────
non_zero = {k: v for k, v in inputs.items() if v > 0}
if non_zero:
    st.markdown("#### 👁️ Preview (hanya yang > 0)")
    rows = []
    for key, val in non_zero.items():
        t, s = key.split("||")
        rows.append({"Jenis NTE": NTE_TYPE_TO_JENIS.get(t,"-"), "Type NTE": t, "Status": s, "Closing Stock": val})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ── Actions ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([4, 1])
with c1:
    if st.button("💾 Simpan Data Stok", type="primary", use_container_width=True):
        saved = 0
        for key, val in inputs.items():
            if val > 0:
                type_nte, status_nte = key.split("||")
                upsert_stok(
                    tanggal      = str(selected_date),
                    area         = selected_area,
                    warehouse    = selected_wh,
                    jenis_nte    = NTE_TYPE_TO_JENIS.get(type_nte, "Lainnya"),
                    type_nte     = type_nte,
                    status_nte   = status_nte,
                    closing_stock= val
                )
                saved += 1
        if saved:
            st.success(f"✅ **{saved} entri** berhasil disimpan untuk {selected_wh}!")
            st.balloons()
            st.rerun()
        else:
            st.warning("⚠️ Tidak ada data > 0 untuk disimpan.")

with c2:
    if st.button("🗑️ Hapus WH Ini", use_container_width=True):
        if not existing_wh.empty:
            delete_stok_by_date_wh(str(selected_date), selected_wh)
            st.warning("Data dihapus.")
            st.rerun()
        else:
            st.info("Tidak ada data.")
