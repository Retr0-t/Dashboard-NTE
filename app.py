"""
NTE Stock Dashboard — Home / Overview
Operational Matrix Style (Google Sheet Inspired)

Operator: Telkomsel · Telkom · TIF
Area: Bandung · Soreang
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from utils.database import (
    init_db,
    get_available_dates,
    get_wh_coverage,
    get_stok,
)

from data.master_data import (
    AREA_CONFIG,
    ALL_OPERATORS,
    ALL_AREAS,
)

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="NTE Stock Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* =========================================================
HEADER
========================================================= */

.main-header{
    background:linear-gradient(135deg,#1E3A5F,#2E6DA4 60%,#3498DB);
    padding:1.75rem 2.5rem;
    border-radius:16px;
    color:white;
    margin-bottom:1.5rem;
    box-shadow:0 8px 32px rgba(30,58,95,.3)
}

.main-header h1{
    font-family:'Space Grotesk',sans-serif;
    font-size:1.9rem;
    font-weight:700;
    margin:0
}

.main-header p{
    font-size:.9rem;
    opacity:.85;
    margin:.3rem 0 0
}

/* =========================================================
BADGE
========================================================= */

.op-badge{
    display:inline-block;
    padding:3px 12px;
    border-radius:20px;
    font-size:.75rem;
    font-weight:600;
    margin:2px
}

.op-telkomsel{
    background:#E8F5E9;
    color:#1B5E20
}

.op-telkom{
    background:#E3F2FD;
    color:#0D47A1
}

.op-tif{
    background:#FFF3E0;
    color:#E65100
}

/* =========================================================
SECTION
========================================================= */

.section-title{
    font-family:'Space Grotesk',sans-serif;
    font-size:1rem;
    font-weight:600;
    color:#1E3A5F;
    border-bottom:2px solid #2E6DA4;
    padding-bottom:.4rem;
    margin:1.2rem 0 .8rem
}

/* =========================================================
METRIC
========================================================= */

[data-testid="metric-container"]{
    background:white;
    border:1px solid #E8EEF4;
    border-radius:12px;
    padding:1rem;
    box-shadow:0 2px 8px rgba(0,0,0,.05)
}

/* =========================================================
DATAFRAME
========================================================= */

[data-testid="stDataFrame"] {
    border: 1px solid #E8EEF4;
    border-radius: 12px;
    overflow: hidden;
}

/* =========================================================
SIDEBAR
========================================================= */

[data-testid="stSidebar"] {
    background: #1E3A5F;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# =============================================================================
# OPERATOR COLOR
# =============================================================================

OP_COLOR = {
    "TELKOMSEL": ("#1B5E20", "#E8F5E9"),
    "TELKOM":    ("#0D47A1", "#E3F2FD"),
    "TIF":       ("#E65100", "#FFF3E0"),
}

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:

    st.markdown("### 📦 NTE Dashboard")
    st.caption("Telkomsel · Telkom · TIF")

    st.divider()

    available_dates = get_available_dates()

    if available_dates:
        selected_date = st.selectbox(
            "📅 Tanggal Laporan",
            available_dates
        )
    else:
        selected_date = str(date.today())
        st.info("Belum ada data.")

    st.divider()

    filter_op = st.multiselect(
        "🏢 Filter Operator",
        ALL_OPERATORS,
        default=ALL_OPERATORS
    )

    filter_area = st.radio(
        "📍 Filter Area",
        ["Semua"] + ALL_AREAS,
        index=0
    )

    st.divider()

    st.caption(
        f"🕐 {datetime.now().strftime('%d %b %Y, %H:%M')}"
    )

    st.caption("v3.0.0 | Operational Matrix")

# =============================================================================
# HEADER
# =============================================================================

st.markdown("""
<div class="main-header">

    <h1>📦 NTE Stock Dashboard</h1>

    <p>
        Operational Monitoring Matrix · Network Terminal Environment
    </p>

    <div style="margin-top:.6rem">

        <span class="op-badge op-telkomsel">
            TELKOMSEL
        </span>

        <span class="op-badge op-telkom">
            TELKOM
        </span>

        <span class="op-badge op-tif">
            TIF
        </span>

        <span style="opacity:.7;font-size:.8rem;margin-left:.5rem">
            Bandung &amp; Soreang
        </span>

    </div>

</div>
""", unsafe_allow_html=True)

# =============================================================================
# LOAD DATA
# =============================================================================

df_coverage = (
    get_wh_coverage(selected_date)
    if selected_date else pd.DataFrame()
)

df_all = (
    get_stok(selected_date)
    if selected_date else pd.DataFrame()
)

# =============================================================================
# FILTER DATA
# =============================================================================

if not df_all.empty and filter_op:
    df_all = df_all[df_all["operator"].isin(filter_op)]

if not df_all.empty and filter_area != "Semua":
    df_all = df_all[df_all["area"] == filter_area]

# =============================================================================
# KPI
# =============================================================================

total_stok = (
    int(df_all["closing_stock"].sum())
    if not df_all.empty else 0
)

total_types = (
    df_all["type_nte"].nunique()
    if not df_all.empty else 0
)

total_wh = (
    df_all["warehouse"].nunique()
    if not df_all.empty else 0
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "📦 Total Stock",
    f"{total_stok:,}"
)

col2.metric(
    "🧩 Type NTE",
    total_types
)

col3.metric(
    "🏭 Warehouse Aktif",
    total_wh
)

st.divider()

# =============================================================================
# COVERAGE
# =============================================================================

st.markdown(
    '<div class="section-title">📊 Status Pelaporan Warehouse</div>',
    unsafe_allow_html=True
)

reported_set = set(
    zip(df_coverage["operator"], df_coverage["warehouse"])
) if not df_coverage.empty else set()

for op in ALL_OPERATORS:

    if op not in filter_op:
        continue

    txt_color, bg_color = OP_COLOR[op]

    with st.expander(f"🏢 {op}", expanded=True):

        cols_area = st.columns(2)

        for ai, area in enumerate(ALL_AREAS):

            area_key = f"{op} - {area}"

            if area_key not in AREA_CONFIG:
                continue

            whs = AREA_CONFIG[area_key]["warehouses"]

            rep = [
                w for w in whs
                if (op, w) in reported_set
            ]

            with cols_area[ai]:

                st.markdown(
                    f"""
                    <div style="
                        background:{bg_color};
                        color:{txt_color};
                        padding:8px 12px;
                        border-radius:8px;
                        font-weight:700;
                        margin-bottom:10px;
                    ">
                        📍 {area}
                        &nbsp;&nbsp;
                        ({len(rep)}/{len(whs)} WH)
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                for w in whs:

                    icon = "✅" if w in rep else "❌"

                    st.caption(f"{icon} {w}")

st.divider()

# =============================================================================
# OPERATIONAL MATRIX
# =============================================================================

if not df_all.empty:

    st.markdown(
        '<div class="section-title">📋 Operational Stock Matrix</div>',
        unsafe_allow_html=True
    )

    for op in filter_op:

        df_op = df_all[df_all["operator"] == op]

        if df_op.empty:
            continue

        txt_color, bg_color = OP_COLOR[op]

        st.markdown(
            f"""
            <div style="
                background:{bg_color};
                color:{txt_color};
                padding:10px 16px;
                border-radius:10px;
                font-weight:700;
                margin-bottom:12px;
                font-size:1rem;
            ">
                🏢 {op}
            </div>
            """,
            unsafe_allow_html=True
        )

        # =============================================================
        # AREA LOOP
        # =============================================================

        for area in sorted(df_op["area"].unique()):

            df_area = df_op[df_op["area"] == area]

            st.markdown(f"### 📍 {area}")

            # =========================================================
            # PIVOT TABLE
            # =========================================================

            pivot_df = pd.pivot_table(
                df_area,
                index=[
                    "jenis_nte",
                    "status_nte",
                    "type_nte"
                ],
                columns="warehouse",
                values="closing_stock",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            # =========================================================
            # COLUMN LIST
            # =========================================================

            warehouse_cols = [
                c for c in pivot_df.columns
                if c not in [
                    "jenis_nte",
                    "status_nte",
                    "type_nte"
                ]
            ]

            # =========================================================
            # GRAND TOTAL
            # =========================================================

            pivot_df["GRAND TOTAL"] = (
                pivot_df[warehouse_cols]
                .sum(axis=1)
            )

            # =========================================================
            # RENAME
            # =========================================================

            pivot_df = pivot_df.rename(columns={
                "jenis_nte": "JENIS NTE",
                "status_nte": "STATUS",
                "type_nte": "TYPE NTE",
            })

            # =========================================================
            # SORT
            # =========================================================

            pivot_df = pivot_df.sort_values(
                by=["JENIS NTE", "STATUS", "TYPE NTE"]
            )

            # =========================================================
            # STYLE
            # =========================================================

            styled_df = (
                pivot_df.style
                .background_gradient(
                    cmap="Blues",
                    subset=warehouse_cols + ["GRAND TOTAL"]
                )
                .format(precision=0)
            )

            # =========================================================
            # DISPLAY MATRIX
            # =========================================================

            st.dataframe(
                styled_df,
                use_container_width=True,
                height=650
            )

            # =========================================================
            # SUMMARY
            # =========================================================

            c1, c2, c3 = st.columns(3)

            c1.metric(
                "📦 Total Unit",
                f"{int(df_area['closing_stock'].sum()):,}"
            )

            c2.metric(
                "🧩 Type NTE",
                df_area["type_nte"].nunique()
            )

            c3.metric(
                "🏭 WH Lapor",
                df_area["warehouse"].nunique()
            )

            st.divider()

else:

    st.info(
        f"""
        📭 Belum ada data untuk
        **{selected_date}**
        """
    )

# =============================================================================
# QUICK MENU
# =============================================================================

st.markdown(
    '<div class="section-title">🚀 Quick Menu</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)

c1.page_link(
    "pages/1_Input_Stok.py",
    label="✏️ Input Stok",
    use_container_width=True
)

c2.page_link(
    "pages/2_Upload_Excel.py",
    label="📤 Upload Excel",
    use_container_width=True
)

c3.page_link(
    "pages/3_Rekap_Otomatis.py",
    label="⚡ Rekap",
    use_container_width=True
)

c4.page_link(
    "pages/4_Tren_Stok.py",
    label="📉 Trend",
    use_container_width=True
)
