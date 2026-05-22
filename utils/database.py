"""
Database utility — SQLite
Skema sekarang menyimpan kolom `operator` dan `area` terpisah
untuk mendukung filter per operator/area/kombinasi
"""

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nte_stok.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabel utama — unique per (tanggal, operator, warehouse, type_nte, status_nte)
    c.execute("""
        CREATE TABLE IF NOT EXISTS stok_harian (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal       DATE    NOT NULL,
            operator      TEXT    NOT NULL,
            area          TEXT    NOT NULL,
            area_key      TEXT    NOT NULL,
            warehouse     TEXT    NOT NULL,
            jenis_nte     TEXT    NOT NULL,
            type_nte      TEXT    NOT NULL,
            status_nte    TEXT    NOT NULL,
            closing_stock INTEGER NOT NULL DEFAULT 0,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tanggal, operator, warehouse, type_nte, status_nte)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS rekap_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal      DATE    NOT NULL,
            scope        TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ── Write ─────────────────────────────────────────────────────────────────────

def upsert_stok(tanggal, operator, area, area_key,
                warehouse, jenis_nte, type_nte, status_nte, closing_stock):
    conn = get_connection()
    conn.execute("""
        INSERT INTO stok_harian
            (tanggal, operator, area, area_key, warehouse,
             jenis_nte, type_nte, status_nte, closing_stock, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
        ON CONFLICT(tanggal, operator, warehouse, type_nte, status_nte)
        DO UPDATE SET closing_stock=excluded.closing_stock,
                      updated_at=CURRENT_TIMESTAMP
    """, (tanggal, operator, area, area_key,
          warehouse, jenis_nte, type_nte, status_nte, closing_stock))
    conn.commit()
    conn.close()

def bulk_upsert_stok(df: pd.DataFrame):
    conn = get_connection()
    success, errors = 0, []
    for idx, row in df.iterrows():
        try:
            conn.execute("""
                INSERT INTO stok_harian
                    (tanggal, operator, area, area_key, warehouse,
                     jenis_nte, type_nte, status_nte, closing_stock, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(tanggal, operator, warehouse, type_nte, status_nte)
                DO UPDATE SET closing_stock=excluded.closing_stock,
                              updated_at=CURRENT_TIMESTAMP
            """, (
                str(row["tanggal"]), row["operator"], row["area"],
                row["area_key"], row["warehouse"],
                row["jenis_nte"], row["type_nte"],
                row["status_nte"], int(row["closing_stock"])
            ))
            success += 1
        except Exception as e:
            errors.append(f"Baris {idx+2}: {e}")
    conn.commit()
    conn.close()
    return success, errors

def delete_stok(tanggal, operator, warehouse):
    conn = get_connection()
    conn.execute(
        "DELETE FROM stok_harian WHERE tanggal=? AND operator=? AND warehouse=?",
        (tanggal, operator, warehouse)
    )
    conn.commit()
    conn.close()

def log_rekap(tanggal, scope=None):
    conn = get_connection()
    conn.execute("INSERT INTO rekap_log (tanggal, scope) VALUES (?,?)", (tanggal, scope))
    conn.commit()
    conn.close()

# ── Read ──────────────────────────────────────────────────────────────────────

def get_available_dates() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT tanggal FROM stok_harian ORDER BY tanggal DESC"
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]

def get_stok(tanggal: str,
             operator: str = None,
             area: str = None,
             area_key: str = None) -> pd.DataFrame:
    """Ambil stok dengan filter opsional."""
    sql    = "SELECT * FROM stok_harian WHERE tanggal=?"
    params = [tanggal]
    if operator:
        sql += " AND operator=?";  params.append(operator)
    if area:
        sql += " AND area=?";      params.append(area)
    if area_key:
        sql += " AND area_key=?";  params.append(area_key)
    sql += " ORDER BY operator, area, warehouse, jenis_nte, type_nte, status_nte"
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def get_wh_coverage(tanggal: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT DISTINCT operator, area, area_key, warehouse FROM stok_harian WHERE tanggal=?",
        conn, params=(tanggal,)
    )
    conn.close()
    return df

def get_rekap_per_wh(area_key: str, tanggal: str) -> pd.DataFrame:
    """Rekap pivot per WH untuk satu area_key."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT jenis_nte, type_nte, status_nte, warehouse, closing_stock
        FROM stok_harian
        WHERE area_key=? AND tanggal=?
        ORDER BY jenis_nte, type_nte, status_nte, warehouse
    """, conn, params=(area_key, tanggal))
    conn.close()
    return df

def get_grand_total(tanggal: str) -> pd.DataFrame:
    """Grand total per (operator, area, jenis, type, status)."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT operator, area, area_key, jenis_nte, type_nte, status_nte,
               SUM(closing_stock) AS total_stock
        FROM stok_harian
        WHERE tanggal=?
        GROUP BY operator, area, area_key, jenis_nte, type_nte, status_nte
        ORDER BY operator, area, jenis_nte, type_nte, status_nte
    """, conn, params=(tanggal,))
    conn.close()
    return df

def get_tren_stok(type_nte: str, status_nte: str,
                  operator: str = None) -> pd.DataFrame:
    sql    = """
        SELECT tanggal, operator, area,
               SUM(closing_stock) AS total_stock
        FROM stok_harian
        WHERE type_nte=? AND status_nte=?
    """
    params = [type_nte, status_nte]
    if operator:
        sql += " AND operator=?"; params.append(operator)
    sql += " GROUP BY tanggal, operator, area ORDER BY tanggal DESC LIMIT 120"
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df
