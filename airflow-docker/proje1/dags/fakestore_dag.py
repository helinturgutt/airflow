from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess
import logging

def run_etl_script():
    """ETL scriptini çalıştır"""
    try:
        # os.system yerine subprocess kullanımı daha güvenli
        result = subprocess.run(
            ["python", "/opt/airflow/etl/api_etl.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info(f"ETL script başarıyla tamamlandı: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"ETL script hatası: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"Beklenmeyen hata: {str(e)}")
        raise

default_args = {
    "owner": "data_team",  # Owner bilgisi eklendi
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),  # Tarihi güncelledim
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,  # Hata durumunda tekrar deneme
}

with DAG(
    dag_id="fakestore_api_etl_dag",
    description="FakeStore API'den veri çeken ETL DAG'ı",  # Açıklama eklendi
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["etl", "api", "fakestore"]
) as dag:
    
    run_etl = PythonOperator(
        task_id="run_etl_script",
        python_callable=run_etl_script,
        doc_md="""
        ## ETL Task
        Bu task FakeStore API'den veri çeker ve işler.
        """
    )

