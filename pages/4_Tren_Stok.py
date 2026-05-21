"""
Page: Tren Stok - Visualisasi tren stok harian
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.database import init_db, get_available_dates, get_stok_by_date, get_tren_stok
from data.master_data import AREA_CONFIG, ALL_NTE_TYPES, NTE_CATALOG, NTE_STATUS

init_db()

st.set_page_config(page_title="Tren Stok | NTE Dashboard", page_icon="📉", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #006064, #00838F);
    color: white; padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem;
}
.page-header h2 { font-family: 'Space Grotesk', sans-serif; margin: 0; font-size: 1.5rem; }
.page-header p { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>📉 Tren Stok Harian</h2>
    <p>Visualisasi pergerakan stok NTE dari hari ke hari</p>
</div>
""", unsafe_allow_html=True)

available_dates = get_available_dates()
if len(available_dates) < 2:
    st.info("📅 Dibutuhkan minimal **2 hari data** untuk menampilkan tren. Silakan input lebih banyak data terlebih dahulu.")
    st.stop()

with st.sidebar:
    st.markdown("### 📊 Filter Tren")
    selected_nte = st.selectbox(
        "Type NTE",
        options=ALL_NTE_TYPES,
        help="Pilih type NTE yang ingin dilihat tren stok-nya"
    )
    selected_status = st.selectbox("Status NTE", NTE_STATUS)
    show_by_area = st.checkbox("Pisah per Area", value=True)

# ── Tren chart untuk 1 type NTE ────────────────────────────────────────────────
st.markdown(f"#### 📈 Tren Stok: `{selected_nte}` — {selected_status}")

df_tren = get_tren_stok(selected_nte, selected_status)

if df_tren.empty:
    st.info(f"Tidak ada data historis untuk **{selected_nte}** ({selected_status}).")
else:
    df_tren["tanggal"] = pd.to_datetime(df_tren["tanggal"])
    df_tren = df_tren.sort_values("tanggal")
    
    if show_by_area:
        fig = px.line(
            df_tren, x="tanggal", y="total_stock", color="area",
            title=f"Tren Stok: {selected_nte} ({selected_status})",
            markers=True,
            color_discrete_map={
                "TELKOM BANDUNG": "#1E3A5F",
                "TELKOM SOREANG": "#2E7D32"
            },
            labels={"tanggal": "Tanggal", "total_stock": "Total Stok (Unit)", "area": "Area"}
        )
    else:
        df_agg = df_tren.groupby("tanggal")["total_stock"].sum().reset_index()
        fig = px.line(
            df_agg, x="tanggal", y="total_stock",
            title=f"Tren Stok Total: {selected_nte} ({selected_status})",
            markers=True,
            labels={"tanggal": "Tanggal", "total_stock": "Total Stok (Unit)"}
        )
    
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", rangemode="tozero"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=400,
        font=dict(family="Inter"),
    )
    fig.update_traces(line=dict(width=2.5))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Distribusi stok per area untuk tanggal terbaru ────────────────────────────
st.markdown("#### 🥧 Distribusi Stok per Area (Tanggal Terbaru)")
latest_date = available_dates[0]
df_latest = get_stok_by_date(latest_date)

if not df_latest.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie by area
        area_summary = df_latest.groupby("area")["closing_stock"].sum().reset_index()
        fig_pie = px.pie(
            area_summary, values="closing_stock", names="area",
            title=f"Distribusi per Area — {latest_date}",
            color_discrete_map={
                "TELKOM BANDUNG": "#1E3A5F",
                "TELKOM SOREANG": "#2E7D32"
            },
            hole=0.4
        )
        fig_pie.update_layout(font=dict(family="Inter"), height=350)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar by jenis NTE
        jenis_summary = df_latest.groupby("jenis_nte")["closing_stock"].sum().reset_index()
        jenis_summary = jenis_summary.sort_values("closing_stock", ascending=True)
        fig_bar = px.bar(
            jenis_summary, x="closing_stock", y="jenis_nte",
            title=f"Stok per Jenis NTE — {latest_date}",
            orientation="h",
            color="closing_stock",
            color_continuous_scale="Blues",
            labels={"closing_stock": "Total Unit", "jenis_nte": "Jenis NTE"}
        )
        fig_bar.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter"), height=350,
            showlegend=False, coloraxis_showscale=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # ── Top 10 NTE by stok ─────────────────────────────────────────────────────
    st.markdown("#### 🏆 Top 10 Type NTE Terbanyak")
    top10 = df_latest.groupby(["type_nte", "status_nte"])["closing_stock"].sum().reset_index()
    top10 = top10.sort_values("closing_stock", ascending=False).head(10)
    
    fig_top = px.bar(
        top10, x="type_nte", y="closing_stock", color="status_nte",
        title=f"Top 10 Type NTE — {latest_date}",
        barmode="group",
        color_discrete_map={"Baru": "#27AE60", "Refurbish": "#F39C12"},
        labels={"type_nte": "Type NTE", "closing_stock": "Total Unit", "status_nte": "Status"}
    )
    fig_top.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=400,
        xaxis_tickangle=-35
    )
    st.plotly_chart(fig_top, use_container_width=True)
