"""
NTE Stock Dashboard - Main App
Telkom Ases Indonesia | Bandung & Soreang Area
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from utils.database import init_db, get_available_dates, get_wh_coverage, get_stok_by_date, get_rekap_grand_total
from data.master_data import AREA_CONFIG, ALL_WAREHOUSES, WAREHOUSE_TO_AREA

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NTE Stock Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init DB ──────────────────────────────────────────────────────────────────
init_db()

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main-header {
    background: linear-gradient(135deg, #1E3A5F 0%, #2E6DA4 60%, #3498DB 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(30, 58, 95, 0.3);
}

.main-header h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
}

.main-header p {
    font-size: 0.95rem;
    opacity: 0.85;
    margin: 0.3rem 0 0;
}

.kpi-card {
    background: white;
    border: 1px solid #E8EEF4;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}

.kpi-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #1E3A5F;
    line-height: 1;
}

.kpi-label {
    font-size: 0.8rem;
    color: #7F8C8D;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 0.3rem;
}

.kpi-sub {
    font-size: 0.85rem;
    color: #27AE60;
    margin-top: 0.4rem;
    font-weight: 500;
}

.area-card {
    background: linear-gradient(135deg, #F0F7FF 0%, #E8F4FD 100%);
    border: 1px solid #BDE0FF;
    border-left: 4px solid #2E6DA4;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
}

.area-card h4 {
    color: #1E3A5F;
    font-weight: 700;
    margin: 0 0 0.5rem;
    font-size: 0.95rem;
}

.wh-badge {
    display: inline-block;
    background: #2E6DA4;
    color: white;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 20px;
    margin: 2px;
    font-weight: 500;
}

.wh-badge.reported {
    background: #27AE60;
}

.wh-badge.missing {
    background: #E74C3C;
}

.status-badge {
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.status-badge.ok { background: #D5F5E3; color: #1E8449; }
.status-badge.warn { background: #FDEBD0; color: #D35400; }
.status-badge.err { background: #FADBD8; color: #C0392B; }

.section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #1E3A5F;
    border-bottom: 2px solid #2E6DA4;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem;
}

/* Sidebar */
.css-1d391kg, [data-testid="stSidebar"] {
    background: #1E3A5F !important;
}
[data-testid="stSidebar"] * {
    color: white !important;
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s;
}

/* Metrics */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #E8EEF4;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📦 NTE Dashboard")
    st.markdown("**Telkom Akses Indonesia**")
    st.markdown("Area Bandung & Soreang")
    st.divider()
    
    available_dates = get_available_dates()
    if available_dates:
        selected_date = st.selectbox(
            "📅 Tanggal Laporan",
            options=available_dates,
            index=0
        )
    else:
        selected_date = str(date.today())
        st.info("Belum ada data. Silakan input via menu Input Stok.")
    
    st.divider()
    st.markdown(f"**🕐 Update Terakhir**")
    st.caption(datetime.now().strftime("%d %b %Y, %H:%M"))
    
    st.divider()
    st.caption("v1.0.0 | NTE Stock System")

# ── Main Header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>📦 NTE Stock Dashboard</h1>
    <p>Sistem Pelaporan Stok Harian Network Terminal Environment · Telkom Indonesia</p>
</div>
""", unsafe_allow_html=True)

# ── KPI Overview ──────────────────────────────────────────────────────────────
df_all = get_stok_by_date(selected_date) if selected_date else pd.DataFrame()
df_coverage = get_wh_coverage(selected_date) if selected_date else pd.DataFrame()

total_wh = len(ALL_WAREHOUSES)
reported_wh = len(df_coverage) if not df_coverage.empty else 0
missing_wh = total_wh - reported_wh
total_stok = int(df_all["closing_stock"].sum()) if not df_all.empty else 0
total_nte_types = df_all["type_nte"].nunique() if not df_all.empty else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📍 Total Warehouse", f"{reported_wh}/{total_wh}", 
              f"+{reported_wh} sudah lapor" if reported_wh > 0 else "Belum ada laporan")
with col2:
    st.metric("📦 Total Stok (Unit)", f"{total_stok:,}", 
              f"{total_nte_types} jenis NTE" if total_nte_types > 0 else "-")
with col3:
    bandung_wh = len(AREA_CONFIG["TELKOM BANDUNG"]["warehouses"])
    reported_bdg = len(df_coverage[df_coverage["area"] == "TELKOM BANDUNG"]) if not df_coverage.empty else 0
    st.metric("🏙️ Bandung", f"{reported_bdg}/{bandung_wh} WH",
              "✅ Lengkap" if reported_bdg == bandung_wh else f"⚠️ {bandung_wh - reported_bdg} belum lapor")
with col4:
    soreang_wh = len(AREA_CONFIG["TELKOM SOREANG"]["warehouses"])
    reported_srg = len(df_coverage[df_coverage["area"] == "TELKOM SOREANG"]) if not df_coverage.empty else 0
    st.metric("🌄 Soreang", f"{reported_srg}/{soreang_wh} WH",
              "✅ Lengkap" if reported_srg == soreang_wh else f"⚠️ {soreang_wh - reported_srg} belum lapor")

st.divider()

# ── Coverage Status per Area ───────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Status Pelaporan Warehouse</div>', unsafe_allow_html=True)

reported_whs = set(df_coverage["warehouse"].tolist()) if not df_coverage.empty else set()

for area, config in AREA_CONFIG.items():
    whs = config["warehouses"]
    rep_count = sum(1 for w in whs if w in reported_whs)
    
    with st.expander(f"{'🟢' if rep_count == len(whs) else '🟡' if rep_count > 0 else '🔴'} {area} — {rep_count}/{len(whs)} warehouse telah lapor", expanded=True):
        cols = st.columns(4)
        for i, wh in enumerate(whs):
            status = "reported" if wh in reported_whs else "missing"
            icon = "✅" if wh in reported_whs else "❌"
            cols[i % 4].markdown(f"{icon} **{wh}**")
            if wh not in reported_whs and selected_date:
                cols[i % 4].caption("Belum lapor")

st.divider()

# ── Summary Stok per Area ─────────────────────────────────────────────────────
if not df_all.empty:
    st.markdown('<div class="section-title">📈 Ringkasan Stok per Area</div>', unsafe_allow_html=True)
    
    for area in ["TELKOM BANDUNG", "TELKOM SOREANG"]:
        df_area = df_all[df_all["area"] == area]
        if df_area.empty:
            continue
        
        st.markdown(f"**{area}**")
        summary = df_area.groupby(["jenis_nte", "status_nte"])["closing_stock"].sum().reset_index()
        summary.columns = ["Jenis NTE", "Status", "Total Stok"]
        summary = summary.sort_values("Total Stok", ascending=False)
        
        col_t, col_c = st.columns([2, 1])
        with col_t:
            st.dataframe(
                summary,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total Stok": st.column_config.NumberColumn(format="%d unit")
                }
            )
        with col_c:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{int(df_area['closing_stock'].sum()):,}</div>
                <div class="kpi-label">Total Unit</div>
                <div class="kpi-sub">📦 {df_area['type_nte'].nunique()} type NTE</div>
                <div class="kpi-sub">🏭 {df_area['warehouse'].nunique()} WH lapor</div>
            </div>
            """, unsafe_allow_html=True)
        st.divider()
else:
    st.info(f"📭 Belum ada data stok untuk tanggal **{selected_date}**. Silakan input data melalui menu **Input Stok** atau **Upload Excel**.")

# ── Quick links ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🚀 Aksi Cepat</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.page_link("pages/1_Input_Stok.py", label="✏️ Input Stok Manual", use_container_width=True)
with c2:
    st.page_link("pages/2_Upload_Excel.py", label="📤 Upload Excel", use_container_width=True)
with c3:
    st.page_link("pages/3_Rekap_Otomatis.py", label="⚡ Rekap Otomatis", use_container_width=True)
with c4:
    st.page_link("pages/4_Tren_Stok.py", label="📉 Tren Stok", use_container_width=True)
