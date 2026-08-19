FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
RUN groupadd --gid 10001 onecent && useradd --uid 10001 --gid onecent --no-create-home onecent
WORKDIR /app
COPY pyproject.toml requirements.lock ./
RUN mkdir -p src/onecent && touch src/onecent/__init__.py \
    && pip install --no-cache-dir --require-hashes -r requirements.lock
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
RUN chmod 0644 /app/pyproject.toml /app/alembic.ini \
    && chmod -R a+rX /app/migrations /app/scripts /app/src \
    && rm -rf build src/*.egg-info \
    && pip install --no-cache-dir --no-deps --force-reinstall .
USER 10001:10001
EXPOSE 8013
CMD ["uvicorn", "onecent.api.app:app", "--host", "0.0.0.0", "--port", "8013", "--workers", "1"]
