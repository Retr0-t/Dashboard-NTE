"""Page: Upload Excel"""
import streamlit as st
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.database import init_db, bulk_upsert_stok
from utils.export_utils import build_excel_template
from data.master_data import AREA_CONFIG, NTE_STATUS, ALL_NTE_TYPES
init_db()

st.set_page_config(page_title="Upload Excel | NTE Dashboard", page_icon="📤", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.page-header{background:linear-gradient(135deg,#1B5E20,#2E7D32);color:white;
  padding:1.5rem 2rem;border-radius:12px;margin-bottom:1.5rem}
.page-header h2{font-family:'Space Grotesk',sans-serif;margin:0;font-size:1.5rem}
.page-header p{margin:.25rem 0 0;opacity:.8;font-size:.9rem}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h2>📤 Upload Data Excel</h2>
    <p>Upload file Excel berisi data stok harian — bisa untuk banyak operator/warehouse sekaligus</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 📋 Langkah 1: Download Template")
st.info(
    "Kolom wajib: `tanggal` · `operator` · `area` · `area_key` · "
    "`warehouse` · `jenis_nte` · `type_nte` · `status_nte` · `closing_stock`\n\n"
    "Format tanggal: `YYYY-MM-DD`  |  Operator: `TELKOMSEL` / `TELKOM` / `TIF`"
)

col_dl, col_info = st.columns([1,2])
with col_dl:
    tpl = build_excel_template(list(AREA_CONFIG.keys()))
    st.download_button(
        "⬇️ Download Template Excel", data=tpl,
        file_name="template_input_stok_NTE.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True, type="primary"
    )
with col_info:
    st.markdown("""
    Template berisi:
    - **Sheet 'Template Input Stok'**: Contoh baris siap diisi
    - **Sheet 'Referensi'**: Daftar lengkap kombinasi operator/area/WH/NTE yang valid
    """)

st.divider()
st.markdown("### 📂 Langkah 2: Upload File")

uploaded = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx","xls"])
if uploaded:
    try:
        df_raw = pd.read_excel(uploaded, sheet_name=0)
        st.success(f"✅ File dibaca: **{len(df_raw)} baris**")

        required = {"tanggal","operator","area","area_key","warehouse",
                    "jenis_nte","type_nte","status_nte","closing_stock"}
        missing_cols = required - set(df_raw.columns.str.lower())
        if missing_cols:
            st.error(f"❌ Kolom tidak ditemukan: **{', '.join(missing_cols)}**"); st.stop()

        df_raw.columns = df_raw.columns.str.lower().str.strip()
        df = df_raw[list(required)].copy()
        df["closing_stock"] = pd.to_numeric(df["closing_stock"], errors="coerce").fillna(0).astype(int)
        df["tanggal"] = pd.to_datetime(df["tanggal"]).dt.strftime("%Y-%m-%d")

        st.dataframe(df.head(10), use_container_width=True, hide_index=True)
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Baris", len(df))
        c2.metric("Tanggal", df["tanggal"].nunique())
        c3.metric("Operator", df["operator"].nunique())

        unknown_op = set(df["operator"].unique()) - {"TELKOMSEL","TELKOM","TIF"}
        if unknown_op:
            st.warning(f"⚠️ Operator tidak dikenal: **{', '.join(unknown_op)}**")

        st.divider()
        st.markdown("### 💾 Langkah 3: Simpan ke Database")
        if st.button("⬆️ Upload & Simpan Semua Data", type="primary", use_container_width=True):
            with st.spinner("Menyimpan..."):
                ok, errors = bulk_upsert_stok(df)
            if errors:
                st.error(f"❌ {len(errors)} baris gagal:")
                for e in errors[:10]: st.code(e)
            if ok > 0:
                st.success(f"✅ **{ok} baris** berhasil disimpan!")
                st.balloons()
                summary = df.groupby(["operator","area","warehouse"])["closing_stock"].sum().reset_index()
                summary.columns = ["Operator","Area","Warehouse","Total Stok"]
                st.dataframe(summary, hide_index=True, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Gagal membaca file: {e}")
else:
    st.markdown("""
    <div style="text-align:center;padding:3rem;color:#9E9E9E;border:2px dashed #BDBDBD;border-radius:12px">
        <div style="font-size:3rem">📊</div>
        <div>Drag & drop file Excel di sini</div>
        <div style="font-size:.8rem;margin-top:.25rem">Format .xlsx · bisa berisi data banyak operator & warehouse sekaligus</div>
    </div>""", unsafe_allow_html=True)
