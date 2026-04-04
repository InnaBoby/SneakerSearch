FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock app.py utils.py ./

RUN apt-get update && pip install poetry && poetry install --no-root 

CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]