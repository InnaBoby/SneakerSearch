FROM python:3.12-slim

ENV POETRY_HTTP_TIMEOUT=1000

WORKDIR /app

COPY pyproject.toml poetry.lock app.py utils.py bot.py ./

RUN apt-get update && pip install poetry && poetry install --no-root 

EXPOSE 8000