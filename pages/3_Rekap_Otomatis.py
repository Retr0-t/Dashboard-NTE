"""
Page: Rekap Otomatis
Format persis seperti laporan STOCK NTE TELKOM:
Kolom: JENIS 2 | STATUS | TYPE | [WH1] [WH2] ... | Grand Total
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
from data.master_data import AREA_CONFIG, NTE_CATALOG, NTE_STATUS

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
.page-header h2 { font-family:'Space Grotesk',sans-serif; margin:0; font-size:1.5rem; }
.page-header p  { margin:.25rem 0 0; opacity:.8; font-size:.9rem; }
.area-header {
    background: linear-gradient(90deg,#1E3A5F,#2E6DA4);
    color:white; padding:.75rem 1.25rem; border-radius:8px 8px 0 0;
    font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:1rem; margin-top:1rem;
}
.grand-box {
    background:linear-gradient(135deg,#FFF8E1,#FFF3E0);
    border:2px solid #F57F17; border-radius:12px;
    padding:1.2rem; text-align:center; margin:1rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>⚡ Rekap Otomatis</h2>
    <p>Generate rekap STOCK NTE — format pivot per area, grand total per type NTE</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Opsi Rekap")
    available_dates = get_available_dates()
    if not available_dates:
        st.warning("Belum ada data. Input stok terlebih dahulu.")
        st.stop()

    selected_date = st.selectbox("📅 Tanggal Rekap", available_dates)
    rekap_scope   = st.radio("📋 Scope", ["Semua Area"] + list(AREA_CONFIG.keys()), index=0)
    show_zeros    = st.checkbox("Tampilkan baris stok = 0", value=False)
    st.divider()
    st.caption(f"Total WH terdaftar: {sum(len(v['warehouses']) for v in AREA_CONFIG.values())}")


def build_pivot(area: str, tanggal: str, warehouses: list) -> pd.DataFrame:
    """
    Pivot table format laporan asli:
    Baris  = (jenis_nte, type_nte, status_nte)
    Kolom  = warehouse names + GRAND TOTAL
    Urutan = sesuai NTE_CATALOG (jenis) → type → NTE BARU dulu, REFURBISH kemudian
    """
    df = get_rekap_per_wh(area, tanggal)
    if df.empty:
        return pd.DataFrame()

    pivot = df.pivot_table(
        index=["jenis_nte", "type_nte", "status_nte"],
        columns="warehouse",
        values="closing_stock",
        aggfunc="sum",
        fill_value=0
    ).reset_index()
    pivot.columns.name = None

    # Pastikan semua kolom WH ada meski kosong
    for wh in warehouses:
        if wh not in pivot.columns:
            pivot[wh] = 0

    pivot["Grand Total"] = pivot[warehouses].sum(axis=1)

    # ── Urutkan sesuai urutan NTE_CATALOG + status (NTE BARU → REFURBISH) ──
    jenis_order  = {j: i for i, j in enumerate(NTE_CATALOG.keys())}
    status_order = {s: i for i, s in enumerate(NTE_STATUS)}
    pivot["_jo"] = pivot["jenis_nte"].map(jenis_order).fillna(99)
    pivot["_so"] = pivot["status_nte"].map(status_order).fillna(99)
    pivot = pivot.sort_values(["_jo", "type_nte", "_so"]).drop(columns=["_jo", "_so"])

    if not show_zeros:
        pivot = pivot[pivot["Grand Total"] > 0]

    return pivot.reset_index(drop=True)


def render_rekap_table(pivot_df: pd.DataFrame, warehouses: list, area: str):
    """Tampilkan pivot table dengan styling seperti laporan asli."""
    if pivot_df.empty:
        st.info(f"Tidak ada data untuk {area} pada tanggal ini.")
        return

    display_cols = ["jenis_nte", "type_nte", "status_nte"] + warehouses + ["Grand Total"]
    available    = [c for c in display_cols if c in pivot_df.columns]
    df_show      = pivot_df[available].rename(columns={
        "jenis_nte":  "JENIS 2",
        "type_nte":   "TYPE",
        "status_nte": "STATUS",
    })

    def style_table(styler):
        # Grand Total kolom — merah muda
        if "Grand Total" in styler.columns:
            styler.set_properties(subset=["Grand Total"],
                **{"background-color": "#FADBD8", "font-weight": "bold", "color": "#C0392B"})
        # Status — hijau / kuning
        def color_status(val):
            if val == "NTE BARU":    return "background-color:#D5F5E3; color:#1E8449; font-weight:600"
            if val == "REFURBISH":   return "background-color:#FFF3CD; color:#856404; font-weight:600"
            return ""
        if "STATUS" in styler.columns:
            styler.applymap(color_status, subset=["STATUS"])
        # Angka 0 di-grey
        num_cols = [c for c in df_show.columns if c not in ["JENIS 2", "TYPE", "STATUS"]]
        def grey_zero(val):
            try:
                return "color:#CCCCCC" if int(val) == 0 else ""
            except Exception:
                return ""
        if num_cols:
            styler.applymap(grey_zero, subset=num_cols)
            styler.format("{:,.0f}", subset=num_cols)
        return styler

    st.dataframe(
        df_show.style.pipe(style_table),
        use_container_width=True,
        hide_index=True,
        height=min(600, 38 + len(df_show) * 35),
    )

    total = int(pivot_df["Grand Total"].sum())
    st.markdown(f"""
    <div style="text-align:right;color:#C0392B;font-weight:700;font-size:1rem;padding:.4rem 0">
        🔢 Grand Total <b>{area}</b>: <span style="font-size:1.25rem">{total:,}</span> unit
    </div>""", unsafe_allow_html=True)


# ── Command button ─────────────────────────────────────────────────────────────
col_btn, col_info = st.columns([2, 3])
with col_btn:
    run = st.button("🚀 GENERATE REKAP SEKARANG", type="primary", use_container_width=True)
with col_info:
    st.info(f"📅 **{selected_date}** · Scope: **{rekap_scope}**")

areas_to_process = (
    list(AREA_CONFIG.keys()) if rekap_scope == "Semua Area" else [rekap_scope]
)

# ── Generate ───────────────────────────────────────────────────────────────────
if run or st.session_state.get("rekap_generated"):
    st.session_state["rekap_generated"] = True

    with st.spinner("Memproses rekap..."):
        all_pivots = {}
        for area in areas_to_process:
            whs   = AREA_CONFIG[area]["warehouses"]
            pivot = build_pivot(area, selected_date, whs)
            all_pivots[area] = (pivot, whs)
        log_rekap(selected_date, rekap_scope)

    st.success(f"✅ Rekap berhasil — **{len(areas_to_process)} area** | {selected_date}")
    st.divider()

    for area, (pivot_df, whs) in all_pivots.items():
        # Header area
        st.markdown(f'<div class="area-header">🏢 STOCK NTE {area} — {len(whs)} Warehouse</div>',
                    unsafe_allow_html=True)

        # Coverage check
        df_detail = get_rekap_per_wh(area, selected_date)
        reported  = df_detail["warehouse"].unique().tolist() if not df_detail.empty else []
        missing   = [w for w in whs if w not in reported]
        if missing:
            st.warning(f"⚠️ **{len(missing)} WH belum lapor:** {', '.join(missing)}")

        # Pivot table
        render_rekap_table(pivot_df, whs, area)

        # Export per area
        if not pivot_df.empty:
            xlsx = export_rekap_area_excel(
                pivot_df=pivot_df, detail_df=df_detail,
                area=area, tanggal=selected_date, warehouses=whs
            )
            st.download_button(
                label=f"⬇️ Export Excel — {area}",
                data=xlsx,
                file_name=f"STOCK_NTE_{area.replace(' ','_')}_{selected_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{area}"
            )
        st.divider()

    # ── Grand total lintas area ─────────────────────────────────────────────
    if rekap_scope == "Semua Area":
        st.markdown("### 🔢 Grand Total — Semua Area")
        df_grand = get_rekap_grand_total(selected_date)

        if not df_grand.empty:
            gp = df_grand.pivot_table(
                index=["jenis_nte","type_nte","status_nte"],
                columns="area", values="total_stock",
                aggfunc="sum", fill_value=0
            ).reset_index()
            gp.columns.name = None
            area_cols = [c for c in gp.columns if c not in ["jenis_nte","type_nte","status_nte"]]
            gp["GRAND TOTAL SEMUA AREA"] = gp[area_cols].sum(axis=1)
            gp = gp[gp["GRAND TOTAL SEMUA AREA"] > 0]
            gp = gp.rename(columns={"jenis_nte":"JENIS 2","type_nte":"TYPE","status_nte":"STATUS"})
            st.dataframe(gp, use_container_width=True, hide_index=True)

            total_all = int(gp["GRAND TOTAL SEMUA AREA"].sum())
            st.markdown(f"""
            <div class="grand-box">
                <div style="color:#F57F17;font-weight:600;font-size:.9rem;text-transform:uppercase">
                    Grand Total Keseluruhan Semua Area
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:2.8rem;font-weight:700;color:#1E3A5F">
                    {total_all:,}
                </div>
                <div style="color:#888;font-size:.9rem">unit NTE · {selected_date}</div>
            </div>""", unsafe_allow_html=True)

else:
    st.info("👆 Klik **GENERATE REKAP SEKARANG** untuk memulai rekap otomatis.")
