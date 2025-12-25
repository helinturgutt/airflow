from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os

def run_etl():
    os.system("python /opt/airflow/etl/fakestore_etl.py")

default_args = {
    "start_date": datetime(2023, 1, 1),
}

with DAG(
    dag_id="fakestore_etl_dag",
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["etl"]
) as dag:

    run_fakestore_etl = PythonOperator(
        task_id="run_fakestore_etl_script",
        python_callable=run_etl
    )
