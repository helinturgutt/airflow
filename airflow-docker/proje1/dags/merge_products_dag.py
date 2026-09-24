
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2

def ensure_merged_schema(cur):
    # Tablo yoksa hedef şema ile oluştur
    cur.execute("""
        CREATE TABLE IF NOT EXISTS merged_products (
            id INT PRIMARY KEY,
            name TEXT,
            api_price NUMERIC,
            local_price NUMERIC,
            price_diff NUMERIC,
            category TEXT,
            rating_rate NUMERIC,
            rating_count INT
        );
    """)

    # Eski kolon adını düzelt (title -> name)
    cur.execute("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='merged_products' AND column_name='title'
      ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='merged_products' AND column_name='name'
      ) THEN
        ALTER TABLE merged_products RENAME COLUMN title TO name;
      END IF;
    END$$;
    """)

    # Eksik kolonlar varsa ekle (id dışında)
    cur.execute("ALTER TABLE merged_products ADD COLUMN IF NOT EXISTS name TEXT;")
    cur.execute("ALTER TABLE merged_products ADD COLUMN IF NOT EXISTS api_price NUMERIC;")
    cur.execute("ALTER TABLE merged_products ADD COLUMN IF NOT EXISTS local_price NUMERIC;")
    cur.execute("ALTER TABLE merged_products ADD COLUMN IF NOT EXISTS price_diff NUMERIC;")
    cur.execute("ALTER TABLE merged_products ADD COLUMN IF NOT EXISTS category TEXT;")
    cur.execute("ALTER TABLE merged_products ADD COLUMN IF NOT EXISTS rating_rate NUMERIC;")
    cur.execute("ALTER TABLE merged_products ADD COLUMN IF NOT EXISTS rating_count INT;")

    # ON CONFLICT (id) çalışabilsin diye unique index (PK yoksa)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_merged_products_id ON merged_products (id);")

def merge_products():
    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow",
        port=5432,
    )
    try:
        with conn, conn.cursor() as cur:
            ensure_merged_schema(cur)

            # Birleştir ve upsert et (ARTIK name kullanılıyor)
            cur.execute("""
                INSERT INTO merged_products (id, name, api_price, local_price, price_diff, category, rating_rate, rating_count)
                SELECT
                    p.id,
                    p.name,
                    p.price AS api_price,
                    ip.price AS local_price,
                    CASE
                        WHEN p.price IS NULL OR ip.price IS NULL THEN NULL
                        ELSE p.price - ip.price
                    END AS price_diff,
                    p.category,
                    p.rating_rate,
                    p.rating_count
                FROM products p
                LEFT JOIN imported_products ip ON ip.id = p.id
                ON CONFLICT (id) DO UPDATE SET
                    name        = EXCLUDED.name,
                    api_price   = EXCLUDED.api_price,
                    local_price = EXCLUDED.local_price,
                    price_diff  = EXCLUDED.price_diff,
                    category    = EXCLUDED.category,
                    rating_rate = EXCLUDED.rating_rate,
                    rating_count= EXCLUDED.rating_count;
            """)
    finally:
        conn.close()
    print("✅ merged_products güncellendi.")

def run_analysis():
    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow",
        port=5432,
    )
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                SELECT ROUND(AVG(api_price)::numeric, 2),
                       ROUND(AVG(local_price)::numeric, 2)
                FROM merged_products;
            """)
            avg_api, avg_local = cur.fetchone()
            print(f"📊 Ortalama API fiyatı: {avg_api}")
            print(f"📊 Ortalama Lokal fiyat: {avg_local}")

            cur.execute("""
                SELECT category, COUNT(*) 
                FROM merged_products 
                GROUP BY category 
                ORDER BY category;
            """)
            for category, count in cur.fetchall():
                print(f"📦 {category}: {count} ürün")

            cur.execute("""
                SELECT COUNT(*) 
                FROM merged_products
                WHERE local_price IS NOT NULL
                  AND api_price IS DISTINCT FROM local_price;
            """)
            diff_cnt = cur.fetchone()[0]
            print(f"🔍 Fiyat farkı olan ürün sayısı: {diff_cnt}")
    finally:
        conn.close()

with DAG(
    dag_id="merge_products_dag",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["etl", "merge", "products"],
) as dag:
    merge_task = PythonOperator(
        task_id="merge_products",
        python_callable=merge_products,
    )
    analysis_task = PythonOperator(
        task_id="run_analysis",
        python_callable=run_analysis,
    )
    merge_task >> analysis_task
