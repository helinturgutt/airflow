import requests
import psycopg2
import pandas as pd
from psycopg2.extras import execute_values

print("🚀 fakestore_etl.py: ETL başladı")

# Docker network içinden erişim isimleri/portları:
FAKE_PG = dict(host="fake-postgres", dbname="fakestoredb", user="fakeuser", password="fakepass", port=5432)
AIRFLOW_PG = dict(host="postgres",      dbname="airflow",   user="airflow",  password="airflow",  port=5432)

# Tekilleştirilmiş tablo şeması (title yerine name)
DDL_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
  id INT PRIMARY KEY,
  name TEXT,
  price NUMERIC,
  description TEXT,
  category TEXT,
  image TEXT,
  rating_rate NUMERIC,
  rating_count INT
);
"""

# Eski tabloda 'title' kolonu varsa tek seferlik migrate et (title -> name)
MIGRATE_TITLE_TO_NAME = """
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='products' AND column_name='title'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='products' AND column_name='name'
  ) THEN
    ALTER TABLE products RENAME COLUMN title TO name;
  END IF;
END$$;
"""

# Esnek tüketim için kısa görünüm (diğer DAG'lar sadece id,name,price bekliyorsa)
CREATE_VIEW_SHORT = """
CREATE OR REPLACE VIEW products_for_etl AS
SELECT id, name, price FROM products;
"""

UPSERT_SQL = """
INSERT INTO products (id, name, price, description, category, image, rating_rate, rating_count)
VALUES %s
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  price = EXCLUDED.price,
  description = EXCLUDED.description,
  category = EXCLUDED.category,
  image = EXCLUDED.image,
  rating_rate = EXCLUDED.rating_rate,
  rating_count = EXCLUDED.rating_count;
"""

def extract():
    url = "https://fakestoreapi.com/products"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def transform(data):
    # rating'i düzleştir
    for item in data:
        item["rating_rate"] = item["rating"]["rate"]
        item["rating_count"] = item["rating"]["count"]
        del item["rating"]
    df = pd.DataFrame(data)

    # title -> name (tek tip şema)
    df["name"] = df["title"]
    df = df.drop(columns=["title"])

    # kolon sırası sabit (INSERT order ile birebir)
    cols = ["id", "name", "price", "description", "category", "image", "rating_rate", "rating_count"]
    df = df[cols]
    return df

def ensure_schema_and_migrate(cur):
    # tabloyu garanti et
    cur.execute(DDL_PRODUCTS)
    # varsa eski 'title' -> 'name' migrate
    cur.execute(MIGRATE_TITLE_TO_NAME)
    # kısa view (opsiyonel ama faydalı): id, name, price
    cur.execute(CREATE_VIEW_SHORT)

def coerce_rows(df: pd.DataFrame):
    """NumPy tiplerini Python native tiplere çevirip NULL'ları None yap."""
    safe_df = df.where(pd.notnull(df), None)
    rows = []
    for r in safe_df.itertuples(index=False, name=None):
        # (id, name, price, description, category, image, rating_rate, rating_count)
        rows.append((
            int(r[0]) if r[0] is not None else None,
            str(r[1]) if r[1] is not None else None,
            float(r[2]) if r[2] is not None else None,
            str(r[3]) if r[3] is not None else None,
            str(r[4]) if r[4] is not None else None,
            str(r[5]) if r[5] is not None else None,
            float(r[6]) if r[6] is not None else None,
            int(r[7]) if r[7] is not None else None,
        ))
    return rows

def load_df(conn_info, df: pd.DataFrame, tag: str):
    conn = psycopg2.connect(**conn_info)
    try:
        with conn, conn.cursor() as cur:
            ensure_schema_and_migrate(cur)
            rows = coerce_rows(df)
            execute_values(cur, UPSERT_SQL, rows, page_size=500)
        print(f"✅ {tag}: {len(df)} satır yüklendi/upsert edildi.")
    finally:
        conn.close()

if __name__ == "__main__":
    data = extract()
    df = transform(data)
    load_df(FAKE_PG, df, "fake-postgres/fakestoredb")
    load_df(AIRFLOW_PG, df, "postgres/airflow")
    print("🎉 fakestore_etl.py: ETL bitti")
