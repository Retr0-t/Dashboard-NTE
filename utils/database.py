"""
Utility database - SQLite untuk penyimpanan data stok NTE
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nte_stok.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inisialisasi database dan buat tabel jika belum ada"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS stok_harian (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal DATE NOT NULL,
            area TEXT NOT NULL,
            warehouse TEXT NOT NULL,
            jenis_nte TEXT NOT NULL,
            type_nte TEXT NOT NULL,
            status_nte TEXT NOT NULL,
            closing_stock INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(tanggal, warehouse, type_nte, status_nte)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS rekap_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal DATE NOT NULL,
            area TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            generated_by TEXT DEFAULT 'system'
        )
    """)
    
    conn.commit()
    conn.close()

def upsert_stok(tanggal, area, warehouse, jenis_nte, type_nte, status_nte, closing_stock):
    """Insert atau update data stok"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO stok_harian (tanggal, area, warehouse, jenis_nte, type_nte, status_nte, closing_stock, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(tanggal, warehouse, type_nte, status_nte)
        DO UPDATE SET closing_stock=excluded.closing_stock, updated_at=CURRENT_TIMESTAMP
    """, (tanggal, area, warehouse, jenis_nte, type_nte, status_nte, closing_stock))
    conn.commit()
    conn.close()

def bulk_upsert_stok(df: pd.DataFrame):
    """Bulk insert dari DataFrame (upload Excel)"""
    conn = get_connection()
    success, errors = 0, []
    for _, row in df.iterrows():
        try:
            c = conn.cursor()
            c.execute("""
                INSERT INTO stok_harian (tanggal, area, warehouse, jenis_nte, type_nte, status_nte, closing_stock, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(tanggal, warehouse, type_nte, status_nte)
                DO UPDATE SET closing_stock=excluded.closing_stock, updated_at=CURRENT_TIMESTAMP
            """, (
                str(row["tanggal"]), row["area"], row["warehouse"],
                row["jenis_nte"], row["type_nte"], row["status_nte"],
                int(row["closing_stock"])
            ))
            success += 1
        except Exception as e:
            errors.append(f"Baris {_+2}: {str(e)}")
    conn.commit()
    conn.close()
    return success, errors

def get_stok_by_date(tanggal: str) -> pd.DataFrame:
    """Ambil semua data stok untuk tanggal tertentu"""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM stok_harian WHERE tanggal=? ORDER BY area, warehouse, jenis_nte, type_nte, status_nte",
        conn, params=(tanggal,)
    )
    conn.close()
    return df

def get_stok_by_area_date(area: str, tanggal: str) -> pd.DataFrame:
    """Ambil data stok berdasarkan area dan tanggal"""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM stok_harian WHERE area=? AND tanggal=? ORDER BY warehouse, jenis_nte, type_nte, status_nte",
        conn, params=(area, tanggal)
    )
    conn.close()
    return df

def get_rekap_grand_total(tanggal: str) -> pd.DataFrame:
    """Grand total per type_nte dan status per semua WH"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT area, jenis_nte, type_nte, status_nte,
               SUM(closing_stock) as total_stock,
               COUNT(DISTINCT warehouse) as jumlah_wh
        FROM stok_harian
        WHERE tanggal=?
        GROUP BY area, jenis_nte, type_nte, status_nte
        ORDER BY area, jenis_nte, type_nte, status_nte
    """, conn, params=(tanggal,))
    conn.close()
    return df

def get_rekap_per_wh(area: str, tanggal: str) -> pd.DataFrame:
    """Rekap per warehouse dalam satu area untuk grand total per type"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT jenis_nte, type_nte, status_nte, warehouse, closing_stock
        FROM stok_harian
        WHERE area=? AND tanggal=?
        ORDER BY jenis_nte, type_nte, status_nte, warehouse
    """, conn, params=(area, tanggal))
    conn.close()
    return df

def get_tren_stok(type_nte: str, status_nte: str, days: int = 30) -> pd.DataFrame:
    """Tren stok untuk type NTE tertentu selama N hari terakhir"""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT tanggal, area, SUM(closing_stock) as total_stock
        FROM stok_harian
        WHERE type_nte=? AND status_nte=?
        GROUP BY tanggal, area
        ORDER BY tanggal DESC
        LIMIT ?
    """, conn, params=(type_nte, status_nte, days * 2))
    conn.close()
    return df

def get_available_dates() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT tanggal FROM stok_harian ORDER BY tanggal DESC")
    dates = [row[0] for row in c.fetchall()]
    conn.close()
    return dates

def get_wh_coverage(tanggal: str) -> pd.DataFrame:
    """Cek warehouse mana yang sudah lapor pada tanggal tertentu"""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT DISTINCT area, warehouse FROM stok_harian WHERE tanggal=?",
        conn, params=(tanggal,)
    )
    conn.close()
    return df

def delete_stok_by_date_wh(tanggal: str, warehouse: str):
    conn = get_connection()
    conn.execute("DELETE FROM stok_harian WHERE tanggal=? AND warehouse=?", (tanggal, warehouse))
    conn.commit()
    conn.close()

def log_rekap(tanggal: str, area: str = None):
    conn = get_connection()
    conn.execute("INSERT INTO rekap_log (tanggal, area) VALUES (?, ?)", (tanggal, area))
    conn.commit()
    conn.close()
