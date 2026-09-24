import sys
import os
import subprocess
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Yol ayarları (telegram_utils ve email fonksiyonu için)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from telegram_utils import send_telegram_message
from send_email_notification import send_email_notification

# Telegram bilgileri
BOT_TOKEN = "8387206014:AAFcxwuO3itJe3MlBKXJkW9VTQBwgJ9JYgM"
CHAT_ID = "6473531278"

# HATA bildirimi (Telegram + Email)
def notify_failure(context):
    dag_id = context.get('dag').dag_id
    task_id = context.get('task_instance').task_id
    execution_date = context.get('execution_date')

    # Telegram mesajı
    message = f"❌ <b>HATA</b>\nDAG: <code>{dag_id}</code>\nTask: <code>{task_id}</code>\nZaman: {execution_date}"

    send_telegram_message(
        token=BOT_TOKEN,
        chat_id=CHAT_ID,
        message=message
    )

    # E-posta mesajı
    subject = f"❌ HATA - DAG: {dag_id}"
    body = f"""
    DAG başarısız oldu.
    DAG: {dag_id}
    Task: {task_id}
    Zaman: {execution_date}
    """

    send_email_notification(
        subject=subject,
        body=body,
        to_email="hellinturgut@gmail.com",
        from_email="hellinturgut@gmail.com",
        app_password="twmusvcudfuphpdf"
    )

    logging.info(f"Telegram ve e-posta mesajları gönderildi.")

# BAŞARI bildirimi
def notify_success(context):
    dag_id = context.get('dag').dag_id
    task_id = context.get('task_instance').task_id
    execution_date = context.get('execution_date')

    # Telegram mesajı
    message = f"✅ <b>BAŞARILI</b>\nDAG: <code>{dag_id}</code>\nTask: <code>{task_id}</code>\nZaman: {execution_date}"
    send_telegram_message(token=BOT_TOKEN, chat_id=CHAT_ID, message=message)

    # E-posta mesajı
    subject = f"✅ BAŞARILI - DAG: {dag_id}"
    body = f"""
    DAG başarıyla tamamlandı.
    DAG: {dag_id}
    Task: {task_id}
    Zaman: {execution_date}
    """

    send_email_notification(
        subject=subject,
        body=body,
        to_email="hellinturgut@gmail.com",
        from_email="hellinturgut@gmail.com",
        app_password="twmusvcudfuphpdf"
    )

    logging.info("Telegram ve e-posta başarı bildirimi gönderildi.")

# ETL scriptini çalıştır
def run_etl():
    try:
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

# Varsayılan ayarlar
default_args = {
    "owner": "data_team",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "on_failure_callback": notify_failure,
    "on_success_callback": notify_success
}

# DAG tanımı
with DAG(
    dag_id="fakestore_etl_dag",
    description="FakeStore API'den veri çeken ETL DAG'ı",
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
