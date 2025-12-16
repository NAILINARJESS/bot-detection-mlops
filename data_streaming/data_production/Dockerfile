FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y netcat-openbsd bash curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY data/ ./data

COPY wait-for-kafka.sh .
RUN chmod +x wait-for-kafka.sh

EXPOSE 5000

CMD ["python", "server.py"]

