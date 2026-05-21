"""
Page: Rekap Otomatis
Command center untuk generate rekap per area + grand total per type NTE
"""

import streamlit as st
import pandas as pd
import sys, os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.database import (
    init_db, get_available_dates, get_stok_by_date,
    get_rekap_per_wh, get_rekap_grand_total, log_rekap
)
from utils.export_utils import export_rekap_area_excel
from data.master_data import AREA_CONFIG, NTE_CATALOG

init_db()

st.set_page_config(page_title="Rekap Otomatis | NTE Dashboard", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.page-header {
    background: linear-gradient(135deg, #4A148C, #7B1FA2);
    color: white; padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1.5rem;
}
.page-header h2 { font-family: 'Space Grotesk', sans-serif; margin: 0; font-size: 1.5rem; }
.page-header p { margin: 0.25rem 0 0; opacity: 0.8; font-size: 0.9rem; }
.grand-total-box {
    background: linear-gradient(135deg, #FFF8E1, #FFF3E0);
    border: 2px solid #F57F17;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    margin-bottom: 1rem;
}
.pivot-area-header {
    background: linear-gradient(90deg, #1E3A5F 0%, #2E6DA4 100%);
    color: white;
    padding: 0.75rem 1.25rem;
    border-radius: 8px 8px 0 0;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    margin-top: 1rem;
}
.rekap-command-box {
    background: linear-gradient(135deg, #E8EAF6, #F3E5F5);
    border: 2px solid #7B1FA2;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>⚡ Rekap Otomatis</h2>
    <p>Generate rekap stok lengkap semua warehouse dengan 1 klik — per area beserta grand total per type NTE</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Opsi Rekap")
    available_dates = get_available_dates()
    
    if not available_dates:
        st.warning("Belum ada data tersedia.")
        st.stop()
    
    selected_date = st.selectbox("📅 Tanggal Rekap", available_dates)
    rekap_scope = st.radio(
        "📋 Scope Rekap",
        ["Semua Area", "TELKOM BANDUNG", "TELKOM SOREANG"],
        index=0
    )
    
    st.divider()
    show_zeros = st.checkbox("Tampilkan baris stok = 0", value=False)


def build_pivot(area: str, tanggal: str, warehouses: list, show_zeros: bool = False) -> pd.DataFrame:
    """Build pivot table: rows = (jenis, type, status), cols = warehouses + grand total"""
    df = get_rekap_per_wh(area, tanggal)
    
    if df.empty:
        return pd.DataFrame()
    
    # Pivot
    pivot = df.pivot_table(
        index=["jenis_nte", "type_nte", "status_nte"],
        columns="warehouse",
        values="closing_stock",
        aggfunc="sum",
        fill_value=0
    ).reset_index()
    
    pivot.columns.name = None
    
    # Add missing WH columns as 0
    for wh in warehouses:
        if wh not in pivot.columns:
            pivot[wh] = 0
    
    # Grand total column
    pivot["GRAND TOTAL"] = pivot[warehouses].sum(axis=1)
    
    if not show_zeros:
        pivot = pivot[pivot["GRAND TOTAL"] > 0]
    
    # Sort by jenis then type
    pivot = pivot.sort_values(["jenis_nte", "type_nte", "status_nte"])
    
    return pivot


def render_pivot_table(pivot_df: pd.DataFrame, warehouses: list, area: str):
    """Render pivot sebagai styled dataframe"""
    if pivot_df.empty:
        st.info(f"Tidak ada data stok untuk {area} pada tanggal ini.")
        return
    
    display_cols = ["jenis_nte", "type_nte", "status_nte"] + warehouses + ["GRAND TOTAL"]
    available = [c for c in display_cols if c in pivot_df.columns]
    df_display = pivot_df[available].copy()
    
    rename_map = {"jenis_nte": "Jenis NTE", "type_nte": "Type NTE", "status_nte": "Status"}
    df_display = df_display.rename(columns=rename_map)
    
    # Styling
    def highlight_grand_total(col):
        if col.name == "GRAND TOTAL":
            return ["background-color: #FADBD8; font-weight: bold; color: #C0392B"] * len(col)
        return [""] * len(col)
    
    def highlight_status(val):
        if val == "Baru":
            return "background-color: #D5F5E3; color: #1E8449"
        elif val == "Refurbish":
            return "background-color: #FFF8E1; color: #F57F17"
        return ""
    
    styled = df_display.style\
        .apply(highlight_grand_total)\
        .applymap(highlight_status, subset=["Status"])\
        .format({wh: "{:,.0f}" for wh in warehouses if wh in df_display.columns})\
        .format({"GRAND TOTAL": "{:,.0f}"})\
        .set_properties(**{"font-size": "12px"})
    
    st.dataframe(styled, use_container_width=True, hide_index=True)
    
    # Summary totals
    total_all = int(pivot_df["GRAND TOTAL"].sum())
    st.markdown(f"""
    <div style="text-align:right; color: #C0392B; font-weight: 700; font-size: 1rem; padding: 0.5rem 0;">
        🔢 Total Keseluruhan {area}: <span style="font-size:1.3rem">{total_all:,}</span> unit
    </div>
    """, unsafe_allow_html=True)


# ── COMMAND BUTTON ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="rekap-command-box">
    <div style="font-size:2.5rem">⚡</div>
    <div style="font-family:'Space Grotesk',sans-serif; font-size:1.3rem; font-weight:700; color:#4A148C; margin:0.5rem 0;">
        REKAP OTOMATIS — {rekap_scope}
    </div>
    <div style="color:#666; font-size:0.9rem">Tanggal: <b>{selected_date}</b></div>
</div>
""", unsafe_allow_html=True)

col_run, col_dl_all = st.columns([2, 1])

with col_run:
    run_rekap = st.button(
        "🚀 GENERATE REKAP SEKARANG",
        type="primary",
        use_container_width=True,
    )

# Determine areas to process
areas_to_process = (
    list(AREA_CONFIG.keys()) if rekap_scope == "Semua Area"
    else [rekap_scope]
)

# ── GENERATE REKAP ─────────────────────────────────────────────────────────────
if run_rekap or st.session_state.get("rekap_done"):
    st.session_state["rekap_done"] = True
    
    with st.spinner("⚙️ Memproses rekap..."):
        all_pivots = {}
        for area in areas_to_process:
            whs = AREA_CONFIG[area]["warehouses"]
            pivot = build_pivot(area, selected_date, whs, show_zeros)
            all_pivots[area] = (pivot, whs)
        log_rekap(selected_date, rekap_scope)
    
    st.success(f"✅ Rekap berhasil di-generate untuk **{len(areas_to_process)} area**!")
    st.divider()
    
    # ── Render per area ────────────────────────────────────────────────────────
    export_files = {}
    
    for area, (pivot_df, whs) in all_pivots.items():
        st.markdown(f'<div class="pivot-area-header">🏢 {area} — {len(whs)} Warehouse</div>', 
                    unsafe_allow_html=True)
        
        # WH coverage check
        df_detail = get_rekap_per_wh(area, selected_date)
        reported = df_detail["warehouse"].unique().tolist() if not df_detail.empty else []
        missing = [w for w in whs if w not in reported]
        
        if missing:
            st.warning(f"⚠️ {len(missing)} warehouse belum lapor: **{', '.join(missing)}**")
        
        # Pivot table
        render_pivot_table(pivot_df, whs, area)
        
        # Export button per area
        if not pivot_df.empty:
            excel_bytes = export_rekap_area_excel(
                pivot_df=pivot_df,
                detail_df=df_detail,
                area=area,
                tanggal=selected_date,
                warehouses=whs
            )
            export_files[area] = excel_bytes
            
            st.download_button(
                label=f"⬇️ Export Excel — {area}",
                data=excel_bytes,
                file_name=f"Rekap_NTE_{area.replace(' ', '_')}_{selected_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{area}"
            )
        
        st.divider()
    
    # ── Grand Summary across all areas ────────────────────────────────────────
    if rekap_scope == "Semua Area":
        st.markdown("### 🔢 Grand Summary — Semua Area")
        df_grand = get_rekap_grand_total(selected_date)
        
        if not df_grand.empty:
            summary_pivot = df_grand.pivot_table(
                index=["jenis_nte", "type_nte", "status_nte"],
                columns="area",
                values="total_stock",
                aggfunc="sum",
                fill_value=0
            ).reset_index()
            summary_pivot.columns.name = None
            
            area_cols = [c for c in summary_pivot.columns if c not in ["jenis_nte", "type_nte", "status_nte"]]
            summary_pivot["GRAND TOTAL SEMUA AREA"] = summary_pivot[area_cols].sum(axis=1)
            summary_pivot = summary_pivot[summary_pivot["GRAND TOTAL SEMUA AREA"] > 0]
            summary_pivot = summary_pivot.rename(columns={
                "jenis_nte": "Jenis NTE", "type_nte": "Type NTE", "status_nte": "Status"
            })
            
            st.dataframe(summary_pivot, use_container_width=True, hide_index=True)
            
            total_semua = int(summary_pivot["GRAND TOTAL SEMUA AREA"].sum())
            st.markdown(f"""
            <div class="grand-total-box">
                <div style="font-size:0.9rem; color:#F57F17; font-weight:600; text-transform:uppercase">
                    Total Keseluruhan Semua Area
                </div>
                <div style="font-family:'Space Grotesk',sans-serif; font-size:3rem; font-weight:700; color:#1E3A5F">
                    {total_semua:,}
                </div>
                <div style="color:#666">unit NTE · {selected_date}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("👆 Klik tombol **GENERATE REKAP SEKARANG** untuk memulai rekap otomatis.")
