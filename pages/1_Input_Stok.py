"""Page: Input Stok Manual — filter operator → area → warehouse"""

import streamlit as st
import pandas as pd
import sys, os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.database import init_db, upsert_stok, get_stok, delete_stok
from data.master_data import (AREA_CONFIG, ALL_OPERATORS, NTE_STATUS,
                               NTE_CATALOG, NTE_TYPE_TO_JENIS)
init_db()

st.set_page_config(page_title="Input Stok | NTE Dashboard", page_icon="✏️", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.page-header{background:linear-gradient(135deg,#1E3A5F,#2E6DA4);color:white;
  padding:1.5rem 2rem;border-radius:12px;margin-bottom:1.5rem}
.page-header h2{font-family:'Space Grotesk',sans-serif;margin:0;font-size:1.5rem}
.page-header p{margin:.25rem 0 0;opacity:.8;font-size:.9rem}
.s-baru{background:#D5F5E3;color:#1E8449;padding:2px 10px;border-radius:20px;font-size:.78rem;font-weight:600}
.s-refurbish{background:#FFF3CD;color:#856404;padding:2px 10px;border-radius:20px;font-size:.78rem;font-weight:600}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>✏️ Input Stok Manual</h2>
    <p>Input data closing stock harian per operator → area → warehouse</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar filter: operator → area_key → warehouse ───────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Pilih Warehouse")
    selected_date = st.date_input("📅 Tanggal", value=date.today())

    selected_op = st.selectbox("🏢 Operator", ALL_OPERATORS)

    # area keys milik operator ini
    op_area_keys = [k for k, v in AREA_CONFIG.items() if v["operator"] == selected_op]
    selected_area_key = st.selectbox("📍 Area", op_area_keys)

    whs = AREA_CONFIG[selected_area_key]["warehouses"]
    selected_wh = st.selectbox("🏭 Warehouse", whs)

cfg = AREA_CONFIG[selected_area_key]

st.markdown(
    f"### Input: **{selected_wh}**  "
    f"<small style='color:#666'>— {selected_op} | {cfg['area']} | {selected_date.strftime('%d %b %Y')}</small>",
    unsafe_allow_html=True
)

# Data existing
existing = get_stok(str(selected_date), operator=selected_op)
existing_wh = (
    existing[existing["warehouse"] == selected_wh]
    if not existing.empty else pd.DataFrame()
)

if not existing_wh.empty:
    st.success(f"✅ **{len(existing_wh)} entri** sudah tersimpan — data baru akan menimpa.")
    with st.expander("Lihat data tersimpan"):
        st.dataframe(
            existing_wh[["jenis_nte","type_nte","status_nte","closing_stock"]],
            hide_index=True, use_container_width=True
        )

st.divider()
st.markdown("#### 📦 Isi Closing Stock")
st.caption("Isi angka stok akhir. Biarkan 0 jika tidak ada.")

inputs = {}

for jenis, types in NTE_CATALOG.items():
    with st.expander(f"📁 **{jenis}** ({len(types)} type)", expanded=False):
        for type_nte in types:
            cols = st.columns([3, 2, 2])
            cols[0].markdown(
                f"<small style='color:#555'>{type_nte.replace('_',' ')}</small>",
                unsafe_allow_html=True
            )
            for si, status in enumerate(NTE_STATUS):
                key = f"{type_nte}||{status}"
                default = 0
                if not existing_wh.empty:
                    m = existing_wh[
                        (existing_wh["type_nte"] == type_nte) &
                        (existing_wh["status_nte"] == status)
                    ]
                    if not m.empty:
                        default = int(m.iloc[0]["closing_stock"])

                badge_cls = "s-baru" if status == "NTE BARU" else "s-refurbish"
                cols[si+1].markdown(
                    f'<span class="{badge_cls}">{status}</span>',
                    unsafe_allow_html=True
                )
                inputs[key] = cols[si+1].number_input(
                    label=f"{type_nte} {status}",
                    label_visibility="collapsed",
                    min_value=0, value=default, key=key
                )

st.divider()

# Preview
non_zero = {k: v for k, v in inputs.items() if v > 0}
if non_zero:
    st.markdown("#### 👁️ Preview (hanya yang > 0)")
    rows = []
    for key, val in non_zero.items():
        t, s = key.split("||")
        rows.append({"Jenis": NTE_TYPE_TO_JENIS.get(t,"-"), "Type": t, "Status": s, "Stok": val})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

c1, c2 = st.columns([4,1])
with c1:
    if st.button("💾 Simpan Data Stok", type="primary", use_container_width=True):
        saved = 0
        for key, val in inputs.items():
            if val > 0:
                type_nte, status_nte = key.split("||")
                upsert_stok(
                    tanggal      = str(selected_date),
                    operator     = selected_op,
                    area         = cfg["area"],
                    area_key     = selected_area_key,
                    warehouse    = selected_wh,
                    jenis_nte    = NTE_TYPE_TO_JENIS.get(type_nte,"Lainnya"),
                    type_nte     = type_nte,
                    status_nte   = status_nte,
                    closing_stock= val
                )
                saved += 1
        if saved:
            st.success(f"✅ **{saved} entri** disimpan untuk {selected_op} | {selected_wh}!")
            st.balloons(); st.rerun()
        else:
            st.warning("⚠️ Tidak ada data > 0 untuk disimpan.")

with c2:
    if st.button("🗑️ Hapus WH Ini", use_container_width=True):
        if not existing_wh.empty:
            delete_stok(str(selected_date), selected_op, selected_wh)
            st.warning("Data dihapus."); st.rerun()
        else:
            st.info("Tidak ada data.")
