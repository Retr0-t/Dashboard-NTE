"""
Export ke Excel — format sesuai laporan STOCK NTE TELKOM
Header: COUNTA of SN | WH SO (SESUAI SCMT)
Kolom : JENIS 2 | STATUS | TYPE | [WH...] | Grand Total
"""

import pandas as pd
import io
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

# ── Warna ─────────────────────────────────────────────────────────────────────
NAVY      = "1E3A5F"
BLUE      = "2E6DA4"
LIGHT_BL  = "D9EAF7"
RED_SOFT  = "C0392B"
RED_BG    = "FADBD8"
GREEN_BG  = "D5F5E3"
GREEN_TXT = "1E8449"
YEL_BG    = "FFF3CD"
YEL_TXT   = "856404"
GRAY_BG   = "F2F2F2"
WHITE     = "FFFFFF"
MID_GRAY  = "CCCCCC"

def _thin(color=MID_GRAY):
    s = Side(style="thin", color=color)
    return Border(left=s, right=s, top=s, bottom=s)

def _hdr(cell, bg=NAVY, fg=WHITE, bold=True, size=10, align="center"):
    cell.fill      = PatternFill("solid", fgColor=bg)
    cell.font      = Font(color=fg, bold=bold, size=size, name="Arial")
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
    cell.border    = _thin()

def _cell(cell, align="center", bg=None, bold=False, color="000000", size=10):
    cell.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
    cell.border    = _thin()
    cell.font      = Font(bold=bold, color=color, size=size, name="Arial")
    if bg:
        cell.fill = PatternFill("solid", fgColor=bg)


def export_rekap_area_excel(pivot_df: pd.DataFrame, detail_df: pd.DataFrame,
                             area: str, tanggal: str, warehouses: list) -> bytes:
    """
    Export rekap area ke Excel.
    Format mengikuti laporan asli STOCK NTE TELKOM.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = area[:28]

    # ── Baris 1-2: Title ─────────────────────────────────────────────────────
    n_cols = 3 + len(warehouses) + 1   # JENIS2 + STATUS + TYPE + WHs + GrandTotal
    last_col = get_column_letter(n_cols)

    ws.merge_cells(f"A1:{last_col}1")
    ws["A1"] = f"STOCK NTE {area.upper()}"
    ws["A1"].font      = Font(bold=True, size=14, color=NAVY, name="Arial")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws["A1"].fill      = PatternFill("solid", fgColor=LIGHT_BL)
    ws.row_dimensions[1].height = 28

    ws.merge_cells(f"A2:{last_col}2")
    ws["A2"] = f"Tanggal: {tanggal}"
    ws["A2"].font      = Font(italic=True, size=10, color="555555", name="Arial")
    ws["A2"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[2].height = 16

    # ── Baris 3: Sub-header area WH ──────────────────────────────────────────
    ws.merge_cells(f"A3:C3")
    ws["A3"] = "COUNTA of SN"
    _hdr(ws["A3"], bg=GRAY_BG, fg=NAVY, size=9)

    ws.merge_cells(f"D3:{last_col}3")
    ws.cell(3, 4).value = "WH SO (SESUAI SCMT)"
    _hdr(ws.cell(3, 4), bg=GRAY_BG, fg=NAVY, size=9)
    ws.row_dimensions[3].height = 16

    # ── Baris 4: Header kolom ─────────────────────────────────────────────────
    headers = ["JENIS 2", "STATUS", "TYPE"] + warehouses + ["Grand Total"]
    for ci, h in enumerate(headers, 1):
        cell = ws.cell(4, ci, value=h)
        if ci <= 3:
            _hdr(cell, bg=NAVY, size=9)
        elif ci == len(headers):
            _hdr(cell, bg=RED_SOFT, size=9)
        else:
            _hdr(cell, bg=BLUE, size=9)
        # Lebar kolom
        if ci == 1:
            ws.column_dimensions[get_column_letter(ci)].width = 18
        elif ci == 2:
            ws.column_dimensions[get_column_letter(ci)].width = 12
        elif ci == 3:
            ws.column_dimensions[get_column_letter(ci)].width = 32
        else:
            ws.column_dimensions[get_column_letter(ci)].width = 10
    ws.row_dimensions[4].height = 36

    # ── Data rows ─────────────────────────────────────────────────────────────
    ROW_START = 5
    ri = ROW_START
    prev_jenis = None

    for _, r in pivot_df.iterrows():
        jenis  = r.get("jenis_nte", "")
        type_  = r.get("type_nte", "")
        status = r.get("status_nte", "")
        grand  = int(r.get("Grand Total", 0))

        # JENIS 2 — tampilkan hanya saat ganti jenis
        jenis_val = jenis if jenis != prev_jenis else ""
        jc = ws.cell(ri, 1, value=jenis_val)
        _cell(jc, align="left", bg="EAF3FB", bold=bool(jenis_val), color=NAVY, size=9)

        # STATUS
        sc = ws.cell(ri, 2, value=status)
        if status == "NTE BARU":
            _cell(sc, bg=GREEN_BG, color=GREEN_TXT, bold=True, size=9)
        else:
            _cell(sc, bg=YEL_BG, color=YEL_TXT, bold=True, size=9)

        # TYPE
        tc = ws.cell(ri, 3, value=type_)
        _cell(tc, align="left", size=9)

        # Per WH
        for wi, wh in enumerate(warehouses, 4):
            val = int(r.get(wh, 0) or 0)
            c = ws.cell(ri, wi, value=val if val > 0 else None)
            bg_wh = "F7FBFF" if val > 0 else WHITE
            _cell(c, bg=bg_wh, color=("333333" if val > 0 else MID_GRAY), size=9)

        # Grand Total
        gtc = ws.cell(ri, n_cols, value=grand if grand > 0 else None)
        _cell(gtc, bg=RED_BG, color=RED_SOFT, bold=True, size=10)

        prev_jenis = jenis
        ri += 1

    # ── Grand Total row ───────────────────────────────────────────────────────
    ws.merge_cells(f"A{ri}:C{ri}")
    gc = ws.cell(ri, 1, value="Grand Total")
    _hdr(gc, bg=NAVY, size=10, align="center")

    for wi in range(4, n_cols):
        cl = get_column_letter(wi)
        c = ws.cell(ri, wi, value=f"=SUM({cl}{ROW_START}:{cl}{ri-1})")
        _hdr(c, bg=BLUE, size=9)

    gt_col = get_column_letter(n_cols)
    gt_c = ws.cell(ri, n_cols, value=f"=SUM({gt_col}{ROW_START}:{gt_col}{ri-1})")
    _hdr(gt_c, bg=RED_SOFT, size=11)
    ws.row_dimensions[ri].height = 20

    # Freeze
    ws.freeze_panes = f"D5"

    # ── Sheet 2: Detail ────────────────────────────────────────────────────────
    if not detail_df.empty:
        ws2 = wb.create_sheet("Data Detail")
        for r2i, row in enumerate(dataframe_to_rows(detail_df, index=False, header=True), 1):
            for c2i, val in enumerate(row, 1):
                cell = ws2.cell(r2i, c2i, value=val)
                if r2i == 1:
                    _hdr(cell, size=9)
                else:
                    _cell(cell, align="left", size=9)
        for ci2 in range(1, len(detail_df.columns)+1):
            ws2.column_dimensions[get_column_letter(ci2)].width = 22

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def build_excel_template(warehouses_list: list) -> bytes:
    """Template Excel untuk upload data stok"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Template Input Stok"

    headers = ["tanggal","area","warehouse","jenis_nte","type_nte","status_nte","closing_stock"]
    for ci, h in enumerate(headers, 1):
        c = ws.cell(1, ci, value=h)
        _hdr(c)
        ws.column_dimensions[get_column_letter(ci)].width = 26

    examples = [
        ["2025-05-19","TELKOM BANDUNG","TA SO CCAN AHMAD YANI WH","ONT SINGLE BAND","ONT_FIBERHOME_AN5506-04-FS","NTE BARU",10],
        ["2025-05-19","TELKOM BANDUNG","TA SO CCAN AHMAD YANI WH","ONT SINGLE BAND","ONT_FIBERHOME_AN5506-04-FS","REFURBISH",3],
        ["2025-05-19","TELKOM SOREANG","TA SO CCAN SOREANG WH","AP","AP_CISCO_C9105AXI-F","NTE BARU",5],
    ]
    for ri, ex in enumerate(examples, 2):
        for ci, val in enumerate(ex, 1):
            c = ws.cell(ri, ci, value=val)
            c.fill = PatternFill("solid", fgColor="F0F7FF")
            _cell(c, align="left", size=9)

    # Sheet referensi
    ws2 = wb.create_sheet("Referensi")
    ref_h = ["area","warehouse","jenis_nte","type_nte","status_nte"]
    for ci, h in enumerate(ref_h, 1):
        _hdr(ws2.cell(1, ci, value=h))
        ws2.column_dimensions[get_column_letter(ci)].width = 32

    from data.master_data import AREA_CONFIG, NTE_CATALOG, NTE_STATUS
    ri2 = 2
    for area, cfg in AREA_CONFIG.items():
        for wh in cfg["warehouses"]:
            for jenis, types in NTE_CATALOG.items():
                for t in types:
                    for st in NTE_STATUS:
                        for ci2, val in enumerate([area, wh, jenis, t, st], 1):
                            c = ws2.cell(ri2, ci2, value=val)
                            _cell(c, align="left", size=9)
                        ri2 += 1
    ws2.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
