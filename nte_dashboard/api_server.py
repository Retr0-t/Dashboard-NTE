"""
api_server.py — FastAPI endpoint untuk WhatsApp Bot
Jalankan terpisah dari Streamlit:
  uvicorn api_server:app --host 0.0.0.0 --port 8502

Endpoint yang tersedia:
  GET  /health
  GET  /laporan?tanggal=YYYY-MM-DD&operator=X&area=Y   → PDF bytes
  GET  /laporan/jpg?tanggal=...&operator=X&area=Y       → JPG bytes
  GET  /laporan/semua?tanggal=YYYY-MM-DD               → ZIP semua PDF
  GET  /stok/ringkas?tanggal=YYYY-MM-DD                → JSON teks ringkas
  GET  /tanggal/tersedia                               → list tanggal ada data
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from datetime import date, datetime
from typing import Optional

from utils.database import (
    init_db, get_available_dates, get_stok,
    get_rekap_per_wh, get_grand_total
)
from utils.report_export import (
    generate_pdf, pdf_to_jpg, generate_all_pdf_zip
)
from data.master_data import (
    AREA_CONFIG, ALL_OPERATORS, ALL_AREAS,
    NTE_CATALOG_BY_OPERATOR, NTE_STATUS
)

init_db()
app = FastAPI(title="NTE Dashboard API", version="1.0.0")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _latest_date() -> str:
    dates = get_available_dates()
    return dates[0] if dates else str(date.today())

def _resolve_date(tanggal: Optional[str]) -> str:
    if not tanggal or tanggal.lower() in ("hari ini", "today", "latest"):
        return _latest_date()
    return tanggal

def _find_area_key(operator: str, area: str) -> Optional[str]:
    """Cari area_key dari operator + area (case-insensitive)."""
    for ak, cfg in AREA_CONFIG.items():
        if (cfg["operator"].upper() == operator.upper() and
                cfg["area"].upper() == area.upper()):
            return ak
    return None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    dates = get_available_dates()
    return {
        "status": "ok",
        "tanggal_terbaru": dates[0] if dates else None,
        "total_tanggal": len(dates),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/tanggal/tersedia")
def tanggal_tersedia():
    return {"tanggal": get_available_dates()}


@app.get("/laporan")
def laporan_pdf(
    tanggal:  Optional[str] = Query(None, description="YYYY-MM-DD atau 'hari ini'"),
    operator: str           = Query(...,  description="TELKOMSEL / TELKOM / TIF"),
    area:     str           = Query(...,  description="BANDUNG / SOREANG"),
):
    """Generate PDF laporan harian 1 operator-area."""
    tgl      = _resolve_date(tanggal)
    area_key = _find_area_key(operator, area)
    if not area_key:
        raise HTTPException(404, f"Kombinasi operator={operator} area={area} tidak ditemukan.")

    cfg     = AREA_CONFIG[area_key]
    df_raw  = get_rekap_per_wh(area_key, tgl)
    catalog = NTE_CATALOG_BY_OPERATOR.get(operator.upper(), {})

    if df_raw.empty:
        raise HTTPException(404, f"Tidak ada data stok untuk {operator} {area} pada {tgl}.")

    pdf = generate_pdf(
        df_raw=df_raw, warehouses=cfg["warehouses"],
        catalog=catalog, nte_status=NTE_STATUS,
        operator=operator.upper(), area=area.upper(), tanggal=tgl,
    )
    fname = f"STOCK_NTE_{operator.upper()}_{area.upper()}_{tgl}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/laporan/jpg")
def laporan_jpg(
    tanggal:  Optional[str] = Query(None),
    operator: str           = Query(...),
    area:     str           = Query(...),
    dpi:      int           = Query(150, ge=72, le=300),
):
    """Generate JPG laporan harian 1 operator-area."""
    tgl      = _resolve_date(tanggal)
    area_key = _find_area_key(operator, area)
    if not area_key:
        raise HTTPException(404, f"Kombinasi operator={operator} area={area} tidak ditemukan.")

    cfg     = AREA_CONFIG[area_key]
    df_raw  = get_rekap_per_wh(area_key, tgl)
    catalog = NTE_CATALOG_BY_OPERATOR.get(operator.upper(), {})

    if df_raw.empty:
        raise HTTPException(404, f"Tidak ada data stok untuk {operator} {area} pada {tgl}.")

    pdf = generate_pdf(
        df_raw=df_raw, warehouses=cfg["warehouses"],
        catalog=catalog, nte_status=NTE_STATUS,
        operator=operator.upper(), area=area.upper(), tanggal=tgl,
    )
    jpg   = pdf_to_jpg(pdf, dpi=dpi)
    fname = f"STOCK_NTE_{operator.upper()}_{area.upper()}_{tgl}.jpg"
    return Response(
        content=jpg,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/laporan/semua")
def laporan_semua(
    tanggal:  Optional[str] = Query(None),
    operator: Optional[str] = Query(None, description="Filter operator (opsional)"),
    format:   str           = Query("zip", description="zip = ZIP berisi semua PDF"),
):
    """Generate ZIP berisi semua PDF untuk semua atau 1 operator."""
    tgl   = _resolve_date(tanggal)
    scope = operator.upper() if operator else "Semua"

    zip_bytes = generate_all_pdf_zip(
        data_fn     = lambda ak, t: get_rekap_per_wh(ak, t),
        area_config = AREA_CONFIG,
        catalog_fn  = lambda op: NTE_CATALOG_BY_OPERATOR.get(op, {}),
        nte_status  = NTE_STATUS,
        tanggal     = tgl,
        scope       = scope,
    )
    fname = f"STOCK_NTE_SEMUA_{tgl}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.get("/stok/ringkas")
def stok_ringkas(
    tanggal:  Optional[str] = Query(None),
    operator: Optional[str] = Query(None),
    area:     Optional[str] = Query(None),
):
    """Ringkasan teks stok — untuk balasan teks WhatsApp."""
    tgl     = _resolve_date(tanggal)
    df_all  = get_stok(tgl,
                       operator=operator.upper() if operator else None,
                       area=area.upper() if area else None)
    if df_all.empty:
        return JSONResponse({"tgl": tgl, "pesan": f"Tidak ada data stok pada {tgl}.", "data": []})

    summary = (
        df_all.groupby(["operator","area","jenis_nte"])["closing_stock"]
        .sum().reset_index()
        .rename(columns={"closing_stock":"total"})
        .sort_values(["operator","area","total"], ascending=[True,True,False])
    )

    # Format teks ringkas
    lines = [f"📦 *RINGKASAN STOK NTE*", f"📅 {tgl}", ""]
    cur_op = cur_area = None
    for _, r in summary.iterrows():
        if r["operator"] != cur_op:
            cur_op = r["operator"]
            lines.append(f"*{cur_op}*")
        if r["area"] != cur_area:
            cur_area = r["area"]
            lines.append(f"  📍 _{cur_area}_")
        lines.append(f"    • {r['jenis_nte']}: {int(r['total']):,} unit")

    grand = int(df_all["closing_stock"].sum())
    lines += ["", f"🔢 *Grand Total: {grand:,} unit*"]

    return JSONResponse({
        "tgl": tgl,
        "pesan": "\n".join(lines),
        "grand_total": grand,
        "data": summary.to_dict(orient="records"),
    })
