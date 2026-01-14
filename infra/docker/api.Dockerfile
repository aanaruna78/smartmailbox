FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY alembic.ini .
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --without dev --no-root

COPY app/ ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
