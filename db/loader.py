"""
Bootstrap the e-commerce PostgreSQL (Neon) database.

On first run (or whenever the `products` table is missing), this module:
  1. Creates all 5 tables using the DDL in db/schema.py
  2. Loads each CSV from ecommerce_data/ into the corresponding table

Safe to call on every app start — it checks for existence before acting.
"""

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from db.schema import ALL_DDL

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "e-commerce_data"


def _get_engine():
    conn_str = os.getenv("DATABASE_URL")
    if not conn_str:
        raise ValueError(
            "DATABASE_URL not set in .env — "
            "expected format: postgresql://user:password@host/dbname?sslmode=require"
        )
    return create_engine(conn_str)


def _is_seeded(conn) -> bool:
    """Return True only if ALL 5 tables exist and each contains at least one row."""
    tables = ["products", "amz_orders", "shopify_orders", "amz_ads", "meta_ads"]
    for table in tables:
        check = conn.execute(text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :t"
        ), {"t": table})
        if check.fetchone() is None:
            return False
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        if count == 0:
            return False
    return True


def _create_tables(conn):
    for ddl in ALL_DDL:
        conn.execute(text(ddl))
    conn.commit()
    print("[bootstrap] Tables created.")


def _truncate_all(conn):
    """Truncate all tables in reverse FK order before a clean re-import."""
    for table in ["meta_ads", "amz_ads", "shopify_orders", "amz_orders", "products"]:
        conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    conn.commit()
    print("[bootstrap] All tables truncated.")


def _load_products(engine):
    df = pd.read_csv(
        DATA_DIR / "products.csv",
        encoding="utf-8-sig",
        dtype={"product_code": str},
    )
    df = df.rename(columns={"product_code": "sku"})
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df.to_sql("products", con=engine, if_exists="append", index=False)
    print(f"[bootstrap] products: {len(df)} rows loaded.")


def _load_amz_orders(engine):
    df = pd.read_csv(
        DATA_DIR / "amz_orders.csv",
        encoding="utf-8-sig",
        parse_dates=["order_date"],
        dtype={"order_id": str, "sku": str},
    )
    df["sale_price"]   = pd.to_numeric(df["sale_price"],   errors="coerce")
    df["total_taxes"]  = pd.to_numeric(df["total_taxes"],  errors="coerce")
    df["fee"]          = pd.to_numeric(df["fee"],          errors="coerce")
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df.to_sql("amz_orders", con=engine, if_exists="append", index=False)
    print(f"[bootstrap] amz_orders: {len(df)} rows loaded.")


def _load_shopify_orders(engine):
    df = pd.read_csv(
        DATA_DIR / "shopify_orders.csv",
        encoding="utf-8-sig",
        parse_dates=["date"],
        dtype={"order_id": str, "sku": str},
    )
    df = df.rename(columns={"date": "order_date", "type": "order_type"})
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
    df.to_sql("shopify_orders", con=engine, if_exists="append", index=False)
    print(f"[bootstrap] shopify_orders: {len(df)} rows loaded.")


def _load_amz_ads(engine):
    df = pd.read_csv(
        DATA_DIR / "amz_ads.csv",
        encoding="utf-8-sig",
        dtype={"sku": str, "country": str},
    )
    for col in ["clicks", ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ["ctr", "total_cost", "cpc", "purchases", "sales", "roas"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.to_sql("amz_ads", con=engine, if_exists="append", index=False)
    print(f"[bootstrap] amz_ads: {len(df)} rows loaded.")


def _load_meta_ads(engine):
    df = pd.read_csv(
        DATA_DIR / "meta_ads.csv",
        encoding="utf-8-sig",
        dtype={"sku": str},
    )
    df["spend"]       = pd.to_numeric(df["spend"],       errors="coerce")
    df["impressions"] = pd.to_numeric(df["impressions"], errors="coerce").astype("Int64")
    df["clicks"]      = pd.to_numeric(df["clicks"],      errors="coerce").astype("Int64")
    df.to_sql("meta_ads", con=engine, if_exists="append", index=False)
    print(f"[bootstrap] meta_ads: {len(df)} rows loaded.")


def bootstrap():
    """
    Ensure tables exist and are populated. Safe to call on every app start.

    - Always runs CREATE TABLE IF NOT EXISTS (no-op if tables are already there).
    - Imports CSVs only if the products table is empty.
    """
    engine = _get_engine()

    # Always ensure table structure is present
    with engine.connect() as conn:
        _create_tables(conn)

    # Only load data if the products table is empty
    with engine.connect() as conn:
        if _is_seeded(conn):
            print("[bootstrap] Database already seeded — skipping import.")
            return

    print("[bootstrap] Tables are empty — truncating and importing data from CSVs...")
    with engine.connect() as conn:
        _truncate_all(conn)
    _load_products(engine)
    _load_amz_orders(engine)
    _load_shopify_orders(engine)
    _load_amz_ads(engine)
    _load_meta_ads(engine)
    print("[bootstrap] All data loaded successfully.")
