# Küçük ve hafif bir Python imajı seçiyoruz
FROM python:3.9-slim

# Uygulamanın çalışacağı dizin
WORKDIR /app

# Etl klasöründeki her şeyi container içine kopyala
COPY . .

# Gerekli kütüphaneleri kur
RUN pip install --no-cache-dir requests pandas psycopg2-binary

# Scripti çalıştır
CMD ["python", "api_etl.py"]
