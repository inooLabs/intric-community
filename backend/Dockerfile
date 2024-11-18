FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libmagic1 ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry

COPY poetry.lock pyproject.toml ./
COPY /src ./src

RUN poetry install

COPY /alembic ./alembic
COPY .env ./.env

EXPOSE 8123

CMD ["poetry", "run", "start"]
