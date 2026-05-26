"""
NTE Stock Dashboard — Home / Overview
Operator: Telkomsel · Telkom · TIF  |  Area: Bandung · Soreang
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from utils.database import init_db, get_available_dates, get_wh_coverage, get_stok, get_grand_total
from data.master_data import AREA_CONFIG, ALL_OPERATORS, ALL_AREAS

st.set_page_config(
    page_title="NTE Stock Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.main-header{background:linear-gradient(135deg,#1E3A5F,#2E6DA4 60%,#3498DB);
  padding:1.75rem 2.5rem;border-radius:16px;color:white;margin-bottom:1.5rem;
  box-shadow:0 8px 32px rgba(30,58,95,.3)}
.main-header h1{font-family:'Space Grotesk',sans-serif;font-size:1.9rem;font-weight:700;margin:0}
.main-header p{font-size:.9rem;opacity:.85;margin:.3rem 0 0}
.op-badge{display:inline-block;padding:3px 12px;border-radius:20px;font-size:.75rem;font-weight:600;margin:2px}
.op-telkomsel{background:#E8F5E9;color:#1B5E20}
.op-telkom{background:#E3F2FD;color:#0D47A1}
.op-tif{background:#FFF3E0;color:#E65100}
.section-title{font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:600;
  color:#1E3A5F;border-bottom:2px solid #2E6DA4;padding-bottom:.4rem;margin:1.2rem 0 .8rem}
[data-testid="metric-container"]{background:white;border:1px solid #E8EEF4;
  border-radius:12px;padding:1rem;box-shadow:0 2px 8px rgba(0,0,0,.05)}
</style>
""", unsafe_allow_html=True)

# ── Operator color map ────────────────────────────────────────────────────────
OP_COLOR = {
    "TELKOMSEL": ("#1B5E20", "#E8F5E9"),
    "TELKOM":    ("#0D47A1", "#E3F2FD"),
    "TIF":       ("#E65100", "#FFF3E0"),
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📦 NTE Dashboard")
    st.caption("Telkomsel · Telkom · TIF")
    st.divider()

    available_dates = get_available_dates()
    if available_dates:
        selected_date = st.selectbox("📅 Tanggal", available_dates)
    else:
        selected_date = str(date.today())
        st.info("Belum ada data.")

    st.divider()
    # Filter operator
    filter_op = st.multiselect(
        "🏢 Filter Operator",
        ALL_OPERATORS,
        default=ALL_OPERATORS,
        help="Pilih operator yang ingin ditampilkan"
    )
    filter_area = st.radio("📍 Filter Area", ["Semua"] + ALL_AREAS, index=0)

    st.divider()
    st.caption(f"🕐 {datetime.now().strftime('%d %b %Y, %H:%M')}")
    st.caption("v2.0.0 | NTE Stock System")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📦 NTE Stock Dashboard</h1>
    <p>Pelaporan Stok Harian Network Terminal Environment</p>
    <div style="margin-top:.6rem">
        <span class="op-badge op-telkomsel">TELKOMSEL</span>
        <span class="op-badge op-telkom">TELKOM</span>
        <span class="op-badge op-tif">TIF</span>
        <span style="opacity:.7;font-size:.8rem;margin-left:.5rem">Bandung &amp; Soreang</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Data load ─────────────────────────────────────────────────────────────────
df_coverage = get_wh_coverage(selected_date) if selected_date else pd.DataFrame()
df_all      = get_stok(selected_date) if selected_date else pd.DataFrame()

# Apply sidebar filters
if not df_all.empty and filter_op:
    df_all = df_all[df_all["operator"].isin(filter_op)]
if not df_all.empty and filter_area != "Semua":
    df_all = df_all[df_all["area"] == filter_area]

# ── KPI row ───────────────────────────────────────────────────────────────────
total_wh_all = sum(len(v["warehouses"]) for v in AREA_CONFIG.values())
reported_set  = set(
    zip(df_coverage["operator"], df_coverage["warehouse"])
) if not df_coverage.empty else set()

total_stok    = int(df_all["closing_stock"].sum()) if not df_all.empty else 0
total_types   = df_all["type_nte"].nunique() if not df_all.empty else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📦 Total Stok",    f"{total_stok:,}",   f"{total_types} type NTE")
col2.metric("📍 WH Aktif",
            f"{len(reported_set)}/{total_wh_all}",
            "sudah lapor hari ini")

# Per operator KPI
for i, op in enumerate(ALL_OPERATORS):
    op_keys = [k for k,v in AREA_CONFIG.items() if v["operator"] == op]
    total_op_wh = sum(len(AREA_CONFIG[k]["warehouses"]) for k in op_keys)
    reported_op = sum(
        1 for (o, w) in reported_set
        if o == op
    ) if reported_set else 0
    [col3, col4, col5][i].metric(
        f"{'🟢' if reported_op==total_op_wh else '🟡'} {op}",
        f"{reported_op}/{total_op_wh} WH",
        "✅ Lengkap" if reported_op == total_op_wh else f"{total_op_wh-reported_op} belum"
    )

st.divider()

# ── Coverage per operator per area ────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Status Pelaporan Warehouse</div>', unsafe_allow_html=True)

for op in ALL_OPERATORS:
    txt_color, bg_color = OP_COLOR[op]
    with st.expander(f"🏢 {op}", expanded=True):
        cols_area = st.columns(2)
        for ai, area in enumerate(ALL_AREAS):
            area_key = f"{op} - {area}"
            if area_key not in AREA_CONFIG:
                continue
            whs = AREA_CONFIG[area_key]["warehouses"]
            rep = [w for w in whs if (op, w) in reported_set]
            miss = [w for w in whs if w not in rep]

            with cols_area[ai]:
                st.markdown(
                    f"**{area}** — {len(rep)}/{len(whs)} WH"
                    f" {'✅' if len(rep)==len(whs) else '⚠️'}"
                )
                for w in whs:
                    icon = "✅" if w in rep else "❌"
                    st.caption(f"{icon} {w}")

st.divider()

# ── Ringkasan stok per operator ───────────────────────────────────────────────
if not df_all.empty:
    st.markdown('<div class="section-title">📈 Ringkasan Stok per Operator & Area</div>',
                unsafe_allow_html=True)

    for op in filter_op:
        df_op = df_all[df_all["operator"] == op]
        if df_op.empty:
            continue
        txt_color, bg_color = OP_COLOR[op]
        st.markdown(
            f'<span style="background:{bg_color};color:{txt_color};padding:3px 12px;'
            f'border-radius:20px;font-weight:700;font-size:.9rem">{op}</span>',
            unsafe_allow_html=True
        )
        c1, c2 = st.columns([3, 1])
        with c1:
            summary = (
                df_op.groupby(["area","jenis_nte","status_nte"])["closing_stock"]
                .sum().reset_index()
                .rename(columns={"area":"Area","jenis_nte":"Jenis NTE",
                                 "status_nte":"Status","closing_stock":"Total Stok"})
                .sort_values("Total Stok", ascending=False)
            )
            st.dataframe(summary, hide_index=True, use_container_width=True,
                         column_config={"Total Stok": st.column_config.NumberColumn(format="%d unit")})
        with c2:
            st.metric("Total Unit", f"{int(df_op['closing_stock'].sum()):,}")
            st.metric("Type NTE",   df_op["type_nte"].nunique())
            st.metric("WH Lapor",   df_op["warehouse"].nunique())
        st.divider()
else:
    st.info(f"📭 Belum ada data untuk **{selected_date}**. Silakan input via menu **Input Stok** atau **Upload Excel**.")

# ── Quick links ───────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
c1.page_link("pages/1_Input_Stok.py",    label="✏️ Input Stok Manual",  use_container_width=True)
c2.page_link("pages/2_Upload_Excel.py",  label="📤 Upload Excel",        use_container_width=True)
c3.page_link("pages/3_Rekap_Otomatis.py",label="⚡ Rekap Otomatis",      use_container_width=True)
c4.page_link("pages/4_Tren_Stok.py",     label="📉 Tren Stok",           use_container_width=True)
