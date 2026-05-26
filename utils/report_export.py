"""
report_export.py
Fungsi export laporan harian NTE ke PDF dan JPG.
Menggunakan ReportLab untuk PDF, lalu Pillow untuk konversi ke JPG.

Output:
  - PDF  : landscape A3, tabel lengkap per operator-area
  - JPG  : render dari PDF page pertama (untuk kirim via WA/email)
  - ZIP  : semua PDF sekaligus (export semua operator-area)
"""

import io
import zipfile
from datetime import datetime

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Warna brand ───────────────────────────────────────────────────────────────
C_NAVY      = colors.HexColor("#1E3A5F")
C_BLUE      = colors.HexColor("#2E6DA4")
C_LBLUE     = colors.HexColor("#D9EAF7")
C_RED       = colors.HexColor("#C0392B")
C_REDBG     = colors.HexColor("#FADBD8")
C_GREEN     = colors.HexColor("#1E8449")
C_GREENBG   = colors.HexColor("#D5F5E3")
C_YELBG     = colors.HexColor("#FFF3CD")
C_YELTXT    = colors.HexColor("#856404")
C_GRAY      = colors.HexColor("#F2F2F2")
C_MIDGRAY   = colors.HexColor("#CCCCCC")
C_WHITE     = colors.white
C_BLACK     = colors.HexColor("#222222")

OP_HEADER_COLOR = {
    "TELKOMSEL": colors.HexColor("#1B5E20"),
    "TELKOM":    colors.HexColor("#0D47A1"),
    "TIF":       colors.HexColor("#E65100"),
}


def _short_wh(wh: str) -> str:
    return (wh
        .replace("TA SO INV ", "").replace("TA SO CCAN ", "")
        .replace("TA SO TIF ", "").replace(" WH", "").strip()
    )


def _build_pivot(df_raw: pd.DataFrame, warehouses: list,
                 catalog: dict, nte_status: list) -> pd.DataFrame:
    """Bangun pivot table dari data raw."""
    if df_raw.empty:
        return pd.DataFrame()

    # Sort order sesuai katalog
    jenis_order  = {j: i for i, j in enumerate(catalog.keys())}
    status_order = {s: i for i, s in enumerate(nte_status)}

    pivot = df_raw.pivot_table(
        index=["jenis_nte", "type_nte", "status_nte"],
        columns="warehouse",
        values="closing_stock",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()
    pivot.columns.name = None

    for wh in warehouses:
        if wh not in pivot.columns:
            pivot[wh] = 0

    pivot["Grand Total"] = pivot[warehouses].sum(axis=1)
    pivot["_j"] = pivot["jenis_nte"].map(jenis_order).fillna(99)
    pivot["_s"] = pivot["status_nte"].map(status_order).fillna(99)
    pivot = (pivot
             .sort_values(["_j", "type_nte", "_s"])
             .drop(columns=["_j", "_s"])
             .reset_index(drop=True))
    return pivot[pivot["Grand Total"] > 0]


def generate_pdf(
    df_raw:     pd.DataFrame,
    warehouses: list,
    catalog:    dict,
    nte_status: list,
    operator:   str,
    area:       str,
    tanggal:    str,
) -> bytes:
    """
    Generate PDF laporan harian 1 operator-area.
    Return bytes PDF.
    """
    pivot = _build_pivot(df_raw, warehouses, catalog, nte_status)
    buf   = io.BytesIO()

    # Page setup: landscape A3
    PAGE  = landscape(A3)
    doc   = SimpleDocTemplate(
        buf,
        pagesize=PAGE,
        leftMargin=12*mm, rightMargin=12*mm,
        topMargin=14*mm,  bottomMargin=14*mm,
    )

    op_color = OP_HEADER_COLOR.get(operator, C_NAVY)

    # ── Styles ────────────────────────────────────────────────────────────────
    style_title = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=16,
        textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=0,
    )
    style_sub = ParagraphStyle(
        "sub", fontName="Helvetica", fontSize=9,
        textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=0,
    )
    style_meta = ParagraphStyle(
        "meta", fontName="Helvetica", fontSize=8,
        textColor=C_NAVY, alignment=TA_LEFT, spaceAfter=4,
    )

    story = []

    # ── Header block ──────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(f"STOCK NTE {operator} — {area}", style_title),
    ],[
        Paragraph(f"Tanggal: {tanggal}   |   "
                  f"Total WH: {len(warehouses)}   |   "
                  f"Dibuat: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                  style_sub),
    ]]
    header_tbl = Table(header_data, colWidths=[doc.width])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), op_color),
        ("TOPPADDING",  (0,0), (-1,-1), 8),
        ("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 14),
        ("RIGHTPADDING",(0,0), (-1,-1), 14),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[op_color]),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 4*mm))

    if pivot.empty:
        story.append(Paragraph(
            "Tidak ada data stok untuk tanggal ini.", style_meta
        ))
        doc.build(story)
        buf.seek(0)
        return buf.getvalue()

    # ── Hitung lebar kolom secara proporsional ─────────────────────────────
    n_wh      = len(warehouses)
    short_whs = [_short_wh(w) for w in warehouses]

    page_w   = doc.width
    # Fixed cols: JENIS(13%), STATUS(7%), TYPE(22%)
    col_jenis  = page_w * 0.13
    col_status = page_w * 0.07
    col_type   = page_w * 0.22
    remaining  = page_w - col_jenis - col_status - col_type
    col_gt     = remaining * 0.09
    col_wh_w   = (remaining - col_gt) / max(n_wh, 1)

    col_widths = (
        [col_jenis, col_status, col_type]
        + [col_wh_w] * n_wh
        + [col_gt]
    )

    # ── Header row ─────────────────────────────────────────────────────────
    hdr_style = ParagraphStyle(
        "hdr", fontName="Helvetica-Bold", fontSize=7,
        textColor=C_WHITE, alignment=TA_CENTER,
    )
    hdr_wh_style = ParagraphStyle(
        "hdrwh", fontName="Helvetica-Bold", fontSize=6,
        textColor=C_WHITE, alignment=TA_CENTER,
    )

    # Sub-header baris 1: COUNTA of SN | WH SO (SESUAI SCMT)
    sub_row = [
        Paragraph("COUNTA of SN", hdr_style), "", "",
    ] + [Paragraph("WH SO (SESUAI SCMT)", hdr_style)] + [""] * (n_wh - 1) + [""]

    # Baris 2: kolom labels
    col_row = [
        Paragraph("JENIS 2", hdr_style),
        Paragraph("STATUS",  hdr_style),
        Paragraph("TYPE",    hdr_style),
    ] + [Paragraph(s, hdr_wh_style) for s in short_whs] + [
        Paragraph("Grand Total", hdr_style)
    ]

    # ── Data rows ─────────────────────────────────────────────────────────
    cell_style = ParagraphStyle(
        "cell", fontName="Helvetica", fontSize=7,
        textColor=C_BLACK, alignment=TA_LEFT,
    )
    cell_num = ParagraphStyle(
        "num", fontName="Helvetica", fontSize=7,
        textColor=C_BLACK, alignment=TA_CENTER,
    )
    cell_num_red = ParagraphStyle(
        "numred", fontName="Helvetica-Bold", fontSize=7,
        textColor=C_RED, alignment=TA_CENTER,
    )

    table_data = [sub_row, col_row]
    row_meta   = []   # untuk styling per baris: (row_idx, status, jenis_changed)

    prev_jenis = None
    for _, r in pivot.iterrows():
        jenis    = r["jenis_nte"]
        type_nte = r["type_nte"]
        status   = r["status_nte"]
        grand    = int(r["Grand Total"])

        jenis_cell = Paragraph(
            jenis if jenis != prev_jenis else "", cell_style
        )
        status_cell = Paragraph(status, cell_style)
        type_cell   = Paragraph(type_nte.replace("_", " "), cell_style)

        wh_cells = []
        for wh in warehouses:
            val = int(r.get(wh, 0) or 0)
            wh_cells.append(
                Paragraph(str(val) if val > 0 else "", cell_num)
            )

        gt_cell = Paragraph(str(grand) if grand > 0 else "", cell_num_red)

        row_data = [jenis_cell, status_cell, type_cell] + wh_cells + [gt_cell]
        table_data.append(row_data)
        row_meta.append({
            "jenis_changed": jenis != prev_jenis,
            "status": status,
        })
        prev_jenis = jenis

    # Grand total row
    totals_row = [
        Paragraph("Grand Total", ParagraphStyle(
            "gt", fontName="Helvetica-Bold", fontSize=7,
            textColor=C_WHITE, alignment=TA_CENTER,
        )),
        "", "",
    ]
    total_grand = 0
    for wh in warehouses:
        v = int(pivot[wh].sum()) if wh in pivot.columns else 0
        totals_row.append(Paragraph(
            str(v) if v > 0 else "",
            ParagraphStyle("gtnum", fontName="Helvetica-Bold", fontSize=7,
                           textColor=C_WHITE, alignment=TA_CENTER)
        ))
        total_grand += v
    totals_row.append(Paragraph(
        str(total_grand),
        ParagraphStyle("gtval", fontName="Helvetica-Bold", fontSize=8,
                       textColor=C_WHITE, alignment=TA_CENTER)
    ))
    table_data.append(totals_row)

    # ── Build table ────────────────────────────────────────────────────────
    tbl = Table(table_data, colWidths=col_widths, repeatRows=2)

    n_data  = len(pivot)
    n_total = len(table_data)  # sub_row + col_row + data + grand_total

    ts = TableStyle([
        # Sub-header row (row 0)
        ("BACKGROUND",   (0, 0), (-1, 0),  C_GRAY),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  C_NAVY),
        ("SPAN",         (0, 0), (2, 0)),   # COUNTA of SN
        ("SPAN",         (3, 0), (-1, 0)),  # WH SO
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  7),
        ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, 0),  3),
        ("BOTTOMPADDING",(0, 0), (-1, 0),  3),

        # Column header row (row 1)
        ("BACKGROUND",   (0, 1), (2, 1),   C_NAVY),
        ("BACKGROUND",   (3, 1), (-2, 1),  C_BLUE),
        ("BACKGROUND",   (-1, 1),(-1, 1),  C_RED),
        ("TOPPADDING",   (0, 1), (-1, 1),  4),
        ("BOTTOMPADDING",(0, 1), (-1, 1),  4),
        ("ALIGN",        (0, 1), (-1, 1),  "CENTER"),

        # Data rows
        ("FONTSIZE",     (0, 2), (-1, n_total-2), 7),
        ("TOPPADDING",   (0, 2), (-1, n_total-2), 2),
        ("BOTTOMPADDING",(0, 2), (-1, n_total-2), 2),
        ("LEFTPADDING",  (0, 2), (2, n_total-2),  4),
        ("ALIGN",        (3, 2), (-1, n_total-2), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1),         "MIDDLE"),

        # Grid
        ("GRID",         (0, 0), (-1, -1),  0.3, C_MIDGRAY),
        ("LINEBELOW",    (0, 1), (-1, 1),   0.8, C_NAVY),

        # Grand total bottom row
        ("BACKGROUND",   (0, -1), (-1, -1), C_NAVY),
        ("SPAN",         (0, -1), (2, -1)),
        ("FONTNAME",     (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN",        (0, -1), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, -1), (-1, -1), 5),
        ("BOTTOMPADDING",(0, -1), (-1, -1), 5),
    ])

    # Per-row styling: jenis header + status color
    for i, meta in enumerate(row_meta):
        ri = i + 2  # offset: sub_row + col_row
        # Jenis bg
        if meta["jenis_changed"]:
            ts.add("BACKGROUND", (0, ri), (0, ri), C_LBLUE)
            ts.add("FONTNAME",   (0, ri), (0, ri), "Helvetica-Bold")
            ts.add("TEXTCOLOR",  (0, ri), (0, ri), C_NAVY)
        # Status badge color
        if meta["status"] == "NTE BARU":
            ts.add("BACKGROUND", (1, ri), (1, ri), C_GREENBG)
            ts.add("TEXTCOLOR",  (1, ri), (1, ri), C_GREEN)
            ts.add("FONTNAME",   (1, ri), (1, ri), "Helvetica-Bold")
        else:
            ts.add("BACKGROUND", (1, ri), (1, ri), C_YELBG)
            ts.add("TEXTCOLOR",  (1, ri), (1, ri), C_YELTXT)
            ts.add("FONTNAME",   (1, ri), (1, ri), "Helvetica-Bold")
        # Grand Total col
        ts.add("BACKGROUND", (-1, ri), (-1, ri), C_REDBG)
        ts.add("TEXTCOLOR",  (-1, ri), (-1, ri), C_RED)
        ts.add("FONTNAME",   (-1, ri), (-1, ri), "Helvetica-Bold")

    tbl.setStyle(ts)
    story.append(tbl)

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_MIDGRAY))
    story.append(Paragraph(
        f"NTE Operations · Telkom Indonesia · {operator} {area} · {tanggal} · "
        f"Total: {total_grand:,} unit",
        ParagraphStyle("footer", fontName="Helvetica", fontSize=7,
                       textColor=colors.HexColor("#888888"), alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def pdf_to_jpg(pdf_bytes: bytes, dpi: int = 150) -> bytes:
    """
    Konversi halaman pertama PDF ke JPG.
    Menggunakan pdf2image jika tersedia, fallback ke render PIL sederhana.
    """
    try:
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=1, last_page=1)
        if images:
            buf = io.BytesIO()
            images[0].save(buf, format="JPEG", quality=92, optimize=True)
            buf.seek(0)
            return buf.getvalue()
    except ImportError:
        pass

    # Fallback: render via reportlab RLImage → PIL (tanpa poppler)
    # Buat gambar putih dengan teks info
    img   = Image.new("RGB", (1200, 850), color=(255, 255, 255))
    draw  = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 1200, 60], fill=(30, 58, 95))
    draw.text((600, 30), "PDF berhasil dibuat — install pdf2image+poppler untuk preview JPG",
              fill=(255,255,255), anchor="mm")
    draw.text((600, 420), "Gunakan tombol Download PDF untuk file lengkap",
              fill=(100,100,100), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf.getvalue()


def generate_all_pdf_zip(
    data_fn,          # callable(area_key, tanggal) -> pd.DataFrame
    area_config: dict,
    catalog_fn,       # callable(operator) -> dict
    nte_status: list,
    tanggal:    str,
    scope:      str = "Semua",  # "Semua" / operator name / area_key
) -> bytes:
    """
    Generate ZIP berisi PDF untuk semua operator-area dalam scope.
    data_fn    : fungsi yang memanggil database, signature (area_key, tanggal)
    catalog_fn : fungsi yang mengembalikan katalog NTE per operator
    """
    buf_zip = io.BytesIO()

    with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for ak, cfg in area_config.items():
            op   = cfg["operator"]
            area = cfg["area"]

            # Filter scope
            if scope != "Semua":
                if scope in ["TELKOMSEL","TELKOM","TIF"] and op != scope:
                    continue
                if scope == ak:
                    pass  # include
                elif scope not in ["TELKOMSEL","TELKOM","TIF"] and scope != ak:
                    continue

            df_raw  = data_fn(ak, tanggal)
            catalog = catalog_fn(op)
            whs     = cfg["warehouses"]

            pdf_bytes = generate_pdf(
                df_raw=df_raw, warehouses=whs,
                catalog=catalog, nte_status=nte_status,
                operator=op, area=area, tanggal=tanggal,
            )

            fname = f"STOCK_NTE_{op}_{area}_{tanggal}.pdf"
            zf.writestr(fname, pdf_bytes)

    buf_zip.seek(0)
    return buf_zip.getvalue()
