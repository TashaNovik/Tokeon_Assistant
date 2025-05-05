FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python - <<'EOF'
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
EOF

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
