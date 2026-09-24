from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os

def run_etl_script():
    os.system("python /opt/airflow/etl/api_etl.py")

default_args = {
    "start_date": datetime(2023, 1, 1),
}

with DAG(
    dag_id="fakestore_api_etl_dag",
    schedule="@daily",  # eski 'schedule_interval' yerine artık bu kullanılıyor
    catchup=False,
    default_args=default_args,
    tags=["etl"]
) as dag:

    run_etl = PythonOperator(
        task_id="run_etl_script",
        python_callable=run_etl_script
    )