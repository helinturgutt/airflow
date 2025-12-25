FROM apache/airflow:3.0.0-python3.12

USER root

RUN apt-get update && \
    apt-get -y install git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


