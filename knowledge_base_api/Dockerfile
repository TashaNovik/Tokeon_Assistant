FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

COPY ./knowledge_base_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

RUN python - <<'EOF'
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
EOF

COPY ./knowledge_base_api /app/knowledge_base_api

EXPOSE 8002

CMD ["uvicorn", "knowledge_base_api.main:app", "--host", "0.0.0.0", "--port", "8002"]
