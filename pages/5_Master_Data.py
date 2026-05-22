"""Page: Master Data"""
import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.master_data import AREA_CONFIG, NTE_CATALOG, NTE_STATUS, ALL_NTE_TYPES, ALL_OPERATORS, ALL_AREAS

st.set_page_config(page_title="Master Data | NTE Dashboard", page_icon="🗂️", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.page-header{background:linear-gradient(135deg,#37474F,#546E7A);color:white;
  padding:1.5rem 2rem;border-radius:12px;margin-bottom:1.5rem}
.page-header h2{font-family:'Space Grotesk',sans-serif;margin:0;font-size:1.5rem}
.page-header p{margin:.25rem 0 0;opacity:.8;font-size:.9rem}
.op-badge{display:inline-block;padding:3px 12px;border-radius:20px;font-size:.78rem;font-weight:600;margin:2px}
</style>
""", unsafe_allow_html=True)

OP_STYLE = {
    "TELKOMSEL": "background:#E8F5E9;color:#1B5E20",
    "TELKOM":    "background:#E3F2FD;color:#0D47A1",
    "TIF":       "background:#FFF3E0;color:#E65100",
}

st.markdown("""
<div class="page-header">
    <h2>🗂️ Master Data</h2>
    <p>Referensi operator, area, warehouse, dan katalog NTE</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🏭 Warehouse", "📦 Katalog NTE", "ℹ️ Info"])

with tab1:
    st.markdown("### Daftar Warehouse per Operator & Area")

    total_wh = sum(len(v["warehouses"]) for v in AREA_CONFIG.values())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Kombinasi", len(AREA_CONFIG))
    c2.metric("Total WH Entry", total_wh)
    c3.metric("Operator", len(ALL_OPERATORS))
    c4.metric("Area", len(ALL_AREAS))

    st.divider()

    for op in ALL_OPERATORS:
        style = OP_STYLE.get(op,"")
        st.markdown(
            f'<span class="op-badge" style="{style}">{op}</span>',
            unsafe_allow_html=True
        )
        cols = st.columns(2)
        for ai, area in enumerate(ALL_AREAS):
            ak = f"{op} - {area}"
            if ak not in AREA_CONFIG: continue
            whs = AREA_CONFIG[ak]["warehouses"]
            with cols[ai]:
                with st.expander(f"📍 {area} — {len(whs)} WH", expanded=True):
                    for i, wh in enumerate(whs, 1):
                        st.caption(f"{i}. {wh}")
        st.divider()

    # Tabel flat
    rows = []
    for ak, cfg in AREA_CONFIG.items():
        for wh in cfg["warehouses"]:
            rows.append({"Operator":cfg["operator"],"Area":cfg["area"],
                         "Area Key":ak,"Warehouse":wh})
    st.markdown("#### Tabel Lengkap")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

with tab2:
    st.markdown(f"### Katalog NTE — {len(ALL_NTE_TYPES)} type dalam {len(NTE_CATALOG)} kategori")
    for jenis, types in NTE_CATALOG.items():
        with st.expander(f"📁 {jenis} — {len(types)} type"):
            for t in types: st.caption(f"• {t}")
    st.divider()
    rows2 = [{"Jenis NTE":j,"Type NTE":t}
             for j,ts in NTE_CATALOG.items() for t in ts]
    st.dataframe(pd.DataFrame(rows2), hide_index=True, use_container_width=True)

with tab3:
    st.markdown("### ℹ️ Informasi Sistem")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **NTE Stock Dashboard v2.0.0**

        Sistem pelaporan stok NTE untuk:

        | Operator | Bandung | Soreang |
        |----------|---------|---------|
        | TELKOMSEL | 12 WH | 5 WH |
        | TELKOM | 12 WH | 5 WH |
        | TIF | 4 WH | 3 WH |
        | **Total** | **28** | **13** |

        **Total entry WH: 41**
        """)
    with c2:
        st.markdown("""
        **Cara Edit Nama Warehouse**

        Edit file `data/master_data.py` bagian `AREA_CONFIG`.
        Tidak perlu ubah file lain.

        **Status NTE:**
        - 🟢 **NTE BARU** — perangkat baru
        - 🟡 **REFURBISH** — bekas, sudah diperbaiki

        **Format key area:** `OPERATOR - AREA`
        Contoh: `TIF - SOREANG`
        """)
