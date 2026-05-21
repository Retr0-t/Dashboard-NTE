"""
Utility export - Excel dan PDF
"""

import pandas as pd
import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import (
    PatternFill, Font, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows


def style_header(cell, bg_color="1E3A5F", font_color="FFFFFF", bold=True, size=11):
    cell.fill = PatternFill("solid", fgColor=bg_color)
    cell.font = Font(color=font_color, bold=bold, size=size)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    _border(cell)

def _border(cell, color="CCCCCC"):
    thin = Side(style="thin", color=color)
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)

def _data_cell(cell, align="center"):
    cell.alignment = Alignment(horizontal=align, vertical="center")
    _border(cell)


def export_rekap_area_excel(pivot_df: pd.DataFrame, detail_df: pd.DataFrame,
                             area: str, tanggal: str, warehouses: list) -> bytes:
    """
    Export rekap per area ke Excel.
    pivot_df: kolom = [jenis_nte, type_nte, status_nte, WH1, WH2, ..., GRAND TOTAL]
    """
    wb = Workbook()
    ws = wb.active
    ws.title = f"Rekap {area}"

    # ── Title block ──────────────────────────────────────────────
    ws.merge_cells("A1:Z1")
    ws["A1"] = f"REKAP STOK NTE HARIAN – {area.upper()}"
    ws["A1"].font = Font(bold=True, size=14, color="1E3A5F")
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:Z2")
    ws["A2"] = f"Tanggal Laporan: {tanggal}"
    ws["A2"].alignment = Alignment(horizontal="center")
    ws["A2"].font = Font(italic=True, size=10, color="555555")
    ws.row_dimensions[2].height = 16

    ws.row_dimensions[3].height = 8  # spacer

    # ── Column headers ───────────────────────────────────────────
    fixed_cols = ["Jenis NTE", "Type NTE", "Status"]
    wh_cols = warehouses
    all_cols = fixed_cols + wh_cols + ["GRAND TOTAL"]

    header_row = 4
    for ci, col in enumerate(all_cols, start=1):
        cell = ws.cell(row=header_row, column=ci, value=col)
        bg = "1E3A5F" if col in ["Jenis NTE", "Type NTE", "Status"] else \
             "2E6DA4" if col != "GRAND TOTAL" else "C0392B"
        style_header(cell, bg_color=bg)
        ws.column_dimensions[get_column_letter(ci)].width = 28 if ci <= 3 else 14

    ws.row_dimensions[header_row].height = 36

    # ── Data rows ────────────────────────────────────────────────
    row_idx = header_row + 1
    prev_jenis = None
    jenis_start = row_idx

    for _, r in pivot_df.iterrows():
        jenis = r.get("jenis_nte", "")
        type_nte = r.get("type_nte", "")
        status = r.get("status_nte", "")
        grand = r.get("GRAND TOTAL", 0)

        # Jenis grouping
        jenis_cell = ws.cell(row=row_idx, column=1, value=jenis if jenis != prev_jenis else "")
        jenis_cell.fill = PatternFill("solid", fgColor="D9E8F5")
        jenis_cell.font = Font(bold=True, color="1E3A5F")
        _data_cell(jenis_cell, "left")

        ws.cell(row=row_idx, column=2, value=type_nte)
        _data_cell(ws.cell(row=row_idx, column=2), "left")

        status_cell = ws.cell(row=row_idx, column=3, value=status)
        status_cell.fill = PatternFill("solid",
            fgColor="E8F8E8" if status == "Baru" else "FFF8E8")
        _data_cell(status_cell)

        for wi, wh in enumerate(wh_cols, start=4):
            val = r.get(wh, 0) or 0
            c = ws.cell(row=row_idx, column=wi, value=int(val))
            c.fill = PatternFill("solid", fgColor="F7FBFF")
            _data_cell(c)

        gt_cell = ws.cell(row=row_idx, column=len(all_cols), value=int(grand))
        gt_cell.fill = PatternFill("solid", fgColor="FADBD8")
        gt_cell.font = Font(bold=True, color="C0392B")
        _data_cell(gt_cell)

        prev_jenis = jenis
        row_idx += 1

    # ── Grand total row ──────────────────────────────────────────
    ws.cell(row=row_idx, column=1, value="TOTAL KESELURUHAN")
    ws.merge_cells(f"A{row_idx}:C{row_idx}")
    tc = ws.cell(row=row_idx, column=1)
    tc.fill = PatternFill("solid", fgColor="1E3A5F")
    tc.font = Font(bold=True, color="FFFFFF", size=11)
    tc.alignment = Alignment(horizontal="center", vertical="center")

    for wi, wh in enumerate(wh_cols, start=4):
        col_letter = get_column_letter(wi)
        formula = f"=SUM({col_letter}{header_row+1}:{col_letter}{row_idx-1})"
        c = ws.cell(row=row_idx, column=wi, value=formula)
        c.fill = PatternFill("solid", fgColor="2E6DA4")
        c.font = Font(bold=True, color="FFFFFF")
        _data_cell(c)

    gt_col = get_column_letter(len(all_cols))
    total_cell = ws.cell(row=row_idx, column=len(all_cols),
                         value=f"=SUM({gt_col}{header_row+1}:{gt_col}{row_idx-1})")
    total_cell.fill = PatternFill("solid", fgColor="C0392B")
    total_cell.font = Font(bold=True, color="FFFFFF", size=12)
    _data_cell(total_cell)
    ws.row_dimensions[row_idx].height = 24

    # ── Freeze panes ─────────────────────────────────────────────
    ws.freeze_panes = f"D{header_row+1}"

    # ── Sheet 2: Raw Detail ───────────────────────────────────────
    ws2 = wb.create_sheet("Data Detail")
    if not detail_df.empty:
        for r_idx, row in enumerate(dataframe_to_rows(detail_df, index=False, header=True), 1):
            for c_idx, val in enumerate(row, 1):
                cell = ws2.cell(row=r_idx, column=c_idx, value=val)
                if r_idx == 1:
                    style_header(cell)
                else:
                    _data_cell(cell, "left")
        for ci in range(1, len(detail_df.columns)+1):
            ws2.column_dimensions[get_column_letter(ci)].width = 22

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


def build_excel_template(warehouses_list: list) -> bytes:
    """Buat template Excel untuk upload data stok"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Template Input Stok"

    headers = ["tanggal", "area", "warehouse", "jenis_nte", "type_nte", "status_nte", "closing_stock"]
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=ci, value=h)
        style_header(c, bg_color="1E3A5F")
        ws.column_dimensions[get_column_letter(ci)].width = 22

    # Contoh baris
    examples = [
        ["2025-01-15", "TELKOM SOREANG", "WH Banjaran", "ONT", "ONT_FiberHome_AN5506-04-FS", "Baru", 10],
        ["2025-01-15", "TELKOM SOREANG", "WH Banjaran", "ONT", "ONT_FiberHome_AN5506-04-FS", "Refurbish", 3],
        ["2025-01-15", "TELKOM BANDUNG", "WH Cicadas", "STB", "STB_ZTE_B700", "Baru", 25],
    ]
    for ri, ex in enumerate(examples, 2):
        for ci, val in enumerate(ex, 1):
            c = ws.cell(row=ri, column=ci, value=val)
            c.fill = PatternFill("solid", fgColor="F0F7FF")
            _data_cell(c, "left")

    ws2 = wb.create_sheet("Referensi")
    ref_headers = ["area", "warehouse", "jenis_nte", "type_nte", "status_nte"]
    for ci, h in enumerate(ref_headers, 1):
        style_header(ws2.cell(row=1, column=ci, value=h))
        ws2.column_dimensions[get_column_letter(ci)].width = 30

    from data.master_data import AREA_CONFIG, NTE_CATALOG, NTE_STATUS
    ri = 2
    for area, cfg in AREA_CONFIG.items():
        for wh in cfg["warehouses"]:
            for jenis, types in NTE_CATALOG.items():
                for t in types:
                    for st in NTE_STATUS:
                        for ci, val in enumerate([area, wh, jenis, t, st], 1):
                            c = ws2.cell(row=ri, column=ci, value=val)
                            _data_cell(c, "left")
                        ri += 1
    ws2.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
