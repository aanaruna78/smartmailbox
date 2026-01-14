FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --without dev --no-root

COPY worker/ ./worker

CMD ["python", "-m", "worker.main"]
