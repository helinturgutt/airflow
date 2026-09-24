# etl/api_etl.py
import requests
import psycopg2
from psycopg2.extras import execute_values

API_URL = "https://fakestoreapi.com/products"

PG = dict(
    host="postgres",
    dbname="airflow",
    user="airflow",
    password="airflow",
    port=5432,
)

CREATE_SQL = """
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

# Eski kurulumda 'title' varsa otomatik 'name'e çevir
MIGRATE_SQL = """
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

UPSERT_SQL = """
INSERT INTO products (id, name, price, description, category, image, rating_rate, rating_count)
VALUES %s
ON CONFLICT (id) DO UPDATE SET
  name         = EXCLUDED.name,
  price        = EXCLUDED.price,
  description  = EXCLUDED.description,
  category     = EXCLUDED.category,
  image        = EXCLUDED.image,
  rating_rate  = EXCLUDED.rating_rate,
  rating_count = EXCLUDED.rating_count;
"""

def extract():
    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()
    return r.json()

def transform(items):
    rows = []
    for it in items:
        rating = it.get("rating") or {}
        # title -> name dönüşümü
        rows.append((
            int(it.get("id")),
            str(it.get("title")) if it.get("title") is not None else None,  # name
            float(it.get("price")) if it.get("price") is not None else None,
            str(it.get("description")) if it.get("description") is not None else None,
            str(it.get("category")) if it.get("category") is not None else None,
            str(it.get("image")) if it.get("image") is not None else None,
            float(rating.get("rate")) if rating.get("rate") is not None else None,
            int(rating.get("count")) if rating.get("count") is not None else None,
        ))
    return rows

def load(rows):
    conn = psycopg2.connect(**PG)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(CREATE_SQL)
            cur.execute(MIGRATE_SQL)
            execute_values(cur, UPSERT_SQL, rows, page_size=500)
    finally:
        conn.close()

if __name__ == "__main__":
    data = extract()
    rows = transform(data)
    load(rows)
    print(f"✅ API verisi yüklendi / güncellendi: {len(rows)} kayıt.")
