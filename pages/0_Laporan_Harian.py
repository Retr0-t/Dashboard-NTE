"""
Page: Laporan Harian
Tampilan pivot persis seperti G-Sheet:
  Header: STOCK NTE [OPERATOR] [AREA]
  Kolom : JENIS 2 | STATUS | TYPE | [WH1..N] | Grand Total
  Baris : diurutkan per jenis → status → type
  Warna : hijau = stok banyak, kuning = sedang, merah = sedikit/kosong (heat map)
"""

import streamlit as st
import pandas as pd
import sys, os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.database import init_db, get_available_dates, get_rekap_per_wh, get_wh_coverage
from data.master_data import (
    AREA_CONFIG, ALL_OPERATORS, ALL_AREAS,
    NTE_CATALOG_BY_OPERATOR, NTE_STATUS,
    get_all_jenis, get_type_to_jenis
)

init_db()

st.set_page_config(
    page_title="Laporan Harian | NTE Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}

.page-header{
    background:linear-gradient(135deg,#0D3B66,#1565C0);
    color:white;padding:1.5rem 2rem;border-radius:12px;margin-bottom:1.5rem;
    box-shadow:0 4px 20px rgba(13,59,102,.3)
}
.page-header h2{font-family:'Space Grotesk',sans-serif;margin:0;font-size:1.5rem}
.page-header p{margin:.25rem 0 0;opacity:.8;font-size:.9rem}

.report-title{
    font-family:'Space Grotesk',sans-serif;
    font-size:1.1rem;font-weight:700;
    background:linear-gradient(90deg,#1E3A5F,#2E6DA4);
    color:white;padding:.65rem 1.25rem;
    border-radius:8px;margin-bottom:.5rem;
    display:flex;align-items:center;gap:.5rem
}

.coverage-ok  {color:#1E8449;font-weight:600}
.coverage-warn{color:#D35400;font-weight:600}
.coverage-miss{color:#C0392B;font-weight:600}

.kpi-row{display:flex;gap:.75rem;margin-bottom:1rem;flex-wrap:wrap}
.kpi-card{background:white;border:1px solid #E8EEF4;border-radius:10px;
  padding:.75rem 1.25rem;min-width:130px;box-shadow:0 2px 6px rgba(0,0,0,.05)}
.kpi-val{font-family:'Space Grotesk',sans-serif;font-size:1.6rem;font-weight:700;color:#1E3A5F;line-height:1}
.kpi-lbl{font-size:.72rem;color:#888;text-transform:uppercase;font-weight:500;margin-top:.2rem}

.wh-chip{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.72rem;
  font-weight:500;margin:2px}
.wh-ok  {background:#D5F5E3;color:#1E8449}
.wh-miss{background:#FADBD8;color:#C0392B}

div[data-testid="stDataFrame"] table thead tr th{
    background:#1E3A5F!important;color:white!important;
    font-size:11px!important;font-weight:600!important;
    text-align:center!important;white-space:nowrap
}
</style>
""", unsafe_allow_html=True)

# ── Operator badge colors ─────────────────────────────────────────────────────
OP_STYLE = {
    "TELKOMSEL": {"bg": "#1B5E20", "light": "#E8F5E9", "txt": "#1B5E20"},
    "TELKOM":    {"bg": "#0D47A1", "light": "#E3F2FD", "txt": "#0D47A1"},
    "TIF":       {"bg": "#E65100", "light": "#FFF3E0", "txt": "#E65100"},
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Filter Laporan")

    avail_dates = get_available_dates()
    if not avail_dates:
        st.warning("Belum ada data stok.")
        st.stop()

    selected_date = st.selectbox("📅 Tanggal", avail_dates)

    selected_op = st.selectbox("🏢 Operator", ALL_OPERATORS)

    area_opts = [
        area for area in ALL_AREAS
        if f"{selected_op} - {area}" in AREA_CONFIG
    ]
    selected_area = st.selectbox("📍 Area", area_opts)

    area_key = f"{selected_op} - {selected_area}"
    warehouses = AREA_CONFIG[area_key]["warehouses"]

    st.divider()
    st.caption(f"WH terdaftar: **{len(warehouses)}**")

    # Tampilan options
    st.markdown("#### 🎨 Tampilan")
    show_heatmap  = st.checkbox("Heat map warna", value=True,
                                help="Warnai sel angka seperti di G-Sheet")
    show_zeros    = st.checkbox("Tampilkan baris stok = 0", value=False)
    hide_zero_wh  = st.checkbox("Sembunyikan WH kosong", value=False)

# ── Page header ───────────────────────────────────────────────────────────────
op_s = OP_STYLE.get(selected_op, {"bg":"#1E3A5F","light":"#EEF","txt":"#1E3A5F"})

st.markdown(f"""
<div class="page-header">
    <h2>📋 Laporan Harian NTE</h2>
    <p>Tampilan pivot detail seperti G-Sheet — {selected_date}</p>
</div>
""", unsafe_allow_html=True)

# ── Build pivot ───────────────────────────────────────────────────────────────
df_raw = get_rekap_per_wh(area_key, selected_date)

# Coverage
df_cov    = get_wh_coverage(selected_date)
op_cov    = df_cov[(df_cov["operator"] == selected_op) & (df_cov["area_key"] == area_key)] \
            if not df_cov.empty else pd.DataFrame()
reported_whs = set(op_cov["warehouse"].tolist()) if not op_cov.empty else set()
missing_whs  = [w for w in warehouses if w not in reported_whs]

# ── KPI bar ───────────────────────────────────────────────────────────────────
if not df_raw.empty:
    total_stok  = int(df_raw["closing_stock"].sum())
    total_types = df_raw["type_nte"].nunique()
    total_jenis = df_raw["jenis_nte"].nunique()
else:
    total_stok = total_types = total_jenis = 0

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-val">{total_stok:,}</div>
    <div class="kpi-lbl">Total Unit</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-val">{total_types}</div>
    <div class="kpi-lbl">Type NTE</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-val">{total_jenis}</div>
    <div class="kpi-lbl">Jenis NTE</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-val" style="color:{'#1E8449' if len(reported_whs)==len(warehouses) else '#C0392B'}">
      {len(reported_whs)}/{len(warehouses)}
    </div>
    <div class="kpi-lbl">WH Lapor</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Coverage chips ────────────────────────────────────────────────────────────
chips = ""
for w in warehouses:
    cls  = "wh-ok" if w in reported_whs else "wh-miss"
    icon = "✅" if w in reported_whs else "❌"
    # Singkat nama WH
    short = w.replace("TA SO INV ","").replace("TA SO CCAN ","").replace("TA SO TIF ","").replace(" WH","")
    chips += f'<span class="wh-chip {cls}">{icon} {short}</span>'

st.markdown(chips, unsafe_allow_html=True)

if missing_whs:
    st.warning(f"⚠️ **{len(missing_whs)} WH belum lapor:** {', '.join(missing_whs)}")

st.divider()

# ── Report title (mirip G-Sheet) ──────────────────────────────────────────────
st.markdown(
    f'<div class="report-title">'
    f'📊 STOCK NTE {selected_op} {selected_area} &nbsp;·&nbsp; {selected_date}'
    f'</div>',
    unsafe_allow_html=True
)

# ── Pivot ─────────────────────────────────────────────────────────────────────
if df_raw.empty:
    st.info("📭 Belum ada data stok untuk kombinasi ini. Silakan input data terlebih dahulu.")
    st.stop()

# Aktif WH untuk kolom (hide kosong jika opsi aktif)
if hide_zero_wh:
    active_whs = [w for w in warehouses if w in df_raw["warehouse"].unique()]
else:
    active_whs = warehouses

pivot = df_raw.pivot_table(
    index=["jenis_nte", "type_nte", "status_nte"],
    columns="warehouse",
    values="closing_stock",
    aggfunc="sum",
    fill_value=0
).reset_index()
pivot.columns.name = None

# Pastikan semua WH ada
for wh in active_whs:
    if wh not in pivot.columns:
        pivot[wh] = 0

pivot["Grand Total"] = pivot[active_whs].sum(axis=1)

# Sort sesuai urutan katalog operator
catalog = NTE_CATALOG_BY_OPERATOR.get(selected_op, {})
jenis_order  = {j: i for i, j in enumerate(catalog.keys())}
status_order = {s: i for i, s in enumerate(NTE_STATUS)}
pivot["_j"] = pivot["jenis_nte"].map(jenis_order).fillna(99)
pivot["_s"] = pivot["status_nte"].map(status_order).fillna(99)
pivot = pivot.sort_values(["_j", "type_nte", "_s"]).drop(columns=["_j","_s"])

if not show_zeros:
    pivot = pivot[pivot["Grand Total"] > 0]

pivot = pivot.reset_index(drop=True)

if pivot.empty:
    st.info("Tidak ada data dengan stok > 0. Aktifkan 'Tampilkan baris stok = 0' untuk melihat semua.")
    st.stop()

# ── Display columns ───────────────────────────────────────────────────────────
disp_cols = ["jenis_nte", "type_nte", "status_nte"] + active_whs + ["Grand Total"]
avail     = [c for c in disp_cols if c in pivot.columns]
df_show   = pivot[avail].rename(columns={
    "jenis_nte":  "JENIS 2",
    "type_nte":   "TYPE",
    "status_nte": "STATUS",
})

# Shorten WH column headers
short_map = {
    w: w.replace("TA SO INV ","").replace("TA SO CCAN ","").replace("TA SO TIF ","").replace(" WH","")
    for w in active_whs
}
df_show = df_show.rename(columns=short_map)
short_wh_cols = [short_map.get(w, w) for w in active_whs]

# ── Styling ───────────────────────────────────────────────────────────────────
num_cols = short_wh_cols + ["Grand Total"]

def apply_styles(styler):
    # STATUS badge warna
    def color_status(val):
        if val == "NTE BARU":
            return "background-color:#D5F5E3;color:#1E8449;font-weight:600"
        if val == "REFURBISH":
            return "background-color:#FFF3CD;color:#856404;font-weight:600"
        return ""

    # Grand Total kolom
    def color_gt(col):
        if col.name == "Grand Total":
            return ["background-color:#FADBD8;color:#C0392B;font-weight:bold"] * len(col)
        return [""] * len(col)

    # Heat map per WH (mirip G-Sheet: merah=0, kuning=sedikit, hijau=banyak)
    def heatmap(col):
        if col.name not in short_wh_cols:
            return [""] * len(col)
        max_val = col.max()
        if max_val == 0:
            return ["color:#CCCCCC"] * len(col)
        styles = []
        for v in col:
            try:
                ratio = v / max_val
            except Exception:
                ratio = 0
            if v == 0:
                styles.append("color:#CCCCCC")
            elif ratio < 0.2:
                styles.append("background-color:#FADBD8;color:#922B21")   # merah
            elif ratio < 0.5:
                styles.append("background-color:#FDEBD0;color:#784212")   # oranye
            elif ratio < 0.8:
                styles.append("background-color:#FDFDE7;color:#7D6608")   # kuning
            else:
                styles.append("background-color:#D5F5E3;color:#1E8449")   # hijau
        return styles

    # pandas ≥2.1: applymap → map
    _map = getattr(styler, "map", None) or styler.applymap
    _map(color_status, subset=["STATUS"])
    styler.apply(color_gt)
    if show_heatmap:
        styler.apply(heatmap)
    # Format angka — hanya kolom yang benar-benar ada dan bertipe numerik
    fmt_cols = [c for c in num_cols if c in df_show.columns
                and pd.api.types.is_numeric_dtype(df_show[c])]
    if fmt_cols:
        styler.format("{:,.0f}", subset=fmt_cols, na_rep="-")
    return styler

styled = df_show.style.pipe(apply_styles)

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    height=min(700, 42 + len(df_show) * 35),
    column_config={
        "JENIS 2": st.column_config.TextColumn(width="medium"),
        "STATUS":  st.column_config.TextColumn(width="small"),
        "TYPE":    st.column_config.TextColumn(width="large"),
        "Grand Total": st.column_config.NumberColumn(width="small"),
    }
)

# ── Grand Total row summary ───────────────────────────────────────────────────
st.markdown("---")
col_totals = st.columns(len(active_whs) + 1)
wh_totals  = {w: int(pivot[w].sum()) for w in active_whs if w in pivot.columns}
grand_all  = int(pivot["Grand Total"].sum())

for i, (wh, tot) in enumerate(wh_totals.items()):
    short = short_map.get(wh, wh)
    col_totals[i].metric(short, f"{tot:,}")
col_totals[-1].metric("**Grand Total**", f"**{grand_all:,}**")

st.divider()

# ── Per-jenis breakdown ───────────────────────────────────────────────────────
with st.expander("📊 Breakdown per Jenis NTE"):
    jenis_summary = (
        pivot.groupby("jenis_nte")["Grand Total"].sum()
        .reset_index()
        .rename(columns={"jenis_nte":"Jenis NTE","Grand Total":"Total Stok"})
        .sort_values("Total Stok", ascending=False)
    )
    jenis_summary["% dari Total"] = (
        jenis_summary["Total Stok"] / jenis_summary["Total Stok"].sum() * 100
    ).round(1).astype(str) + "%"
    st.dataframe(jenis_summary, hide_index=True, use_container_width=True,
                 column_config={"Total Stok": st.column_config.NumberColumn(format="%d unit")})

# ── Export ────────────────────────────────────────────────────────────────────
from utils.export_utils import export_rekap_area_excel

col_ex1, col_ex2 = st.columns([2,3])
with col_ex1:
    detail_df = df_raw.copy()
    xlsx = export_rekap_area_excel(
        pivot_df   = pivot,
        detail_df  = detail_df,
        area       = f"{selected_op} - {selected_area}",
        tanggal    = selected_date,
        warehouses = active_whs
    )
    st.download_button(
        label    = f"⬇️ Export Excel — {selected_op} {selected_area}",
        data     = xlsx,
        file_name= f"STOCK_NTE_{selected_op}_{selected_area}_{selected_date}.xlsx",
        mime     = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type     = "primary"
    )
with col_ex2:
    st.caption(
        f"Export berisi pivot table lengkap + sheet Data Detail. "
        f"Format mengikuti laporan G-Sheet."
    )
