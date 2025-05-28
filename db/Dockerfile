FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y build-essential \
  && pip install --no-cache-dir --upgrade pip


COPY ./db/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
  --index-url https://pypi.tuna.tsinghua.edu.cn/simple


COPY ./db /app/db
COPY ./alembic.ini /app/alembic.ini
COPY ./alembic /app/alembic


CMD ["alembic", "upgrade", "head"]
