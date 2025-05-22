FROM python:3.11-slim

WORKDIR /tokeon_assistant_rest_api

ENV PYTHONPATH=/tokeon_assistant_rest_api

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

COPY ../tokeon_assistant_rest_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

RUN python - <<'EOF'
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('punkt_tab')
EOF

COPY ./tokeon_assistant_rest_api .

EXPOSE 8001

CMD ["uvicorn", "tokeon_assistant_rest_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
