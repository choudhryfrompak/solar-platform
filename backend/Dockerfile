FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x wait-for-postgres.sh

RUN mkdir -p migrations/versions
RUN mkdir -p /app/templates
RUN mkdir -p /app/containers

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["./wait-for-postgres.sh", "postgres", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]