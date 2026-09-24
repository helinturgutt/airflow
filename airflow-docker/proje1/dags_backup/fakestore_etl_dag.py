from proje1.scripts.telegram_utils import send_telegram_message
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import subprocess
import logging
# Telegram bot bilgileri
BOT_TOKEN = "8387206014:AAFcxwu03itJe3M1BKXJkW9VTQBwgJ9JYgM"
CHAT_ID = "6473531278"
def run_etl():
    """FakeStore ETL scriptini çalıştır"""
    try:
        # os.system yerine subprocess kullanımı daha güvenli
        # Orijinal kodda "python/opt/..." şeklinde boşluk eksikti, düzeltildi
        result = subprocess.run(
            ["python", "/opt/airflow/etl/fakestore_etl.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info(f"FakeStore ETL script başarıyla tamamlandı: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"FakeStore ETL script hatası: {e.stderr}")
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
    dag_id="fakestore_etl_dag",
    description="FakeStore API'den veri çeken ETL DAG'ı",  # Açıklama eklendi
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["etl", "api", "fakestore"]
) as dag:
    
    run_fakestore_etl = PythonOperator(
        task_id="run_fakestore_etl_script",
        python_callable=run_etl,
        doc_md="""
        ## FakeStore ETL Task
        Bu task FakeStore API'den veri çeker ve işler.
        """
    )