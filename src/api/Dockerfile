FROM python:3.12-slim

WORKDIR /app

# Copier requirements depuis la racine
COPY ../../requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier uniquement ce qui est nécessaire à l'API
COPY ../../src ./src
COPY ../../data ./data
COPY ../../src/tracking/bot_detection_latest.pkl ./src/tracking/

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

