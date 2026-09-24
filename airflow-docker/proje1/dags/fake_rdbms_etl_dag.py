from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2

def transfer_data():
    # Kaynak veritabanına bağlan (Fake Postgres)
    src_conn = psycopg2.connect(
        host="fake-postgres",
        database="fakestoredb",
        user="fakeuser",
        password="fakepass"
    )
    src_cur = src_conn.cursor()
    src_cur.execute("SELECT id, name, price FROM products;")  # <-- title yerine name
    rows = src_cur.fetchall()

    # Hedef veritabanına bağlan (Ana Postgres)
    dest_conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow"
    )
    dest_cur = dest_conn.cursor()

    dest_cur.execute("""
        CREATE TABLE IF NOT EXISTS imported_products (
            id INT PRIMARY KEY,
            name TEXT,
            price NUMERIC
        );
    """)

    dest_cur.executemany("""
        INSERT INTO imported_products (id, name, price)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, rows)

    dest_conn.commit()

    src_cur.close()
    src_conn.close()
    dest_cur.close()
    dest_conn.close()

with DAG(
    dag_id="fake_rdbms_etl_dag",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False
) as dag:
    transfer_task = PythonOperator(
        task_id="transfer_data",
        python_callable=transfer_data
    )
