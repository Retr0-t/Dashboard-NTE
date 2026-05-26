"""
Page: Export Laporan — PDF & JPG
Export laporan harian per operator-area ke PDF atau JPG.
Bisa export satu per satu atau semua sekaligus (ZIP).
"""

import streamlit as st
import pandas as pd
import sys, os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.database import init_db, get_available_dates, get_rekap_per_wh, get_wh_coverage
from utils.report_export import generate_pdf, pdf_to_jpg, generate_all_pdf_zip
from data.master_data import (
    AREA_CONFIG, ALL_OPERATORS, ALL_AREAS,
    NTE_CATALOG_BY_OPERATOR, NTE_STATUS,
)

init_db()

st.set_page_config(
    page_title="Export Laporan | NTE Dashboard",
    page_icon="📄",
    layout="wide",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.page-header{
    background:linear-gradient(135deg,#4A0E0E,#C0392B);
    color:white;padding:1.5rem 2rem;border-radius:12px;margin-bottom:1.5rem;
}
.page-header h2{font-family:'Space Grotesk',sans-serif;margin:0;font-size:1.5rem}
.page-header p{margin:.25rem 0 0;opacity:.8;font-size:.9rem}

.export-card{
    background:white;border:1px solid #E0EAF5;border-radius:12px;
    padding:1.25rem 1.5rem;margin-bottom:.75rem;
    box-shadow:0 2px 8px rgba(0,0,0,.05);
    transition:box-shadow .2s;
}
.export-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1)}

.op-tag{display:inline-block;padding:2px 10px;border-radius:20px;
  font-size:.75rem;font-weight:600;margin-right:6px}
.op-telkomsel{background:#E8F5E9;color:#1B5E20}
.op-telkom   {background:#E3F2FD;color:#0D47A1}
.op-tif      {background:#FFF3E0;color:#E65100}

.preview-frame{
    background:#F8F9FA;border:1px solid #DEE2E6;
    border-radius:8px;padding:.5rem;margin-top:.5rem;
    text-align:center;
}

.stat-chip{display:inline-block;background:#EBF5FF;border:1px solid #BDE0FF;
  border-radius:20px;padding:2px 10px;font-size:.78rem;color:#0D47A1;margin:2px}
</style>
""", unsafe_allow_html=True)

OP_TAG = {
    "TELKOMSEL": '<span class="op-tag op-telkomsel">TELKOMSEL</span>',
    "TELKOM":    '<span class="op-tag op-telkom">TELKOM</span>',
    "TIF":       '<span class="op-tag op-tif">TIF</span>',
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📄 Opsi Export")
    avail = get_available_dates()
    if not avail:
        st.warning("Belum ada data.")
        st.stop()

    sel_date = st.selectbox("📅 Tanggal", avail)
    st.divider()
    st.markdown("**Kualitas JPG**")
    jpg_dpi = st.select_slider(
        "DPI (resolusi)",
        options=[72, 96, 120, 150, 200],
        value=150,
        help="Lebih tinggi = gambar lebih tajam, ukuran file lebih besar",
    )
    st.divider()
    st.caption("PDF: format landscape A3, siap cetak")
    st.caption("JPG: untuk kirim via WA / email")
    st.caption("ZIP: semua laporan sekaligus")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <h2>📄 Export Laporan Harian</h2>
    <p>Download laporan stok NTE dalam format PDF atau JPG · per operator-area atau semua sekaligus</p>
</div>
""", unsafe_allow_html=True)

# ── Coverage check ─────────────────────────────────────────────────────────────
df_cov = get_wh_coverage(sel_date)
reported_keys = set()
if not df_cov.empty:
    reported_keys = set(df_cov["area_key"].tolist())

total_keys    = len(AREA_CONFIG)
reported_cnt  = sum(1 for ak in AREA_CONFIG if ak in reported_keys)

st.markdown(
    f'📊 <span class="stat-chip">📅 {sel_date}</span>'
    f'<span class="stat-chip">✅ {reported_cnt}/{total_keys} kombinasi ada data</span>',
    unsafe_allow_html=True
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT SEMUA — 1 KLIK
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### ⚡ Export Semua Sekaligus")

c_all1, c_all2 = st.columns([2,3])
with c_all1:
    scope_all = st.selectbox(
        "Scope export",
        ["Semua Operator & Area"] + ALL_OPERATORS + list(AREA_CONFIG.keys()),
        key="scope_all"
    )

scope_val = "Semua" if scope_all == "Semua Operator & Area" else scope_all

with c_all2:
    if st.button("📦 Generate ZIP (semua PDF)", type="primary", use_container_width=True):
        with st.spinner("Membuat semua PDF..."):
            zip_bytes = generate_all_pdf_zip(
                data_fn      = lambda ak, tgl: get_rekap_per_wh(ak, tgl),
                area_config  = AREA_CONFIG,
                catalog_fn   = lambda op: NTE_CATALOG_BY_OPERATOR.get(op, {}),
                nte_status   = NTE_STATUS,
                tanggal      = sel_date,
                scope        = scope_val,
            )
        st.success("✅ ZIP siap didownload!")
        st.download_button(
            label     = f"⬇️ Download ZIP — {scope_all} ({sel_date})",
            data      = zip_bytes,
            file_name = f"STOCK_NTE_ALL_{sel_date.replace('-','')}.zip",
            mime      = "application/zip",
            use_container_width=True,
        )

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT PER OPERATOR-AREA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 📋 Export Per Operator-Area")

for op in ALL_OPERATORS:
    op_keys = [k for k,v in AREA_CONFIG.items() if v["operator"] == op]
    if not op_keys:
        continue

    st.markdown(f"#### {OP_TAG[op]}", unsafe_allow_html=True)
    cols = st.columns(len(op_keys))

    for ci, ak in enumerate(op_keys):
        cfg  = AREA_CONFIG[ak]
        area = cfg["area"]
        whs  = cfg["warehouses"]
        has_data = ak in reported_keys

        with cols[ci]:
            # Card header
            st.markdown(f"""
            <div class="export-card">
                <div style="font-weight:700;color:#1E3A5F;font-size:.95rem">
                    📍 {area}
                </div>
                <div style="font-size:.78rem;color:#888;margin-top:.15rem">
                    {len(whs)} warehouse ·
                    {'✅ ada data' if has_data else '⚠️ belum ada data'}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not has_data:
                st.caption("Tidak ada data untuk di-export.")
                continue

            # Load data
            df_raw  = get_rekap_per_wh(ak, sel_date)
            catalog = NTE_CATALOG_BY_OPERATOR.get(op, {})

            # Hitung ringkasan
            total_unit = int(df_raw["closing_stock"].sum()) if not df_raw.empty else 0
            n_types    = df_raw["type_nte"].nunique() if not df_raw.empty else 0
            st.markdown(
                f'<span class="stat-chip">📦 {total_unit:,} unit</span>'
                f'<span class="stat-chip">🔢 {n_types} type</span>',
                unsafe_allow_html=True
            )

            # Generate PDF
            pdf_bytes = generate_pdf(
                df_raw=df_raw, warehouses=whs,
                catalog=catalog, nte_status=NTE_STATUS,
                operator=op, area=area, tanggal=sel_date,
            )
            fname_base = f"STOCK_NTE_{op}_{area}_{sel_date}"

            # ── Download PDF ─────────────────────────────────────────────
            st.download_button(
                label         = "⬇️ Download PDF",
                data          = pdf_bytes,
                file_name     = f"{fname_base}.pdf",
                mime          = "application/pdf",
                use_container_width=True,
                key           = f"pdf_{ak}",
            )

            # ── Download JPG ─────────────────────────────────────────────
            if st.button(
                "🖼️ Generate & Download JPG",
                use_container_width=True,
                key=f"jpg_btn_{ak}"
            ):
                with st.spinner("Mengkonversi ke JPG..."):
                    jpg_bytes = pdf_to_jpg(pdf_bytes, dpi=jpg_dpi)
                st.download_button(
                    label         = "⬇️ Download JPG",
                    data          = jpg_bytes,
                    file_name     = f"{fname_base}.jpg",
                    mime          = "image/jpeg",
                    use_container_width=True,
                    key           = f"jpg_dl_{ak}",
                )

            # ── Preview JPG (thumbnail) ───────────────────────────────────
            with st.expander("👁️ Preview", expanded=False):
                with st.spinner("Membuat preview..."):
                    jpg_prev = pdf_to_jpg(pdf_bytes, dpi=96)
                st.image(jpg_prev, use_container_width=True,
                         caption=f"{op} {area} — {sel_date}")

    st.divider()

# ── Tips ───────────────────────────────────────────────────────────────────────
with st.expander("💡 Tips penggunaan export"):
    st.markdown("""
    **PDF (landscape A3):**
    - Siap cetak, format profesional dengan header warna per operator
    - Heat map warna pada sel (hijau = stok banyak, merah = sedikit)
    - Footer otomatis dengan total unit dan timestamp

    **JPG:**
    - Cocok untuk dikirim via WhatsApp atau email
    - Resolusi 150 DPI sudah cukup untuk layar; naikkan ke 200 DPI untuk cetak
    - Membutuhkan library `pdf2image` + `poppler` untuk hasil terbaik
    - Untuk install poppler: `sudo apt install poppler-utils` (Linux/Server)

    **ZIP (semua sekaligus):**
    - Berisi semua PDF dalam 1 file ZIP
    - Cocok untuk arsip harian atau distribusi ke atasan
    - Bisa filter per operator saja atau semua area

    **Install pdf2image untuk preview JPG yang lebih baik:**
    ```bash
    pip install pdf2image
    sudo apt install poppler-utils  # Linux
    # atau: brew install poppler   # Mac
    ```
    """)
