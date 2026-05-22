"""Page: Tren Stok"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.database import init_db, get_available_dates, get_stok, get_tren_stok
from data.master_data import ALL_NTE_TYPES, NTE_CATALOG, NTE_STATUS, ALL_OPERATORS
init_db()

st.set_page_config(page_title="Tren Stok | NTE Dashboard", page_icon="📉", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.page-header{background:linear-gradient(135deg,#006064,#00838F);color:white;
  padding:1.5rem 2rem;border-radius:12px;margin-bottom:1.5rem}
.page-header h2{font-family:'Space Grotesk',sans-serif;margin:0;font-size:1.5rem}
.page-header p{margin:.25rem 0 0;opacity:.8;font-size:.9rem}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>📉 Tren Stok Harian</h2>
    <p>Visualisasi pergerakan stok NTE dari hari ke hari per operator & area</p>
</div>
""", unsafe_allow_html=True)

avail = get_available_dates()
if len(avail) < 2:
    st.info("Dibutuhkan minimal **2 hari data** untuk menampilkan tren."); st.stop()

with st.sidebar:
    st.markdown("### 📊 Filter")
    sel_nte    = st.selectbox("Type NTE", ALL_NTE_TYPES)
    sel_status = st.selectbox("Status", NTE_STATUS)
    sel_op     = st.selectbox("Operator", ["Semua"] + ALL_OPERATORS)
    by_area    = st.checkbox("Pisah per Area", value=True)

st.markdown(f"#### Tren: `{sel_nte}` — {sel_status}")

df_tren = get_tren_stok(
    sel_nte, sel_status,
    operator=(None if sel_op == "Semua" else sel_op)
)

if df_tren.empty:
    st.info("Tidak ada data historis untuk pilihan ini.")
else:
    df_tren["tanggal"] = pd.to_datetime(df_tren["tanggal"])
    df_tren = df_tren.sort_values("tanggal")

    color_col = "area" if by_area else "operator"
    fig = px.line(
        df_tren, x="tanggal", y="total_stock",
        color=color_col, markers=True,
        title=f"Tren: {sel_nte} ({sel_status})"
            + (f" — {sel_op}" if sel_op != "Semua" else ""),
        labels={"tanggal":"Tanggal","total_stock":"Total Stok","area":"Area","operator":"Operator"}
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0"),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", rangemode="tozero"),
        height=400, font=dict(family="Inter"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    fig.update_traces(line=dict(width=2.5))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

latest = avail[0]
df_latest = get_stok(latest)
if not df_latest.empty:
    st.markdown(f"#### Distribusi Stok — {latest}")
    c1, c2 = st.columns(2)

    with c1:
        pie_data = df_latest.groupby("operator")["closing_stock"].sum().reset_index()
        fig_pie = px.pie(
            pie_data, values="closing_stock", names="operator",
            title="Per Operator",
            color_discrete_map={"TELKOMSEL":"#1B5E20","TELKOM":"#0D47A1","TIF":"#E65100"},
            hole=0.4
        )
        fig_pie.update_layout(font=dict(family="Inter"), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        bar_data = (
            df_latest.groupby(["operator","area"])["closing_stock"].sum()
            .reset_index()
            .rename(columns={"closing_stock":"Total Stok"})
        )
        fig_bar = px.bar(
            bar_data, x="operator", y="Total Stok", color="area",
            title="Per Operator & Area", barmode="group",
            labels={"operator":"Operator","area":"Area"}
        )
        fig_bar.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter"), height=320
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("#### 🏆 Top 10 Type NTE")
    top10 = (
        df_latest.groupby(["type_nte","status_nte"])["closing_stock"].sum()
        .reset_index().sort_values("closing_stock", ascending=False).head(10)
    )
    fig_top = px.bar(
        top10, x="type_nte", y="closing_stock", color="status_nte",
        barmode="group",
        color_discrete_map={"NTE BARU":"#27AE60","REFURBISH":"#F39C12"},
        labels={"type_nte":"Type NTE","closing_stock":"Total Unit","status_nte":"Status"}
    )
    fig_top.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=380, xaxis_tickangle=-35
    )
    st.plotly_chart(fig_top, use_container_width=True)
