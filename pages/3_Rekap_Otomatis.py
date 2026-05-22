"""Page: Rekap Otomatis — pivot per operator×area, grand total per type NTE"""

import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.database import (init_db, get_available_dates, get_rekap_per_wh,
                             get_grand_total, get_stok, log_rekap)
from utils.export_utils import export_rekap_area_excel
from data.master_data import AREA_CONFIG, ALL_OPERATORS, ALL_AREAS, NTE_CATALOG, NTE_STATUS

init_db()

st.set_page_config(page_title="Rekap Otomatis | NTE Dashboard", page_icon="⚡", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.page-header{background:linear-gradient(135deg,#4A148C,#7B1FA2);color:white;
  padding:1.5rem 2rem;border-radius:12px;margin-bottom:1.5rem}
.page-header h2{font-family:'Space Grotesk',sans-serif;margin:0;font-size:1.5rem}
.page-header p{margin:.25rem 0 0;opacity:.8;font-size:.9rem}
.area-hdr{color:white;padding:.65rem 1.25rem;border-radius:8px 8px 0 0;
  font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:.95rem;margin-top:1rem}
.grand-box{border:2px solid #F57F17;border-radius:12px;
  padding:1.2rem;text-align:center;margin:1rem 0}
</style>
""", unsafe_allow_html=True)

OP_BG = {"TELKOMSEL":"#1B5E20","TELKOM":"#0D47A1","TIF":"#E65100"}

st.markdown("""
<div class="page-header">
    <h2>⚡ Rekap Otomatis</h2>
    <p>Generate pivot STOCK NTE per operator × area — grand total per type NTE lintas warehouse</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Opsi Rekap")
    avail = get_available_dates()
    if not avail:
        st.warning("Belum ada data."); st.stop()
    selected_date = st.selectbox("📅 Tanggal", avail)

    # Scope selector
    scope_opts = ["Semua"] + ALL_OPERATORS + [
        f"{op} - {area}" for op in ALL_OPERATORS for area in ALL_AREAS
        if f"{op} - {area}" in AREA_CONFIG
    ]
    scope = st.selectbox("📋 Scope", scope_opts)
    show_zeros = st.checkbox("Tampilkan baris stok = 0", value=False)

# Tentukan area_keys yang diproses
if scope == "Semua":
    keys_to_process = list(AREA_CONFIG.keys())
elif scope in ALL_OPERATORS:
    keys_to_process = [k for k,v in AREA_CONFIG.items() if v["operator"] == scope]
else:
    keys_to_process = [scope] if scope in AREA_CONFIG else []


def build_pivot(area_key, tanggal, warehouses):
    df = get_rekap_per_wh(area_key, tanggal)
    if df.empty:
        return pd.DataFrame()
    pivot = df.pivot_table(
        index=["jenis_nte","type_nte","status_nte"],
        columns="warehouse", values="closing_stock",
        aggfunc="sum", fill_value=0
    ).reset_index()
    pivot.columns.name = None
    for wh in warehouses:
        if wh not in pivot.columns:
            pivot[wh] = 0
    pivot["Grand Total"] = pivot[warehouses].sum(axis=1)
    # Sort sesuai urutan katalog
    jo = {j:i for i,j in enumerate(NTE_CATALOG)}
    so = {s:i for i,s in enumerate(NTE_STATUS)}
    pivot["_j"] = pivot["jenis_nte"].map(jo).fillna(99)
    pivot["_s"] = pivot["status_nte"].map(so).fillna(99)
    pivot = pivot.sort_values(["_j","type_nte","_s"]).drop(columns=["_j","_s"])
    if not show_zeros:
        pivot = pivot[pivot["Grand Total"] > 0]
    return pivot.reset_index(drop=True)


def render_pivot(pivot_df, warehouses, label):
    if pivot_df.empty:
        st.info(f"Tidak ada data untuk {label}.")
        return
    cols = ["jenis_nte","type_nte","status_nte"] + warehouses + ["Grand Total"]
    avail_cols = [c for c in cols if c in pivot_df.columns]
    df_show = pivot_df[avail_cols].rename(columns={
        "jenis_nte":"JENIS 2","type_nte":"TYPE","status_nte":"STATUS"
    })

    def styler(s):
        if s.name == "Grand Total":
            return ["background-color:#FADBD8;font-weight:bold;color:#C0392B"]*len(s)
        if s.name == "STATUS":
            return [
                "background-color:#D5F5E3;color:#1E8449;font-weight:600" if v=="NTE BARU"
                else "background-color:#FFF3CD;color:#856404;font-weight:600"
                for v in s
            ]
        return [""]*len(s)

    num_cols = [c for c in df_show.columns if c not in ["JENIS 2","TYPE","STATUS"] and pd.api.types.is_numeric_dtype(df_show[c])]
    styled = df_show.style.apply(styler)
    if num_cols:
        styled = styled.format("{:,.0f}", subset=num_cols, na_rep="-")

    st.dataframe(styled, use_container_width=True, hide_index=True,
                 height=min(600, 38 + len(df_show)*35))
    total = int(pivot_df["Grand Total"].sum())
    st.markdown(
        f'<div style="text-align:right;color:#C0392B;font-weight:700;padding:.3rem 0">'
        f'🔢 Grand Total: <span style="font-size:1.2rem">{total:,}</span> unit</div>',
        unsafe_allow_html=True
    )


# ── Command button ─────────────────────────────────────────────────────────────
c1, c2 = st.columns([2,3])
with c1:
    run = st.button("🚀 GENERATE REKAP SEKARANG", type="primary", use_container_width=True)
with c2:
    st.info(f"📅 **{selected_date}** · Scope: **{scope}** · {len(keys_to_process)} laporan")

if run or st.session_state.get("rekap_ok"):
    st.session_state["rekap_ok"] = True

    with st.spinner("Memproses..."):
        all_data = {}
        for ak in keys_to_process:
            whs   = AREA_CONFIG[ak]["warehouses"]
            pivot = build_pivot(ak, selected_date, whs)
            all_data[ak] = (pivot, whs)
        log_rekap(selected_date, scope)

    st.success(f"✅ Rekap selesai — **{len(keys_to_process)} laporan** | {selected_date}")
    st.divider()

    # ── Render per area_key, dikelompokkan per operator ────────────────────────
    for op in ALL_OPERATORS:
        op_keys = [k for k in keys_to_process if AREA_CONFIG[k]["operator"] == op]
        if not op_keys:
            continue

        bg = OP_BG.get(op, "#333")
        st.markdown(
            f'<div class="area-hdr" style="background:{bg}">🏢 {op}</div>',
            unsafe_allow_html=True
        )

        for ak in op_keys:
            pivot_df, whs = all_data[ak]
            area_label = AREA_CONFIG[ak]["area"]

            st.markdown(f"**{op} — {area_label}** ({len(whs)} WH)")

            # Coverage warning
            df_det = get_rekap_per_wh(ak, selected_date)
            reported = df_det["warehouse"].unique().tolist() if not df_det.empty else []
            missing  = [w for w in whs if w not in reported]
            if missing:
                st.warning(f"⚠️ {len(missing)} WH belum lapor: {', '.join(missing)}")

            render_pivot(pivot_df, whs, f"{op} {area_label}")

            if not pivot_df.empty:
                xlsx = export_rekap_area_excel(
                    pivot_df=pivot_df, detail_df=df_det,
                    area=f"{op} - {area_label}",
                    tanggal=selected_date, warehouses=whs
                )
                st.download_button(
                    label=f"⬇️ Export Excel — {op} {area_label}",
                    data=xlsx,
                    file_name=f"STOCK_NTE_{op}_{area_label}_{selected_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{ak}"
                )
            st.divider()

    # ── Grand Summary lintas semua ─────────────────────────────────────────────
    if scope == "Semua":
        st.markdown("### 🔢 Grand Summary — Semua Operator & Area")
        df_grand = get_grand_total(selected_date)
        if not df_grand.empty:
            gp = df_grand.pivot_table(
                index=["jenis_nte","type_nte","status_nte"],
                columns="operator", values="total_stock",
                aggfunc="sum", fill_value=0
            ).reset_index()
            gp.columns.name = None
            op_cols = [c for c in gp.columns if c not in ["jenis_nte","type_nte","status_nte"]]
            gp["GRAND TOTAL"] = gp[op_cols].sum(axis=1)
            gp = gp[gp["GRAND TOTAL"] > 0]
            gp.rename(columns={"jenis_nte":"JENIS 2","type_nte":"TYPE","status_nte":"STATUS"},
                      inplace=True)
            st.dataframe(gp, use_container_width=True, hide_index=True)

            total_all = int(gp["GRAND TOTAL"].sum())
            st.markdown(f"""
            <div class="grand-box">
                <div style="color:#F57F17;font-weight:600;font-size:.85rem;text-transform:uppercase">
                    Grand Total Semua Operator & Area
                </div>
                <div style="font-family:'Space Grotesk',sans-serif;font-size:2.8rem;font-weight:700;color:#1E3A5F">
                    {total_all:,}
                </div>
                <div style="color:#888;font-size:.9rem">unit NTE · {selected_date}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("👆 Klik **GENERATE REKAP SEKARANG** untuk memulai.")
